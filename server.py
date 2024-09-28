import sqlite3
import grpc
from concurrent import futures
import kvstore_pb2
import kvstore_pb2_grpc
import logging

# Set up logging to file
logging.basicConfig(
    filename='kvstore.log',  # Log file name
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Define SQLite-based storage backend
class KeyValueStore:
    def __init__(self, db_file='kvstore.db'):
        try:
            self.conn = sqlite3.connect(db_file, check_same_thread=False)
            self.conn.execute("PRAGMA journal_mode=WAL;")  # Enable WAL mode for better concurrency
            self.conn.execute("PRAGMA busy_timeout = 5000;")  # Wait up to 5 seconds for database locks
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
            with self.conn:  # Automatically handles BEGIN, COMMIT, and ROLLBACK
                if found:
                    self.conn.execute("UPDATE kvstore SET value=? WHERE key=?", (value, key))
                else:
                    self.conn.execute("INSERT INTO kvstore (key, value) VALUES (?, ?)", (key, value))
            logging.info("Put operation successful for key: %s", key)
            return old_value, found
        except sqlite3.Error as e:
            logging.error(f"Error writing to database for key '{key}': {e}")
            return None, False

# Restriction helper function
def validate_key_value(key, value):
    # Restrictions for keys:
    if len(key) > 128 or any(char in key for char in ["[", "]"]):
        return False, "Key must be a valid printable ASCII string, 128 or fewer bytes, and cannot contain '[' or ']'"

    # Restrictions for values:
    if len(value) > 2048 or any(char in value for char in ["[", "]"]):
        return False, "Value must be a valid printable ASCII string, 2048 or fewer bytes, and cannot contain '[' or ']'"
    
    return True, None

# Global store variable
store = KeyValueStore()

# Implement gRPC service
class KVStoreServicer(kvstore_pb2_grpc.KVStoreServicer):
    def Get(self, request, context):
        # Validate the key
        valid, error_message = validate_key_value(request.key, "")
        if not valid:
            logging.error(f"Get operation failed: {error_message}")
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(error_message)
            return kvstore_pb2.GetResponse(value='', found=False)

        # Proceed with the normal get operation
        value, found = store.get(request.key)  # Use the global store
        return kvstore_pb2.GetResponse(value=value if found else '', found=found)

    def Put(self, request, context):
        # Validate the key and value
        valid, error_message = validate_key_value(request.key, request.value)
        if not valid:
            logging.error(f"Put operation failed: {error_message}")
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(error_message)
            return kvstore_pb2.PutResponse(old_value='', old_value_found=False)

        # Proceed with the normal put operation
        old_value, old_value_found = store.put(request.key, request.value)  # Use the global store
        return kvstore_pb2.PutResponse(old_value=old_value if old_value_found else '', old_value_found=old_value_found)

# Start gRPC server
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=12))
    kvstore_pb2_grpc.add_KVStoreServicer_to_server(KVStoreServicer(), server)
    server.add_insecure_port('[::]:50051')
    logging.info("Server started on port 50051.")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
