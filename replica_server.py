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

class KeyValueStoreServicer(kvstore_pb2_grpc.KVStoreServicer):
    """gRPC server for the key-value store."""

    def __init__(self, port, master_port, child_port=None):
        self.port = port
        self.master_port = master_port
        self.child_port = child_port
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
                time.sleep(2)  # Adjust heartbeat interval if needed
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

    def Crash(self, request, context):
        """Simulate a server crash."""
        self.stop_event.set()
        logging.info(f"Server on port {self.port} crashed.")
        return kvstore_pb2.CrashResponse()

def serve(port, master_port, child_port=None):
    """Run the gRPC server."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    kvstore_servicer = KeyValueStoreServicer(port, master_port, child_port)
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
    parser.add_argument('--master_port', type=int, required=True, help='Master node port.')
    parser.add_argument('--child_port', type=int, help='Child port of the next server in the chain (if any).')

    args = parser.parse_args()

    # Ensure the DB directory exists
    os.makedirs(DB_PATH, exist_ok=True)

    # Start the server with the provided arguments
    serve(args.port, args.master_port, args.child_port)