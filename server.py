import sqlite3
import grpc
from concurrent import futures
import kvstore_pb2
import kvstore_pb2_grpc

# Define SQLite-based storage backend
class KeyValueStore:
    def __init__(self, db_file='kvstore.db'):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.conn.execute('''CREATE TABLE IF NOT EXISTS kvstore
                             (key TEXT PRIMARY KEY, value TEXT)''')
        print("Initialize KVStore")
        self.conn.commit()

    def get(self, key):
        cursor = self.conn.execute("SELECT value FROM kvstore WHERE key=?", (key,))
        result = cursor.fetchone()
        print("Get KVStore")
        print("Value:",result)
        if result:
            print("Result KVStore",result)
            return result[0], True
        return None, False

    def put(self, key, value):
        old_value, found = self.get(key)
        print("Put KVStore")
        if found:
            self.conn.execute("UPDATE kvstore SET value=? WHERE key=?", (value, key))
        else:
            self.conn.execute("INSERT INTO kvstore (key, value) VALUES (?, ?)", (key, value))
        
        self.conn.commit()
        return old_value, found

# Global store variable
store = KeyValueStore()

# Implement gRPC service
class KVStoreServicer(kvstore_pb2_grpc.KVStoreServicer):
    def Get(self, request, context):
        value, found = store.get(request.key)  # Use the global store
        print("Get_value",value)
        print("Get_found", found)
        print("Get KVStoreServicer")
        return kvstore_pb2.GetResponse(value=value if found else '', found=found)

    def Put(self, request, context):
        old_value, old_value_found = store.put(request.key, request.value)  # Use the global store
        print("Put_old_value",old_value)
        print("Put_old_value_found", old_value_found)
        print("Put KVStoreServicer")
        return kvstore_pb2.PutResponse(old_value=old_value if old_value_found else '', old_value_found=old_value_found)

# Start gRPC server
def serve():
    store.__init__() # Initialize the store here
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    kvstore_pb2_grpc.add_KVStoreServicer_to_server(KVStoreServicer(), server)  # No arguments needed now
    server.add_insecure_port('[::]:50051')
    print("Server started on port 50051.")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()