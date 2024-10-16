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
from typing import Iterable, Tuple

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
                 debug_mode=False,
                 crash_db=True
                 ):
        """
        Initialize the key-value store.
        Args:
            server_port: The port on which the server is running.
            debug_mode: Whether to print debug info.
            crash_db: Whether to clear the database(local file system) on failure.
        """
        
        self.db_file = os.path.join(DB_PATH, f"kvstore_{server_port}.db")
        self.port = server_port
        self.crash_db = crash_db
        
        try:
            self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
            self.conn.execute("PRAGMA journal_mode=WAL;")
            self.conn.execute("PRAGMA busy_timeout = 5000;")
            self.conn.execute('''CREATE TABLE IF NOT EXISTS kvstore
                                 (key TEXT PRIMARY KEY, value TEXT)''')
            logging.info("Initialized KVStore")
        except sqlite3.Error as e:
            logging.error(f"Database connection error for server {self.port}: {e}")
            raise
        
        
    def get(self, key):
        try:
            cursor = self.conn.execute("SELECT value FROM kvstore WHERE key=?", (key,))
            result = cursor.fetchone()
            if result:
                logging.info(f"Result for {key} found: {result[0]}")
                return result[0], True
            return None, False
        except sqlite3.Error as e:
            logging.error(f"Error fetching key '{key}': {e}")
            return None, False

    def put(self, key, value):
        old_value, found = self.get(key)
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

    def get_cursor(self):
        """Return a cursor to traverse the database."""
        return self.conn.cursor()
        
    def get_new_connection(self):
        return sqlite3.connect(self.db_file, check_same_thread=False)

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
        else:
            logging.info("Server crashed.")
            self.conn.close()
            
class KeyValueStoreServicer(kvstore_pb2_grpc.KVStoreServicer):
    """gRPC server for the key-value store."""

    def __init__(self,
                 store: KeyValueStore,
                 server: grpc.Server,
                 master_port,
                 heartbeat_gap=1,
                 prev_port=None,
                 next_port=None,
                 ):
        """
        Initialize the key-value store servicer for gRPC comm.
        Args:
            store: The KeyValueStore object.
            server: The gRPC server object.
            master_port: The port of the master node.
            heartbeat_gap: The interval between heartbeats.
            prev_port: The port of the previous server in the chain.
            next_port: The port of the next server in the chain.
        """
        self.port = store.port
        self.store = store
        self.server = server
        self.master_port = master_port
        self.heartbeat_gap = heartbeat_gap
        self.db_file = os.path.join(DB_PATH, f"kvstore_{self.port}.db")
        
        # Init comm along the chain and to the master
        self.master_stub = kvstore_pb2_grpc.MasterNodeStub(grpc.insecure_channel(f'localhost:{master_port}'))
        assert prev_port or next_port, "Must be either head, tail or middle node"
        self.prev_port = prev_port
        self.next_port = next_port
        self.is_tail = not next_port
        
        # NOTE: only forwarding, don't need previous stub (one-way linkedlist style chain)
        # if prev_port:
        #     self.prev_stub = kvstore_pb2_grpc.KVStoreStub(grpc.insecure_channel(f'localhost:{prev_port}'))
        if next_port:
            self.next_stub = kvstore_pb2_grpc.KVStoreStub(grpc.insecure_channel(f'localhost:{next_port}'))
            
        # Start heartbeat thread
        self.stop_heartbeat = threading.Event()
        self.heartbeat_thread = threading.Thread(target=self.send_heartbeat)
        self.heartbeat_thread.start()

    def send_heartbeat(self, is_alive=True):
        """Send heartbeat to master to signal that the server is alive."""
        while not self.stop_heartbeat.is_set():
            try:
                # Simulate sending a heartbeat to the master
                logging.info(f"Heartbeat sent from server {self.port} to master {self.master_port}")
                self.master_stub.GetHeartBeat(kvstore_pb2.HeartBeatRequest(is_alive=is_alive))
                time.sleep(self.heartbeat_gap)  # Adjust heartbeat interval if needed
                
            except Exception as e:
                logging.error(f"Error in sending heartbeat heartbeat on port {self.port}: {e}")
                break

    def Get(self, request, context):
        """Handle 'Get' requests."""
        # Not tail, reject req and ask client to go to master for new tail.
        if not self.is_tail:
            logging.info(f"Server on port {self.port} is not the tail. Rejecting Get request.")
            return kvstore_pb2.GetResponse(success=False)
        
        try:
            result = self.store.get(request.key)
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
        # Not head, reject req and ask client to go to master for new head.
        if self.prev_port is not None:
            logging.info(f"Server on port {self.port} is not the head. Rejecting Put request.")
            return kvstore_pb2.PutResponse(success=False)
        
        try:
            self.store.put(request.key, request.value)
            # Forward to next in chain
            self.ForwardToNext(request.key, request.value)
        except sqlite3.Error as e:
            logging.error(f"Error processing Put request for key {request.key}: {e}")
            return kvstore_pb2.PutResponse(success=False)


    def ForwardToNext(self, key, value):
        """Forward key-value pairs to the next node in the chain."""
        if self.next_stub is not None:
            response = self.next_stub.Put(kvstore_pb2.PutRequest(key=key, value=value))
        
    def ForwardAll(self, ):
        """
        Forward all key-value pairs to the new tail node in the chain.
        Upon completion, relinquish the tail status.
        """
        assert self.next_stub, "Next stub not initialized."
        conn = self.store.get_new_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM kvstore")
            rows = cursor.fetchall()
            for key, value in rows:
                self.ForwardToNext(key, value)
        except Exception as e:
            logging.error(f"Error in ForwardAll: {e}")
        finally:
            cursor.close()
            conn.close()
            self.is_tail = False # Relinquish tail status
            logging.info(f"Server {self.port} data forwarding to new tail completed.")
        
                            
    def UpdateTail(self, request, context):
        """Notifies the tail KV Store of a new replacement tail."""
        if not self.is_tail:
            logging.info(f"Server {self.port} is not the tail. Rejecting update tail request.")
            return kvstore_pb2.UpdateTailResponse(success=False)
        
        self.next_port = request.tail_port 
        self.next_stub = kvstore_pb2_grpc.KVStoreStub(grpc.insecure_channel(f'localhost:{self.next_port}'))
        # Spawn another thread to forward all KV pairs to the new tail. Once done, return success.
        threading.Thread(target=self.ForwardAll).start()
        logging.info(f"Server {self.port} forwarding data to new tail.")
        return kvstore_pb2.UpdateTailResponse(success=True)


    def Die(self, request, context):
        """Terminate the server to simulate failure."""
        logging.info(f"Server on port {self.port} crashed by request.")        
        self.stop_heartbeat.set() # Stops the heartbeat thread
        
        if request.clean: # Notify master
            self.send_heartbeat(is_alive=False)
        # Shut down the server
        self.server.stop(0)  # This will stop the server gracefully
        self.store.crash()
        logging.info("Server shut down successfully.")
        
        context.set_code(grpc.StatusCode.OK)
        context.set_details("Server is shutting down.")
        return kvstore_pb2.DieResponse(success=True)
    
    
    
def serve(args):
    """Run the gRPC server."""
    port, master_port = args.port, args.master_port,
    
    store = KeyValueStore(master_port, crash_db=args.crash_db)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
    kvstore_servicer = KeyValueStoreServicer(store,
                                             server,
                                             master_port,
                                             args.heartbeat_gap,
                                             args.prev_port,
                                             args.next_port
                                            )
    kvstore_pb2_grpc.add_KVStoreServicer_to_server(kvstore_servicer, server)

    server.add_insecure_port(f'[::]:{port}')
    server.start()
    logging.info(f"Server started on port {port}. Waiting for requests...")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(0)
        logging.info(f"Server on port {port} shutting down.")
        kvstore_servicer.stop_heartbeat.set()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Start a replica server.')
    parser.add_argument('--port', type=int, required=True, help='Port to run the server on.')
    parser.add_argument('-m', '--master_port', type=int, required=True, help='Master node port.')
    parser.add_argument("--prev_port", type=int, default=None, help='Port of the previous server in the chain (if any).')
    parser.add_argument('--next_port', type=int, default=None,
                        help='Child port of the next server in the chain (if any).')
    parser.add_argument('-i', "--heartbeat_gap", type=int, default=1, help='Heartbeat interval in seconds.')
    parser.add_argument("--crash_db", type=eval, default=True,
                        help="Whether to crash the database in failure simulation, which requires tail data forwarding to recover.")
    parser.add_argument("--verbose", type=eval, default=True, help="Whether to print debug info.")
    args = parser.parse_args()
    if not args.verbose:
        logging.disable(logging.INFO)

    # Ensure the DB directory exists
    os.makedirs(DB_PATH, exist_ok=True)

    # Start the server with the provided arguments
    serve(args)