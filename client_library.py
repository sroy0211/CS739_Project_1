import grpc
import kvstore_pb2
import kvstore_pb2_grpc
import logging
import argparse
import time

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

    def kv739_get(self, key, timeout):
        """Retrieve the value corresponding to the key, with a timeout."""
        try:
            response = self.stub.Get(kvstore_pb2.GetRequest(key=key), timeout=timeout)
            if response.found:
                logging.info("Retrieved value for key '%s': %s", key, response.value)
                return 0, response.value  # Success, key found
            else:
                logging.info("Key '%s' not found", key)
                return 1, ''  # Key not found
        except grpc.RpcError as e:
            # Handle timeout or other gRPC errors
            if e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                logging.error("GET operation timed out after %s seconds", timeout)
            else:
                logging.error(f"Error during GET operation: {e}")
            print("There is a failure")
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

# Command-line argument parsing
if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='KV739 Client Operations')
    parser.add_argument('operation', choices=['get', 'put'], help='Specify whether to get or put')
    parser.add_argument('key', help='The key for the GET/PUT operation')
    parser.add_argument('value', nargs='?', default='', help='The value for the PUT operation (optional for GET)')
    parser.add_argument('--server', default="localhost:50051", help='Server address (default: localhost:50051)')
    parser.add_argument('--timeout', type=int, default=0, help='Timeout for the GET operation to terminate in case of server failure/crash (in seconds)')
    parser.add_argument('--wait', type=int, default=0, help='Time to wait between PUT and GET operations (in seconds)')

    args = parser.parse_args()

    client = KV739Client()

    # Initialize connection to server
    if client.kv739_init(args.server) == 0:
        logging.info("Connected to server.")

        # Perform PUT operation
        if args.operation == 'put':
            if args.value:
                status, old_value = client.kv739_put(args.key, args.value)
                if status == 0:
                    logging.info(f"Status = {status}. Put operation successful. Old value: {old_value}")
                elif status == 1:
                    logging.info(f"Status = {status}. Put operation successful. No old value.")
                elif status == -1:
                    logging.error(f"Status = {status}. Put operation failed.")

                # Introduce a wait before the GET operation
                if args.wait > 0:
                    logging.info(f"Waiting for {args.wait} seconds before performing GET operation.")
                    time.sleep(args.wait)

                # Perform GET operation after the wait
                status, value = client.kv739_get(args.key, args.timeout)
                if status == 0:
                    logging.info(f"Status = {status}. Retrieved value for '{args.key}': {value}")
                elif status == 1:
                    logging.info(f"Status = {status}. Key '{args.key}' not found.")
                elif status == -1:
                    logging.error(f"Status = {status}. GET operation failed.")

            else:
                logging.error("PUT operation requires both key and value.")

        # Perform GET operation directly
        elif args.operation == 'get':
            status, value = client.kv739_get(args.key, args.timeout)
            if status == 0:
                logging.info(f"Status = {status}.Retrieved value for '{args.key}': {value}")
            elif status == 1:
                logging.info(f"Status = {status}.Key '{args.key}' not found.")
            elif status == -1:
                logging.error(f"Status = {status}.GET operation failed.")

        # Shutdown connection
        if client.kv739_shutdown() == 0:
            logging.info("Connection closed.")
