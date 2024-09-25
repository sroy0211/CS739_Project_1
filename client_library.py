import grpc
import kvstore_pb2
import kvstore_pb2_grpc

class KV739Client:
    def __init__(self):
        self.channel = None
        self.stub = None

    def kv739_init(self, server_name):
        """Initialize the client with server address."""
        try:
            host, port = server_name.split(":")
            self.channel = grpc.insecure_channel(f'{host}:{port}')
            self.stub = kvstore_pb2_grpc.KVStoreStub(self.channel)
            print("Initialize kvclient")
            return 0  # Success
        except Exception as e:
            print(f"Error during connection setup: {e}")
            return -1  # Failure

    def kv739_shutdown(self):
        """Shutdown the connection to the server."""
        try:
            if self.channel:
                self.channel.close()
            print("Shutdown kvclient")
            return 0  # Success
        except Exception as e:
            print(f"Error during shutdown: {e}")
            return -1  # Failure

    def kv739_get(self, key):
        """Retrieve the value corresponding to the key."""
        try:
            response = self.stub.Get(kvstore_pb2.GetRequest(key=key))
            if response.found:
                print("Get Value kvclient")
                return 0, response.value  # Success, key found
            else:
                return 1, ''  # Key not found
        except grpc.RpcError as e:
            print(f"Error during GET operation: {e}")
            return -1, ''  # Failure

    def kv739_put(self, key, value):
        """Store the specified value and retrieve any old value."""
        try:
            response = self.stub.Put(kvstore_pb2.PutRequest(key=key, value=value))
            if response.old_value_found:
                print("Put Old Value kvclient : ",response.old_value )
                return 0, response.old_value  # Success, old value found
            else:
                return 1, ''  # Success, no old value
        except grpc.RpcError as e:
            print(f"Error during PUT operation: {e}")
            return -1, ''  # Failure

# Example of usage
if __name__ == "__main__":
    client = KV739Client()

    # Initialize connection to server
    if client.kv739_init("localhost:50051") == 0:
        print("Connected to server.")

        # Example PUT operation
        old_value = " " * 2049  # Allocate space for the old value
        status = client.kv739_put("ename", "don")
        if status == 0:
            print(f"Put operation successful. Old value: {old_value}")
        elif status == 1:
            print("Put operation successful. No old value.")

        # Example GET operation
        value = " " * 2049  # Allocate space for the retrieved value
        status, value = client.kv739_get("name")
        if status == 0:
            print(f"Retrieved value for 'name': {value}")
        elif status == 1:
            print("Key 'name' not found.")

        # Shutdown connection
        if client.kv739_shutdown() == 0:
            print("Connection closed.")