import sqlite3
import grpc
from concurrent import futures
import kvstore_pb2
import kvstore_pb2_grpc
import logging
import time
import threading
import csv
import os

# Set up logging to file
logging.basicConfig(
    filename='kvstore.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Define SQLite-based storage backend
class KeyValueStore:
    def __init__(self, db_file='kvstore.db'):
        try:
            self.conn = sqlite3.connect(db_file, check_same_thread=False)
            self.conn.execute("PRAGMA journal_mode=WAL;")
            self.conn.execute("PRAGMA busy_timeout = 5000;")
            self.conn.execute('''CREATE TABLE IF NOT EXISTS kvstore
                                 (key TEXT PRIMARY KEY, value TEXT)''')
            logging.info("Initialized KVStore")
        except sqlite3.Error as e:
            logging.error(f"Database connection error: {e}")
            raise

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

    def replicate(self, key, value, replicas):
        for replica in replicas:
            try:
                channel = grpc.insecure_channel(replica)
                stub = kvstore_pb2_grpc.KVStoreStub(channel)
                response = stub.Put(kvstore_pb2.PutRequest(key=key, value=value))
                if response.old_value_found:
                    logging.info(f"Successfully replicated to {replica} for key: {key}")
                    break
                else:
                    logging.error(f"Replication to {replica} failed for key: {key}")
                    break  # Stop replication if one fails
            except grpc.RpcError as e:
                logging.error(f"Failed to replicate to {replica}: {e}")
                break  # Stop on error
            
    def Ping(self, request, context):
        logging.info("Ping received.")
        return kvstore_pb2.PingResponse(is_alive=True)

def validate_key_value(key, value):
    if len(key) > 128 or any(char in key for char in ["[", "]"]):
        return False, "Key must be a valid printable ASCII string, 128 or fewer bytes, and cannot contain '[' or ']'"
    if len(value) > 2048 or any(char in value for char in ["[", "]"]):
        return False, "Value must be a valid printable ASCII string, 2048 or fewer bytes, and cannot contain '[' or ']'"
    return True, None

# Global store variable
store = KeyValueStore()

class KVStoreServicer(kvstore_pb2_grpc.KVStoreServicer):
    def __init__(self, server, replicas):
        self.server = server  # Store the server reference
        self.replicas = replicas

    def Get(self, request, context):
        valid, error_message = validate_key_value(request.key, "")
        if not valid:
            logging.error(f"Get operation failed: {error_message}")
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(error_message)
            return kvstore_pb2.GetResponse(value='', found=False)

        value, found = store.get(request.key)
        return kvstore_pb2.GetResponse(value=value if found else '', found=found)

    def Put(self, request, context):
        valid, error_message = validate_key_value(request.key, request.value)
        if not valid:
            logging.error(f"Put operation failed: {error_message}")
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(error_message)
            return kvstore_pb2.PutResponse(old_value='', old_value_found=False)

        old_value, old_value_found = store.put(request.key, request.value)
        
        # Replicate to other servers in the chain
        # if self.replicas:
            # store.replicate(request.key, request.value, self.replicas)

        return kvstore_pb2.PutResponse(old_value=old_value if old_value_found else '', old_value_found=old_value_found)
    
    def Die(self, request, context):
        logging.info(f"Received termination request for server: {request.server_name}. Clean: {request.clean}")
        
        if request.clean:
            # If clean termination is requested, perform any necessary cleanup here
            logging.info("Performing cleanup before termination.")
            store.close()  # Close the database connection
            # e.g., save state, close connections, etc.

        # Shut down the server
        if hasattr(self, 'server'):
            logging.info("Shutting down the server.")
            self.server.stop(0)  # This will stop the server gracefully
            logging.info("Server shut down successfully.")

        context.set_code(grpc.StatusCode.OK)
        context.set_details("Server is shutting down.")
        return kvstore_pb2.DieResponse(success=True)
    
    def Ping(self, request, context):
        logging.info("Ping received, server is alive.")
        return kvstore_pb2.PingResponse(is_alive=True)

def serve(port, replicas):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    kvstore_pb2_grpc.add_KVStoreServicer_to_server(KVStoreServicer(server, replicas), server)
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    try:
        while True:
            time.sleep(86400)  # Keep the server running
    except KeyboardInterrupt:
        logging.info("Shutting down the server gracefully.")
        server.stop(0)  # This will stop the server gracefully



def create_config_file(filename='server_config.txt', num_servers=100):
    """Create a configuration file for server instances."""
    with open(filename, mode='w') as file:
        for i in range(num_servers):
            hostname = "localhost"
            port = 50000 + i  # Incrementing port number for each server
            file.write(f"{hostname}:{port}\n")  # Writing in format hostname:port

def read_config_file(filename='server_config.txt'):
    """Read server configuration from a TXT file."""
    servers = []
    with open(filename, mode='r') as file:
        for line in file:
            hostname, port = line.strip().split(':')
            servers.append((hostname, int(port)))
    return servers

if __name__ == '__main__':
    # Create a configuration file with 100 server instances
    create_config_file()

    # Read the server configurations
    server_configs = read_config_file()
    
    # Create threads for each server
    threads = []
    for hostname, port in server_configs:
        thread = threading.Thread(target=serve, args=(port, [conf[1] for conf in server_configs if conf != (hostname, port)]))
        threads.append(thread)
        thread.start()
    
    # Optionally, join threads to wait for them to finish
    for thread in threads:
        thread.join()
