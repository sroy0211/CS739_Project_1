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
import os
import subprocess
import math

DB_PATH = "./db_files/"

# Set up logging to file
logging.basicConfig(
    filename='kvstore.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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

def create_config_file(filename='server_config.json', num_replicas=3):
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
    def __init__(self, port, child_ports, num_replicas=10, timeout=3,):
        """
        Args:
            port (int): Port number to run the master node on
            child_ports (list): List of ports for the child nodes
            num_replicas (int): Number of replicas in the chain
            timeout (int): Max timeout for heartbeat detection. This should be shorter than
                cache TTL to ensure consistency (bring server back on line before cache is invalidated),
                considering network latency/restart cost etc..
        """
        self.servers = {} # {port: server object}
        self.timeout = timeout
        self.num_replicas = num_replicas
        self.heartbeats = {} # {port: timestamp}
        self.server_stubs = {} # {port: stub}
        self.min_chain_len = math.ceil(args.num_replicas / 2)
        
        self.port = port
        self.child_ports = child_ports
        self.head_port = self.child_ports[0]
        self.tail_port = self.child_ports[-1]

        # Spawn replica servers
        self.spawn_servers()
        # Runs in an infinite loop to check for heartbeats
        threading.Thread(target=self.check_heartbeat, args=(self.timeout,)).start()
        
    def check_heartbeat(self, timeout=3):
        """Check for heartbeats and remove failed servers."""
        current_time = time.time()
        for port, last_hb_time in self.heartbeats.items():
            if current_time - last_hb_time > timeout:
                logging.warning(f"Server on port {port} is down. Attempting replacement...")
                self.replace_server(port)
                logging.info(f"Server on port {port} replaced.")
        # Check every `timeout` seconds
        time.sleep(timeout)
        
    def log_heartbeat(self, port, is_alive=True):
        """Log the heartbeat for the given server port, or replace a server
        in a "clean" way. """
        if not is_alive:
            self.heartbeats[port] = None
            self.replace_server(port)
        else:
            self.heartbeats[port] = time.time()
        
    def spawn_servers(self):
        """Spawn the replica servers and initialize them with master and child ports."""
        for i, port in enumerate(self.child_ports):
            child_port = self.child_ports[i + 1] if i < len(self.child_ports) - 1 else None  # Tail has no child
            # Spawn the server with the required configuration
            process = self.start_server(port, child_port)
            self.servers[port] = process  # Store the process object for management
            logging.info(f"Server started on port {port} with child port {child_port}.")
            
    # TODO: spawn replica servers and pass master & child port to them
    def start_server(self, child_port, next_child_port=None):
        """Start a replica server as a subprocess with the given ports."""
        command = [
            "python3", "replica_server.py",  # Launch the same server.py file
            f"--port={child_port}", 
            f"--master_port={self.port}",  # Pass the master port to the server
            f"--crash_db={args.crash_db}"  # Whether to recover by chain forwarding
        ]
        if next_child_port:
            command.append(f"--child_port={next_child_port}")
        return subprocess.Popen(command)  # Start the server as a subprocess
    
    def get_head(self):
        """Get the head node's address in the chain. If it is down, replace it by spawning a new server."""
        if not self.child_ports:
            logging.error("No servers are available.")
            return None

        # Check if the head is alive by verifying its last heartbeat
        current_time = time.time()
        if head_port not in self.heartbeats or current_time - self.heartbeats[head_port] > self.timeout:
            logging.warning(f"Head server on port {head_port} is down. Attempting replacement...")
            
            # Replace the head by spawning a new server on an available port
            self.replace_server(head_port)
            # Update the head to the new server (newly spawned server should be at the front)
            head_port = self.child_ports[0]
            logging.info(f"New head server spawned on port {head_port}.")
        else:
            logging.info(f"Head server is alive on port {head_port}.")
        
        hostname = socket.gethostname()
        return head_port, hostname

        
    def get_tail(self):
        """Get the tail node's address in the chain. If it is down, replace it by spawning a new server."""
        if not self.child_ports:
            logging.error("No servers are available.")
            return None

        # The tail is the last server in the chain
        tail_port = self.child_ports[-1]

        # Check if the tail is alive by verifying its last heartbeat
        current_time = time.time()
        if tail_port not in self.heartbeats or current_time - self.heartbeats[tail_port] > self.timeout:
            logging.warning(f"Tail server on port {tail_port} is down. Attempting replacement...")
            
            # Replace the tail by spawning a new server on an available port
            self.replace_server(tail_port)
            # Update the tail to the new server (new server added to the end of the list)
            tail_port = self.child_ports[-1]
            logging.info(f"New tail server spawned on port {tail_port}.")
        else:
            logging.info(f"Tail server is alive on port {tail_port}.")

        hostname = socket.gethostname()
        return tail_port, hostname

    
    def replace_server(self, port, is_tail=False):
        """Replace a failed server with a new one. If the tail failed, 
        the new server becomes the tail and either
            1. Reads the old database (when the node isn't totally destroyed)
            2. Starts with an empty database, fetch data from previous node
        """
        pass
    

# TODO implement master servicer
class MasterServicer(kvstore_pb2_grpc.MasterNodeServicer):
    def __init__(self, server: grpc.Server, master_node: MasterNode, port: int):
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
        head_port, hostname = MasterNode.get_head()
        return kvstore_pb2.GetHeadResponse(port=head_port, hostname=hostname)

    def GetTail(self, request, context):
        """Get the tail node's address in the chain."""
        tail_port, hostname = MasterNode.get_tail()
        return kvstore_pb2.GetTailResponse(port=tail_port, hostname=hostname)
    
    def GetHeartBeat(self, request, context):
        """Get the heartbeat status of the master node.
            For now assume running on localhost, so we just need the port
            to identify client.
        """
        client_info = context.peer()
        client_port = int(client_info.split(":")[-1])
        # Assume running on localhost

        self.master_node.log_heartbeat(client_port, is_alive=request.is_alive)
        return kvstore_pb2.HeartBeatResponse(is_alive=True)

def serve(args, ports):
    # Setup args
    master_port = ports["master_port"]
    child_ports = ports["child_ports"]
    
    # Establish connection
    master_node = MasterNode(master_port, child_ports, num_replicas=args.num_replicas, timeout=args.timeout)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
    kvstore_pb2_grpc.add_KVStoreServicer_to_server(MasterServicer(server, master_node), server)

    server.add_insecure_port(f'[::]:{master_port}')
    server.start()
    logging.info(f"Server started on masterport")
    try:
        server.wait_for_termination()
        pass
    except KeyboardInterrupt:
        logging.info(f"Server on port shutting down.")
        # Remove all db files
        os.rmdir(DB_PATH)
        

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Start a chain replication server.')
    parser.add_argument("-p", "--port", type=int, default=50000, help="For both master and replica. Port number to start the current server on")
    parser.add_argument("-n", "--num_replicas", type=int, default=3, help="Number of server replicas in chain")
    parser.add_argument("-t", "--timeout", type=int, default=3, help="Timeout for heartbeat detection. Should be less than cache TTL.")
    parser.add_argument("--crash_db", type=eval, default=True,
                        help="Whether to crash the database in failure simulation, which requires tail data forwarding to recover.")
    args = parser.parse_args()

    create_config_file()  # You can specify the filename and num_replicas if needed
    try:
        ports = read_config_file()
        print("Configuration loaded:", ports)
        serve(args, ports)
    except Exception as e:
        print("Error:", e)

    else:
        print("Master Server not started")
