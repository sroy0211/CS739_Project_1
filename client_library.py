import grpc
import kvstore_pb2
import kvstore_pb2_grpc
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
            logging.info("Initialized kvclient and connected to %s", server_name)
            return 0  # Success
        except Exception as e:
            logging.error(f"Error during connection setup: {e}")
            return -1  # Failure

    def kv739_shutdown(self):
        """Shutdown the connection to the server."""
        try:
            if self.channel:
                self.channel.close()
            logging.info("Shutdown kvclient")
            return 0  # Success
        except Exception as e:
            logging.error(f"Error during shutdown: {e}")
            return -1  # Failure

    def kv739_get(self, key):
        """Retrieve the value corresponding to the key."""
        try:
            response = self.stub.Get(kvstore_pb2.GetRequest(key=key))
            if response.found:
                logging.info("Retrieved value for key '%s': %s", key, response.value)
                return 0, response.value  # Success, key found
            else:
                logging.info("Key '%s' not found", key)
                return 1, ''  # Key not found
        except grpc.RpcError as e:
            logging.error(f"Error during GET operation: {e}")
            return -1, ''  # Failure

    def kv739_put(self, key, value):
        """Store the specified value and retrieve any old value."""
        try:
            response = self.stub.Put(kvstore_pb2.PutRequest(key=key, value=value))
            if response.old_value_found:
                logging.info("Put operation successful for key '%s'. Old value: %s", key, response.old_value)
                return 0, response.old_value  # Success, old value found
            else:
                logging.info("Put operation successful for key '%s'. No old value.", key)
                return 1, ''  # Success, no old value
        except grpc.RpcError as e:
            logging.error(f"Error during PUT operation: {e}")
            return -1, ''  # Failure

# Example of usage
if __name__ == "__main__":
    client = KV739Client()

    # Initialize connection to server
    if client.kv739_init("localhost:50051") == 0:
        logging.info("Connected to server.")

        # Example PUT operation
        old_value = " " * 2049  # Allocate space for the old value
        status = client.kv739_put("oname", "ron")
        if status == 0:
            logging.info(f"Put operation successful. Old value: {old_value}")
        elif status == 1:
            logging.info("Put operation successful. No old value.")

        # Example GET operation
        value = " " * 2049  # Allocate space for the retrieved value
        status, value = client.kv739_get("zname")
        if status == 0:
            logging.info(f"Retrieved value for 'name': {value}")
        elif status == 1:
            logging.info("Key 'name' not found.")

        # Shutdown connection
        if client.kv739_shutdown() == 0:
            logging.info("Connection closed.")
