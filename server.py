import sqlite3
import grpc
from concurrent import futures
import kvstore_pb2
import kvstore_pb2_grpc
import logging
import time
import threading
import argparse
import socket
import random
import json
from typing import Union, List
import shutil
import subprocess
import math
from contextlib import nullcontext
DB_PATH = "./db_files/"

# Clear logging file before starting
# Set up logging to file
logging.basicConfig(
    filename='master_server.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    filemode='w'
)
# clear replica logs
with open('replica_server.log', 'w') as f:
    pass

def scan_ports(num_ports=3, start_port=50000, end_port=60000):
    """ Look for an open port in the given range. """
    ports = []
    while(len(ports) < num_ports):
        port = random.randint(start_port, end_port)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            result = s.connect_ex(('localhost', port))
            if result != 0:
                ports.append(port)
    return ports

def create_config_file(filename='server_config.json', num_replicas=10):
    """Create a configuration file for server instances."""
    ports = scan_ports(num_replicas + 1)
    ports = {"child_ports": ports[:-1], "master_port": ports[-1]}
    with open(filename, mode='w') as file:
        json.dump(ports, file)

def read_config_file(filename='server_config.json'):
    """Read server configuration from a json file."""
    with open(filename, mode='r') as file:
        ports = json.load(file)
    return ports

class MasterNode:
    """
    The master node in chain replication. Functionalities include:
    1. Recording a list of replicated servers and their ports
    2. Detecting heartbeats and replacing faileds servers
    3. Recording the tail node to forward queries to.
    The master node is assumed to not fail or properly replicate itself.
    """
    def __init__(self, port, child_ports, num_replicas=10, timeout=2.5, verbose=True, host="localhost"):
        """
        Args:
            port (int): Port number to run the master node on
            child_ports (list): List of ports for the child nodes
            num_replicas (int): Number of replicas in the chain
            timeout (int): Max timeout for heartbeat detection. This should be shorter than
                cache TTL to ensure consistency (bring server back on line before cache is invalidated),
                considering network latency/restart cost etc..
        """
        self.servers_procs = {} # {port: server object}
        self.timeout = timeout
        self.num_replicas = num_replicas
        self.heartbeats = {} # {port: timestamp}
        self.min_chain_len = math.ceil(self.num_replicas / 3 * 2)
        self.host = host
        self.verbose = verbose
        
        if not verbose:
            logging.disable(logging.INFO)
        self.port = port
        # make it a linked list
        self.child_ports = child_ports
        self.server_stubs = {port: kvstore_pb2_grpc.KVStoreStub(grpc.insecure_channel(f'{self.host}:{port}')) for port in child_ports}
        self.child_order = {port: i for i, port in enumerate(child_ports)}
        self.head_port = self.child_ports[0]
        self.tail_port = self.child_ports[-1]
        self.num_live_replicas = len(child_ports)
        
        self.lock = threading.Lock()
        # Spawn replica servers
        self.spawn_servers(self.child_ports)
        self.append_to_tail_in_progress = False
        
        # Runs an infinite loop to check for heartbeats
        self.stop_event = threading.Event()
        threading.Thread(target=self.check_heartbeat).start()
        
        
    def log_heartbeat(self, port, is_alive=True):
        """Log the heartbeat for the given server port, or replace a server
        in a "clean" way. """
        if not is_alive:
            logging.warning(f"Server on port {port} notified master that it's down. Attempting replacement...")
            with self.lock:
                del self.heartbeats[port]
                self.num_live_replicas -= 1
            # self.remove_server(port)
            self.replace_server(port)
        else:
            with self.lock:
                self.heartbeats[port] = time.time()
            
    def spawn_servers(self, child_ports: Union[int, List[int]]):
        """Intialize the replica servers and initialize them with master and child ports."""
        if isinstance(child_ports, int):
            child_ports = [child_ports]
            
        for i, port in enumerate(child_ports):
            command = [
                "python3", "replica_server.py",  # Launch the same server.py file
                f"--port={port}", 
                f"--master_port={self.port}",  # Pass the master port to the server
                f"--crash_db={args.crash_db}", # Whether to recover by chain forwarding
                f"--verbose={self.verbose}"
            ]
            if self.host != "localhost":
                command = ["ssh", self.host] + command
                
            # Chain structure
            if i > 0:
                command.append(f"--prev_port={child_ports[i - 1]}")
            if i < len(child_ports) - 1:
                command.append(f"--next_port={child_ports[i + 1]}")
                
            process = subprocess.Popen(command)  # Start the server as a subprocess
            # Spawn the server with the required configuration
            self.servers_procs[port] = process  # Store the process object for management
            self.server_stubs[port] = kvstore_pb2_grpc.KVStoreStub(grpc.insecure_channel(f'{self.host}:{port}'))
            self.heartbeats[port] = time.time()
        logging.info(f"Replicas spawn on ports: {child_ports}")
    
    
    def check_heartbeat(self):
        """Check for heartbeats and remove failed servers."""
        while not self.stop_event.is_set():
            try:
                current_time = time.time()
                servers_to_replace = []
                for port, last_hb_time in self.heartbeats.items():
                    # logging.info(f"Checking heartbeat for port {port}. num_live_replicas: {self.num_live_replicas}")
                    if current_time - last_hb_time > self.timeout:
                        logging.warning(f"Found that server on port {port} has no heartbeat. ")
                        self.num_live_replicas -= 1
                        
                        # if self.num_live_replicas < self.min_chain_len:
                            # logging.error(f"Chain length below threshold, recovering back to threshold.")
                        try:
                            # self.replace_server(port)
                            servers_to_replace.append(port)
                            logging.info(f"Server on port {port} replaced.")
                        except Exception as e:
                            logging.error(f"Error in replacing server: {e}")
                for port in servers_to_replace:
                    self.replace_server(port)
                    
            except Exception as e:
                logging.error(f"Error in checking heartbeat: {e}")
            # Check every timeout / 2 seconds
            time.sleep(self.timeout // 2)
        
    def remove_server(self, ports):  
        """Remove a server from the chain."""
        ports = [ports] if isinstance(ports, int) else ports
        
        with self.lock:
            for port in ports:
                del self.child_ports[self.child_order[port]]
                for i in range(self.child_order[port], len(self.child_ports)):
                    self.child_order[self.child_ports[i]] -= 1
                    
                self.child_order.pop(port)
                self.heartbeats.pop(port)
                self.server_stubs.pop(port)
                self.servers_procs[port].kill()
        logging.info(f"Remove servers on ports: {ports}. Current replicas: {self.child_ports} " +
                     "num_live_replicas: {self.num_live_replicas}, recovery threshold: {self.min_chain_len}")
    
    def add_server(self, port):
        """Add a new server to the tail of the chain."""
        self.child_ports.append(port)
        self.child_order[port] = len(self.child_ports) - 1
        command = [
            "python3", "replica_server.py",  # Launch the same server.py file
            f"--port={port}",
            f"--master_port={self.port}",  # Pass the master port to the server
            f"--crash_db={args.crash_db}",
            f"--verbose={self.verbose}"
            f"--prev_port={self.tail_port}",
            "--notify_tail", # Notify old tail for forwarding
        ]
        process = subprocess.Popen(command)  # Start the server as a subprocess
        self.heartbeats[port] = time.time()
        self.servers_procs[port] = process
        logging.info(f"Started server on port {port} to the chain.")

        
    def replace_server(self, port):
        """Replace a failed server by appending a new one to tail, 
            using the original port(as we run in a simulated LAN environment).
            1. Reads the old database (when the node isn't totally destroyed)
            2. Starts with an empty database, fetch data from previous node
        """
        # Kill the old server
        self.servers_procs[port].kill()
        # Start a new server on the same port
        command = [
            "python3", "replica_server.py",  # Launch the same server.py file
            f"--port={port}", 
            f"--master_port={self.port}",  # Pass the master port to the server
            f"--crash_db={args.crash_db}",
            f"--notify_tail", # Notify old tail for forwarding once it's up
        ]

        # Chain structure
        start_time = time.time()
        while self.append_to_tail_in_progress:
            logging.info(f"Waiting for previous tail to finish forwarding to replica {self.tail_port}")
            time.sleep(0.06)
            if time.time() - start_time > self.timeout:
                # Drop last tail if forwarding times out
                logging.error(f"Forwarding to new tail {self.tail_port} times out. Dropping it.")
                self.remove_server(self.tail_port)
                self.append_to_tail_in_progress = False
                
        with self.lock:
            self.append_to_tail_in_progress = True
            del self.child_ports[self.child_order[port]]
            for i in range(self.child_order[port], len(self.child_ports)):
                self.child_order[self.child_ports[i]] -= 1
                
            self.child_ports.append(port)
            self.child_order[port] = len(self.child_ports) - 1    
            if port == self.head_port:
                self.head_port = self.child_ports[0]
                self.promote_to_head(self.head_port)
            
        command.append(f"--prev_port={self.tail_port}") # Temp tail until the new one is up
        logging.info(f"Appended new server {self.tail_port} to tail.")
        self.servers_procs[port] = subprocess.Popen(command)  # Start the server as a subprocess
        self.num_live_replicas += 1
        self.heartbeats[port] = time.time()
        
    def promote_to_head(self, new_head_port, retries=3):
        """Notify the new head to claim head status."""
        for i in range(retries):
            try:
                self.server_stubs[new_head_port].PromoteToHead(kvstore_pb2.PromoteToHeadRequest())
                with self.lock if not self.lock.locked() else nullcontext():
                    self.head_port = new_head_port
                logging.info(f"Master requested server {self.head_port} to claim head status.")
                return
            except Exception as e:
                logging.error(f"Error in promoting server {new_head_port} to head: {e}")
        logging.error(f"Failed to update head after {retries} retries.")
            
            
    def update_tail_done(self, new_tail_port):
        """Replica will send this message when replacement & forwarding is done"""
        with self.lock:
            self.append_to_tail_in_progress = False
            self.tail_port = new_tail_port   
            logging.info(f"Master updated tail port to {new_tail_port}.")
            self.heartbeats[new_tail_port] = time.time()
        logging.info(f"Tail node resurrected on port {new_tail_port}. List of current replicas: {self.child_ports}")
        
        
    def get_head(self, replace=False):
        """Get the head node's address in the chain. If it is down, replace it by spawning a new server."""
        if not self.child_ports or self.head_port is None:
            logging.error("No servers are available.")
            return None, None

        # Check if the head is alive by verifying its last heartbeat
        current_time = time.time()
        if (self.head_port not in self.heartbeats \
            or current_time - self.heartbeats[self.head_port] > self.timeout 
            or replace
            ):
            logging.warning(f"Master heard that the replica on port {self.head_port} is down. Attempting replacement...")
            
            # Replace the head by spawning a new server on an available port
            self.replace_server(self.head_port)
            # Update the head to the new server (newly spawned server should be at the front)
            self.head_port = self.child_ports[0]
            logging.info(f"New head server shifted to port {self.head_port}.")
        else:
            logging.info(f"Head server is alive on port {self.head_port}, returning it to client.")
        
        hostname = socket.gethostname()
        return self.head_port, hostname

    def get_tail(self, replace=False):
        """Get the tail node's address in the chain. If it is down, replace it by spawning a new server."""
        if not self.child_ports or self.tail_port is None:
            logging.error(f"No servers are available.")
            return None, None

        # The tail is the last server in the chain
        tail_port = self.tail_port

        # Check if the tail is alive by verifying its last heartbeat
        current_time = time.time()
        if tail_port not in self.heartbeats \
        or current_time - self.heartbeats[tail_port] > self.timeout\
        or replace:
            logging.warning(f"Tail server on port {tail_port} is down. Attempting replacement...")
            
            # Replace the tail by spawning a new server on an available port
            self.replace_server(tail_port)
            # Update the tail to the new server (new server added to the end of the list)
            tail_port = self.child_ports[-1]
            logging.info(f"New tail server spawned on port {tail_port}.")
        else:
            logging.info(f"Tail server is alive on port {tail_port}, returning it to client.")

        hostname = socket.gethostname()
        return tail_port, hostname
 
    def kill_all(self,):
        """ Clean up all servers on exit"""
        self.stop_event.set()
        for port, process in self.servers_procs.items():
            process.kill()
        logging.info("All replicas killed.")    


class MasterServicer(kvstore_pb2_grpc.MasterNodeServicer):
    def __init__(self, server: grpc.Server, master_node: MasterNode):
        self.server = server  # Store the server reference
        self.master_node = master_node
        self.port = master_node.port
        
    @staticmethod
    def validate_key_value(key, value):
        if len(key) > 128 or any(char in key for char in ["[", "]"]):
            return False, "Key must be a valid printable ASCII string, 128 or fewer bytes, and cannot contain '[' or ']'"
        if len(value) > 2048 or any(char in value for char in ["[", "]"]):
            return False, "Value must be a valid printable ASCII string, 2048 or fewer bytes, and cannot contain '[' or ']'"
        return True, None
    
    def GetHead(self, request, context):
        """Get the head node's address in the chain."""
        head_port, hostname = self.master_node.get_head(request.replace)
        return kvstore_pb2.GetReplicaResponse(port=head_port, hostname=hostname)

    def GetTail(self, request, context):
        """Get the tail node's address in the chain."""
        tail_port, hostname = self.master_node.get_tail(request.replace)
        return kvstore_pb2.GetReplicaResponse(port=tail_port, hostname=hostname)
    
    def GetNextInChain(self, request, context):
        """Get the next node in the chain."""
        port = request.port
        if port not in self.master_node.child_ports:
            logging.error(f"Port {port} not found in the chain.")
            return kvstore_pb2.GetReplicaResponse(port=None, hostname=None)
        if port == self.master_node.tail_port:
            logging.info(f"Tail node {port} tries to reach next in chain, which shouldn't happen...")
            return kvstore_pb2.GetReplicaResponse(port=None, hostname=None)
        
        next_port = self.master_node.child_ports[self.master_node.child_order[port] + 1]
        # breakpoint()
        logging.info(f"Sending next in chain for port {port}: {next_port}.")
        hostname = socket.gethostname()
        return kvstore_pb2.GetReplicaResponse(port=next_port, hostname=hostname)
    
    def SendHeartBeat(self, request, context):
        """Get the heartbeat status from a replica.
        """
        replica_port = request.port
        try:
            self.master_node.log_heartbeat(replica_port, is_alive=request.is_alive)
            # logging.info(f"Heartbeat from port {replica_port} received. is_alive={request.is_alive}")
        except Exception as e:
            logging.error(f"Master error in receiving heartbeat: {e}")
        finally:
            return kvstore_pb2.SendHeartBeatResponse(is_alive=True)
        
    def StartServer(self, request, context):
        """Add a new server to the chain."""
        try:
            new_port = scan_ports(1)[0]
            self.master_node.add_server(new_port)
            logging.info(f"New server spawned on port {new_port}.")
            return kvstore_pb2.StartServerResponse(success=True)
        except Exception as e:
            logging.error(f"Master error in StartServer: {e}")
            return kvstore_pb2.StartServerResponse(success=False)
            
    
    def TransferToNewTailDone(self, request, context):
        """Update the tail node's address in the chain."""
        try:
            self.master_node.update_tail_done(request.new_tail_port)
        except Exception as e:
            logging.error(f"Master error in TransferToNewTailDone tail: {e}")
        finally:
            return kvstore_pb2.Empty()
    
def serve(args, ports):
    # Setup args
    master_port = ports["master_port"]
    child_ports = ports["child_ports"]
    
    # Establish connection
    master_node = MasterNode(master_port,
                             child_ports, 
                             num_replicas=args.num_replicas,
                             timeout=args.timeout,
                             verbose=args.verbose,
                             host=args.host
                            )
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=16))
    kvstore_pb2_grpc.add_MasterNodeServicer_to_server(MasterServicer(server, master_node), server)

    server.add_insecure_port(f'[::]:{master_port}') # ipv6
    server.add_insecure_port(f'0.0.0.0:{master_port}') # ipv4
    server.start()
    logging.info(f"Master started on port {master_port}. Waiting for requests...")
    try:
        server.wait_for_termination()
        pass
    except KeyboardInterrupt:
        logging.info(f"Master node shutting down.")
        server.stop(0)
        master_node.kill_all()
        # Remove all db files
        shutil.rmtree(DB_PATH)
        

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Start a chain replication server.')
    parser.add_argument("-p", "--port", type=int, default=50000, help="For both master and replica. Port number to start the current server on")
    parser.add_argument("-n", "--num_replicas", type=int, default=10, help="Number of server replicas in chain")
    parser.add_argument("-t", "--timeout", type=int, default=3, help="Timeout for heartbeat detection. Should be less than cache TTL.")
    parser.add_argument("--crash_db", type=eval, default=True,
                        help="Whether to crash the database in failure simulation, which requires tail data forwarding to recover.")
    parser.add_argument("--verbose", type=eval, default=True, help="Whether to print debug info.")
    parser.add_argument("--host", type=str, default="localhost", help="Host name to run the server on.")
    args = parser.parse_args()
        
    create_config_file(num_replicas=args.num_replicas)  # You can specify the filename and num_replicas if needed
    # try:
    ports = read_config_file()
    print("Configuration loaded:", ports)
    serve(args, ports)
    # except Exception as e:
    #     print("Error:", e)

