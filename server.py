import sqlite3
import grpc
from concurrent import futures
import kvstore_pb2
import kvstore_pb2_grpc
import logging
import time
import threading

# Set up logging to file
logging.basicConfig(
    filename='kvstore.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Define SQLite-based storage backend
class KeyValueStore:
    def __init__(self, db_file='kvstore.db'):  # Corrected __init method
        try:
            self.conn = sqlite3.connect(db_file, check_same_thread=False)
            self.conn.execute("PRAGMA journal_mode=WAL;")
            self.conn.execute("PRAGMA busy_timeout = 5000;")
            self.conn.execute('''CREATE TABLE IF NOT EXISTS kvstore
                                 (key TEXT PRIMARY KEY, value TEXT)''')
            logging.info("Initialized KVStore")
        except sqlite3.Error as e:
            logging.error(f"Database connection error: {e}")

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
                else:
                    logging.error(f"Replication to {replica} failed for key: {key}")
                    break  # Stop replication if one fails
            except grpc.RpcError as e:
                logging.error(f"Failed to replicate to {replica}: {e}")
                break  # Stop on error

def validate_key_value(key, value):
    if len(key) > 128 or any(char in key for char in ["[", "]"]):
        return False, "Key must be a valid printable ASCII string, 128 or fewer bytes, and cannot contain '[' or ']'"
    if len(value) > 2048 or any(char in value for char in ["[", "]"]):
        return False, "Value must be a valid printable ASCII string, 2048 or fewer bytes, and cannot contain '[' or ']'"
    return True, None

# Global store variable
store = KeyValueStore()

class KVStoreServicer(kvstore_pb2_grpc.KVStoreServicer):
    def __init__(self, replicas):  # Corrected __init method
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
        if self.replicas:
            store.replicate(request.key, request.value, self.replicas)

        return kvstore_pb2.PutResponse(old_value=old_value if old_value_found else '', old_value_found=old_value_found)
    
    def Ping(self, request, context):  # Add this method
        logging.info("Ping received, server is alive.")
        return kvstore_pb2.PingResponse(is_alive=True)  # Always return true

def serve(port, replicas):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=12))
    
    kvstore_pb2_grpc.add_KVStoreServicer_to_server(KVStoreServicer(replicas), server)
    
    server.add_insecure_port(f'[::]:{port}')
    logging.info(f"Server started on port {port}.")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':  # Corrected __name_ check
    # Define replicas for all servers
    replicas_for_server1 = ["localhost:50052", "localhost:50053"]
    replicas_for_server2 = ["localhost:50051", "localhost:50053"]
    replicas_for_server3 = ["localhost:50051", "localhost:50052"]

    # Create threads for each server
    thread1 = threading.Thread(target=serve, args=(50051, replicas_for_server1))
    thread2 = threading.Thread(target=serve, args=(50052, replicas_for_server2))
    thread3 = threading.Thread(target=serve, args=(50053, replicas_for_server3))
    
    # Start the threads
    thread1.start()
    thread2.start()
    thread3.start()
    
    # Optionally, join threads to wait for them to finish
    thread1.join()
    thread2.join()
    thread3.join()
