import grpc
from concurrent import futures
import kvstore_pb2_grpc
import kvstore_pb2
import logging
import argparse
import sqlite3
import os
import time
import threading
# Set up logging to file
logging.basicConfig(
    filename='replica_server.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

DB_PATH = "./db_files/"
# Define SQLite-based storage backend
class KeyValueStore:
    def __init__(self,
                 server_port,
                 heartbeat_gap,
                 prev_port=None,
                 next_port=None,
                 debug_mode=False,
                 crash_db=True
                 ):
        """
        Initialize the key-value store.
        Args:
            server_port: The port on which the server is running.
            heartbeat_gap: The interval between heartbeats.
            prev_port: The port of the previous server in the chain.
            next_port: The port of the next server in the chain.
            debug_mode: Whether to run in debug mode.
            crash_db: Whether to clear the database(local file system) on failure.
        """
        
        self.db_file = os.path.join(DB_PATH, f"kvstore_{server_port}.db")
        self.port = server_port
        self.master_stub = None # heartbeat from replica to master
        self.prev_stub = None
        self.next_stub = None
        self.heartbeat_gap = heartbeat_gap
        self.crash_db = crash_db
        
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
                logging.info(f"Heartbeat sent from server {self.port}")
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

    def crash(self):
        """
        Simulate the server crashing. 
        If hit by a missle, all db data is lost and use chain forwarding to recover.
        """
        self.stop_event.set()
        if self.crash_db:
            logging.info(f"Server {self.port} hit by a missile. All data lost.")
            self.conn.close()
            os.remove(self.db_file)
            self.heartbeat_thread.join()
        else:
            logging.info("Server crashed.")
            self.conn.close()
            self.heartbeat_thread.join()
            
class KeyValueStoreServicer(kvstore_pb2_grpc.KVStoreServicer):
    """gRPC server for the key-value store."""

    def __init__(self, port, master_port, store: KeyValueStore, child_port=None):
        self.port = port
        self.master_port = master_port
        self.child_port = child_port
        self.store = store
        self.db_file = os.path.join(DB_PATH, f"kvstore_{port}.db")

        # Database connection
        try:
            self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
            self.conn.execute("PRAGMA journal_mode=WAL;")
            self.conn.execute("PRAGMA busy_timeout = 5000;")
            self.conn.execute('''CREATE TABLE IF NOT EXISTS kvstore
                                 (key TEXT PRIMARY KEY, value TEXT)''')
            logging.info(f"Server on port {self.port} initialized successfully.")
        except sqlite3.Error as e:
            logging.error(f"Database connection error on port {self.port}: {e}")
            raise

        # Start heartbeat thread
        self.stop_event = threading.Event()
        self.heartbeat_thread = threading.Thread(target=self.send_heartbeat)
        self.heartbeat_thread.start()

    def send_heartbeat(self):
        """Send heartbeat to master to signal that the server is alive."""
        while not self.stop_event.is_set():
            try:
                # Simulate sending a heartbeat to the master
                logging.info(f"Heartbeat sent from server {self.port} to master {self.master_port}")
                time.sleep(2.5)  # Adjust heartbeat interval if needed
                
            except Exception as e:
                logging.error(f"Error in heartbeat thread on port {self.port}: {e}")
                break

    def Get(self, request, context):
        """Handle 'Get' requests."""
        try:
            cursor = self.conn.execute("SELECT value FROM kvstore WHERE key=?", (request.key,))
            result = cursor.fetchone()
            if result:
                logging.info(f"Get request for key: {request.key} - Found value: {result[0]}")
                return kvstore_pb2.GetResponse(value=result[0], success=True)
            else:
                logging.info(f"Get request for key: {request.key} - Not found.")
                return kvstore_pb2.GetResponse(success=False)
        except sqlite3.Error as e:
            logging.error(f"Error processing Get request for key {request.key}: {e}")
            return kvstore_pb2.GetResponse(success=False)

    def Put(self, request, context):
        """Handle 'Put' requests."""
        try:
            with self.conn:
                self.conn.execute("INSERT OR REPLACE INTO kvstore (key, value) VALUES (?, ?)", 
                                  (request.key, request.value))
            logging.info(f"Put request - Key: {request.key}, Value: {request.value}")
            return kvstore_pb2.PutResponse(success=True)
        except sqlite3.Error as e:
            logging.error(f"Error processing Put request for key {request.key}: {e}")
            return kvstore_pb2.PutResponse(success=False)

    def Die(self, request, context):
        """Terminate the server to simulate failure."""
        logging.info(f"Server on port {self.port} crashed by request.")        
        self.stop_event.set() # Ensure the heartbeat thread stops
        
        # Shut down the server
        if hasattr(self, 'server'):
            logging.info("Shutting down the server.")
            self.server.stop(0)  # This will stop the server gracefully
            self.store.crash()
            logging.info("Server shut down successfully.")

        context.set_code(grpc.StatusCode.OK)
        context.set_details("Server is shutting down.")
        return kvstore_pb2.DieResponse(success=True)
    

def serve(args):
    """Run the gRPC server."""
    port, master_port, child_port = args.port, args.master_port, args.next_port
    
    store = KeyValueStore(master_port, args.timeout)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    kvstore_servicer = KeyValueStoreServicer(port, master_port, store, child_port)
    kvstore_pb2_grpc.add_KVStoreServicer_to_server(kvstore_servicer, server)

    server.add_insecure_port(f'[::]:{port}')
    server.start()
    logging.info(f"Server started on port {port}. Waiting for requests...")

    try:
        server.wait_for_termination()
        pass
    except KeyboardInterrupt:
        logging.info(f"Server on port {port} shutting down.")
        kvstore_servicer.stop_event.set()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Start a replica server.')
    parser.add_argument('--port', type=int, required=True, help='Port to run the server on.')
    parser.add_argument('-m', '--master_port', type=int, required=True, help='Master node port.')
    parser.add_argument('--next_port', type=int, default=None,
                        help='Child port of the next server in the chain (if any).')
    parser.add_argument("--crash_db", type=eval, default=True,
                        help="Whether to crash the database in failure simulation, which requires tail data forwarding to recover.")
    args = parser.parse_args()

    # Ensure the DB directory exists
    os.makedirs(DB_PATH, exist_ok=True)

    # Start the server with the provided arguments
    serve(args)