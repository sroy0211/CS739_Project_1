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

DB_PATH = "./db_files/"

# Set up logging to file
logging.basicConfig(
    filename=f'{DB_PATH}/kvstore.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def scan_ports(num_ports=100, start_port=50000, end_port=60000):
    """ Look for an open port in the given range. """
    ports = []
    while(len(ports) < num_ports):
        port = random.randint(start_port, end_port)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            result = s.connect_ex(('localhost', port))
            if result != 0:
                ports.append(port)
    return ports

def create_config_file(filename='server_config.json', num_replicas=100):
    """Create a configuration file for server instances."""
    ports = scan_ports(num_replicas + 1)
    ports = {"server_ports": ports[:-1], "master_port": ports[-1]}
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
    def __init__(self, num_replicas=100, timeout=3):
        """
        Args:
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
        
        create_config_file(num_replicas=num_replicas)
        ports = read_config_file()
        self.port = ports['master_port']
        self.server_ports = ports['server_ports']
        self.tail_port = self.server_ports[-1]

        # Spawn replica servers
        self.spawn_servers()
    
    def spawn_servers(self):
        """Spawn the replica servers and initialize them with master and child ports."""
        for i, port in enumerate(self.server_ports):
            child_port = self.server_ports[i + 1] if i < len(self.server_ports) - 1 else None  # Tail has no child

            # Spawn the server with the required configuration
            process = self.start_server(port, child_port)
            self.servers[port] = process  # Store the process object for management

            logging.info(f"Server started on port {port} with child port {child_port}.")
            
    # TODO: spawn replica servers and pass master & child port to them
    def start_server(self, port, child_port=None):
        """Start a replica server as a subprocess with the given ports."""
        command = [
            "python3", "server.py",  # Launch the same server.py file
            f"--port={port}", 
            f"--master_port={self.port}"  # Pass the master port to the server
        ]
        return subprocess.Popen(command)  # Start the server as a subprocess
    
    def get_head(self):
        """Get the head node's address in the chain. If it is down, replace it by spawning a new server."""
        if not self.server_ports:
            logging.error("No servers are available.")
            return None

        # The head is the first server in the chain
        head_port = self.server_ports[0]

        # Check if the head is alive by verifying its last heartbeat
        current_time = time.time()
        if head_port not in self.heartbeats or current_time - self.heartbeats[head_port] > self.timeout:
            logging.warning(f"Head server on port {head_port} is down. Attempting replacement...")
            
            # Replace the head by spawning a new server on an available port
            self.replace_server(head_port)
            # Update the head to the new server (newly spawned server should be at the front)
            head_port = self.server_ports[0]
            logging.info(f"New head server spawned on port {head_port}.")
        else:
            logging.info(f"Head server is alive on port {head_port}.")
        
        return head_port

        
    def get_tail(self):
        """Get the tail node's address in the chain. If it is down, replace it by spawning a new server."""
        if not self.server_ports:
            logging.error("No servers are available.")
            return None

        # The tail is the last server in the chain
        tail_port = self.server_ports[-1]

        # Check if the tail is alive by verifying its last heartbeat
        current_time = time.time()
        if tail_port not in self.heartbeats or current_time - self.heartbeats[tail_port] > self.timeout:
            logging.warning(f"Tail server on port {tail_port} is down. Attempting replacement...")
            
            # Replace the tail by spawning a new server on an available port
            self.replace_server(tail_port)
            # Update the tail to the new server (new server added to the end of the list)
            tail_port = self.server_ports[-1]
            logging.info(f"New tail server spawned on port {tail_port}.")
        else:
            logging.info(f"Tail server is alive on port {tail_port}.")

        return tail_port

    
    def replace_server(self, port, is_tail=False):
        """Replace a failed server with a new one. If the tail failed, 
        the new server becomes the tail and either
            1. Reads the old database (when the node isn't totally destroyed)
            2. Starts with an empty database, fetch data from previous node
        """
        pass
    
# Define SQLite-based storage backend
class KeyValueStore:
    def __init__(self, server_port, heartbeat_gap, prev_port=None, next_port=None, debug_mode=False):
        self.db_file = os.path.join(DB_PATH, f"kvstore_{server_port}.db")
        self.port = server_port
        self.master_stub = None # heartbeat from replica to master
        self.prev_stub = None
        self.next_stub = None
        self.heartbeat_gap = heartbeat_gap
        assert not prev_port or not next_port, "Must be either head, tail or middle node"
        if prev_port:
            self.prev_stub = kvstore_pb2_grpc.KVStoreStub(grpc.insecure_channel(f'localhost:{prev_port}'))
        if next_port:
            self.next_stub = kvstore_pb2_grpc.KVStoreStub(grpc.insecure_channel(f'localhost:{next_port}'))
        self.master_stub = kvstore_pb2_grpc.KVStoreStub(grpc.insecure_channel(f'localhost:{server_port}'))
        
        try:
            self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
            self.conn.execute("PRAGMA journal_mode=WAL;")
            self.conn.execute("PRAGMA busy_timeout = 5000;")
            self.conn.execute('''CREATE TABLE IF NOT EXISTS kvstore
                                 (key TEXT PRIMARY KEY, value TEXT)''')
            logging.info("Initialized KVStore")
        except sqlite3.Error as e:
            logging.error(f"Database connection error for server {server_port}: {e}")
            raise
        
        # spawn another thread to send heartbeats every heartbeat_gap seconds
        self.stop_event = threading.Event()
        self.heartbeat_thread = threading.Thread(target=self.send_heartbeat)
        self.heartbeat_thread.start()
        
    def send_heartbeat(self):
        """Notify the master node that the server is alive in a "push" manner."""
        while not self.stop_event.is_set():
            try:
                # Send heartbeat to master
                # logging.info(f"Heartbeat sent from server {self.port}")
                ack = self.master_stub.Ping(kvstore_pb2.PingRequest())
                time.sleep(self.heartbeat_gap)  # Interval between heartbeats
                return ack
            except Exception as e:
                logging.error(f"Error sending heartbeat on server {self.port}: {e}")
                break
        
    def get(self, key):
        try:
            cursor = self.conn.execute("SELECT value FROM kvstore WHERE key=?", (key,))
            result = cursor.fetchone()
            logging.info("Get KVStore for key: %s", key)
            if result:
                logging.info("Result found: %s", result[0])
                return result[0], True
            return None, False
        except sqlite3.Error as e:
            logging.error(f"Error fetching key '{key}': {e}")
            return None, False

    def put(self, key, value):
        old_value, found = self.get(key)
        logging.info("Put KVStore for key: %s", key)
        try:
            with self.conn:
                if found:
                    self.conn.execute("UPDATE kvstore SET value=? WHERE key=?", (value, key))
                else:
                    self.conn.execute("INSERT INTO kvstore (key, value) VALUES (?, ?)", (key, value))
            logging.info("Put operation successful for key: %s", key)
            return old_value, found
        except sqlite3.Error as e:
            logging.error(f"Error writing to database for key '{key}': {e}")
            return None, False

    def crash(self, hit_by_missle=False):
        """
        Simulate the server crashing. If hit by a missle, all db data is lost (not needed for p2).
        """
        self.stop_event.set()
        if hit_by_missle:
            logging.info(f"Server {self.port} hit by a missile. All data lost.")
            self.conn.close()
            os.remove(self.db_file)
            self.heartbeat_thread.join()
        else:
            logging.info("Server crashed.")
            self.conn.close()
            self.heartbeat_thread.join()


class KVStoreServicer(kvstore_pb2_grpc.KVStoreServicer):
    def __init__(self, server: grpc.Server, store: KeyValueStore, master_port: int):
        self.server = server  # Store the server reference
        self.master_port = master_port
        self.store = store
        
    @staticmethod
    def validate_key_value(key, value):
        if len(key) > 128 or any(char in key for char in ["[", "]"]):
            return False, "Key must be a valid printable ASCII string, 128 or fewer bytes, and cannot contain '[' or ']'"
        if len(value) > 2048 or any(char in value for char in ["[", "]"]):
            return False, "Value must be a valid printable ASCII string, 2048 or fewer bytes, and cannot contain '[' or ']'"
        return True, None
    
    def Get(self, request, context):
        valid, error_message = KVStoreServicer.validate_key_value(request.key, "")
        if not valid:
            logging.error(f"Get operation failed: {error_message}")
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(error_message)
            return kvstore_pb2.GetResponse(value='', found=False)

        value, found = self.store.get(request.key)
        return kvstore_pb2.GetResponse(value=value if found else '', found=found)

    def Put(self, request, context):
        valid, error_message = KVStoreServicer.validate_key_value(request.key, request.value)
        if not valid:
            logging.error(f"Put operation failed: {error_message}")
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(error_message)
            return kvstore_pb2.PutResponse(old_value='', old_value_found=False)

        old_value, old_value_found = self.store.put(request.key, request.value)
        return kvstore_pb2.PutResponse(old_value=old_value if old_value_found else '', old_value_found=old_value_found)
    
    def Die(self, request, context):
        """Terminate the server to simulate failure."""
        logging.info(f"Received termination request for server: {request.server_name}. ")
        
        # Shut down the server
        if hasattr(self, 'server'):
            logging.info("Shutting down the server.")
            self.server.stop(0)  # This will stop the server gracefully
            self.store.crash(hit_by_missle=False)
            logging.info("Server shut down successfully.")

        context.set_code(grpc.StatusCode.OK)
        context.set_details("Server is shutting down.")
        return kvstore_pb2.DieResponse(success=True)
    
    def Ping(self, request, context):
        logging.info("Ping received, server is alive.")
        return kvstore_pb2.PingResponse(is_alive=True)


def serve(args):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
    store = KeyValueStore(args.port, args.timeout)
    kvstore_pb2_grpc.add_KVStoreServicer_to_server(KVStoreServicer(server, store, args.master_port), server)
    server.add_insecure_port(f'[::]:{args.port}')
    server.start()
    logging.info(f"Server started on port {args.port}")
    try:
        while True:
            time.sleep(86400)  # Keep the server running
    except KeyboardInterrupt:
        logging.info("Shutting down the server gracefully.")
        server.stop(0)  # This will stop the server gracefully
        logging.info(f"Server on port {args.port} shut down successfully.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Start a chain replication server.')
    parser.add_argument("-a", "--action", choices=['master', 'replica'], default='master',
                        help="Whether to start a master or launch replica nodes called from master")
    parser.add_argument("-p", "--port", type=int, default=50000, help="For both master and replica. Port number to start the server on")
    parser.add_argument("-m", "--master_port", type=int, default=50001, help="For child only. Master port to send heartbeat to")
    parser.add_argument("-n", "--num_replicas", type=int, default=100, help="Number of server replicas in chain")
    parser.add_argument("-t", "--timeout", type=int, default=3, help="Timeout for heartbeat detection. Should be less than cache TTL.")
    args = parser.parse_args()
    if args.action == 'master':
        master_node = MasterNode(num_replicas=args.num_replicas, timeout=args.timeout)
    else:
        serve(args)
    