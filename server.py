import sqlite3
import grpc
from concurrent import futures
import kvstore_pb2
import kvstore_pb2_grpc
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define SQLite-based storage backend
class KeyValueStore:
    def __init__(self, db_file='kvstore.db'):
        try:
            self.conn = sqlite3.connect(db_file, check_same_thread=False)
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
            self.conn.execute("BEGIN")
            if found:
                self.conn.execute("UPDATE kvstore SET value=? WHERE key=?", (value, key))
            else:
                self.conn.execute("INSERT INTO kvstore (key, value) VALUES (?, ?)", (key, value))
            self.conn.commit()
            logging.info("Put operation successful for key: %s", key)
            return old_value, found
        except sqlite3.Error as e:
            self.conn.rollback()
            logging.error(f"Error writing to database for key '{key}': {e}")
            return None, False

# Global store variable
store = KeyValueStore()

# Implement gRPC service
class KVStoreServicer(kvstore_pb2_grpc.KVStoreServicer):
    def Get(self, request, context):
        value, found = store.get(request.key)  # Use the global store
        return kvstore_pb2.GetResponse(value=value if found else '', found=found)

    def Put(self, request, context):
        old_value, old_value_found = store.put(request.key, request.value)  # Use the global store
        return kvstore_pb2.PutResponse(old_value=old_value if old_value_found else '', old_value_found=old_value_found)

# Start gRPC server
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    kvstore_pb2_grpc.add_KVStoreServicer_to_server(KVStoreServicer(), server)  # No arguments needed now
    server.add_insecure_port('[::]:50051')
    logging.info("Server started on port 50051.")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
