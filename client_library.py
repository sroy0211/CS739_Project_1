import grpc
import kvstore_pb2
import kvstore_pb2_grpc
import logging
import argparse
import time
from collections import OrderedDict
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Cache:
    def __init__(self, max_size=100, ttl=0.2):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.ttl = ttl

    def get(self, key):
        if key in self.cache:
            value, timestamp = self.cache.pop(key)
            if time.time() - timestamp < self.ttl:
                self.cache[key] = (value, time.time())
                logging.info(f"Cache hit for key: {key}")
                return value
            else:
                logging.info(f"Cache expired for key: {key}")
        logging.info(f"Cache miss for key: {key}")
        return None

    def put(self, key, value):
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)
        self.cache[key] = (value, time.time())

    def clear(self):
        logging.info("Clearing cache due to server crash.")
        self.cache.clear()

class KV739Client:
    def __init__(self, port, cache_size=100, ttl=0.2, use_cache=True):
        self.channels = []
        self.use_cache = use_cache
        self.cache = Cache(max_size=cache_size, ttl=ttl) if use_cache else None
        self.master_stub = None
        self.head_stub = None
        self.tail_stub = None

    def kv739_init(self, config_file):
        """Initialize connections to the master and tail servers."""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)  # Load the JSON content

            master_port = config['master_port']
            tail_port = config['child_ports'][-1]  # Assuming the last child is the tail server

            # Connect to the master server
            master_channel = grpc.insecure_channel(f'localhost:{master_port}')
            self.master_stub = kvstore_pb2_grpc.MasterNodeStub(master_channel)
            logging.info(f"Connected to master server at port: {master_port}")

            # Connect to the tail server
            tail_channel = grpc.insecure_channel(f'localhost:{tail_port}')
            self.tail_stub = kvstore_pb2_grpc.KVStoreStub(tail_channel)
            logging.info(f"Connected to tail server at port: {tail_port}")

            return 0

        except Exception as e:
            logging.error(f"Error reading config file '{config_file}': {e}")
            return -1


    def _get_tail_stub(self):
        """Fetches the tail address from the master and returns the tail stub."""
        try:
            response = self.master_stub.GetTail(kvstore_pb2.Empty())
            if response.success:
                host, port = response.host, response.port
                logging.info(f"Retrieved tail address: {host}:{port}")
                
                # Check if tail_stub is already initialized; if not, create it
                if self.tail_stub is None:
                    tail_channel = grpc.insecure_channel(f'{host}:{port}')
                    self.tail_stub = kvstore_pb2_grpc.KVStoreStub(tail_channel)
                    logging.info(f"Initialized tail stub for: {host}:{port}")
                    
                return self.tail_stub

        except grpc.RpcError as e:
            logging.error(f"Error during GetTail call: {e}")
            
        return None


    def _get_head_stub(self):
        """Fetches the head address from the master and returns the head stub."""
        try:
            response = self.master_stub.GetHead(kvstore_pb2.Empty())
            if response.success:
                host, port = response.host, response.port
                logging.info(f"Retrieved head address: {host}:{port}")

                # Check if head_stub is already initialized; if not, create it
                if self.head_stub is None:
                    head_channel = grpc.insecure_channel(f'{host}:{port}')
                    self.head_stub = kvstore_pb2_grpc.KVStoreStub(head_channel)
                    logging.info(f"Initialized head stub for: {host}:{port}")

                return self.head_stub

        except grpc.RpcError as e:
            logging.error(f"Error during GetHead call: {e}")

        return None


    def kv739_get(self, key, timeout=5):
        """Fetches a key's value from the tail server."""
        
        # Check if the value is in the cache
        if self.use_cache and (value := self.cache.get(key)) is not None:
            return 0, value

        # Initialize tail stub if not already done
        if not self.tail_stub:
            self.tail_stub = self._get_tail_stub()
            if not self.tail_stub:
                logging.error(f"Client failed to initialize tail stub.")
                return -1, ''  

        try:
            # Make a Get request to the tail server
            response = self.tail_stub.Get(kvstore_pb2.GetRequest(key=key), timeout=timeout)
            
            # Check if the key was found and handle the response
            if response.found:
                if self.use_cache:
                    self.cache.put(key, response.value)  # Cache the value if caching is enabled
                return 0, response.value  # Return success and the value
            
            return 1, ''  # Key not found, return code 1
        
        except grpc.RpcError as e:
            logging.error(f"GET operation failed: {e}")
            self.tail_stub = None  # Reset tail stub on error
            self.cache.clear()  # Clear the cache on error
            return self.kv739_get(key, timeout)  # Retry the operation


    def kv739_put(self, key, value, timeout=5, retries=3):
        """Performs a PUT operation using the head server."""
        # Ensure the head stub is available
        if not self.head_stub:
            self.head_stub = self._get_head_stub()
            if not self.head_stub:
                logging.error("Failed to get head stub.")
                return -1, ''  # Internal error

        try:
            # Create the PutRequest object
            request = kvstore_pb2.PutRequest(key=key, value=value)

            # Send the request to the head node
            response = self.head_stub.Put(request, timeout=timeout)

            # Check if an old value was found and the operation succeeded
            if response.old_value_found:
                old_value = response.old_value
                logging.info(f"Updated key '{key}' from old value '{old_value}' to new value '{value}'")
                return 0, old_value  # Return 0 on success with old value
            else:
                logging.info(f"Successfully put key '{key}' with new value '{value}'")
                return 1, ''  # Return 1 on success without old value

        except grpc.RpcError as e:
            logging.error(f"PUT operation failed: {e}")

            if retries > 0:
                self.head_stub = None  # Reset head stub for next attempt
                logging.info(f"Retrying... attempts left: {retries}")
                return self.kv739_put(key, value, timeout, retries - 1)  # Retry the operation

            logging.error("Max retries exceeded; operation failed.")
            return -2, ''  # Return -2 on communication failure

        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return -1, ''  # Return -1 on any other internal error



    def kv739_shutdown(self):
        """Shuts down the client and releases resources."""
        logging.info("Shutting down client.")

        # Clear the cache if enabled
        if self.use_cache:
            self.cache.clear()

        # Close all channels
        for channel in self.channels:
            try:
                channel.close()
                logging.info("Successfully closed a channel.")
            except Exception as e:
                logging.error(f"Error closing channel: {e}")

        # Reset any client state if necessary
        self.head_stub = None  # Reset the head stub
        self.channels = []  # Clear the channels list
        self.cache = None  # Optional: Clear cache reference

        # Allow time for resources to be freed
        time.sleep(1)

        logging.info("Client shutdown complete.")
        return 0  # Return success


    def kv739_die(self, server_names, clean=False):
        """Sends termination requests to the specified servers."""
        if isinstance(server_names, str):
            server_names = [server_names]

        success_count = 0  # Count successful terminations

        for server_name in server_names:
            try:
                host, port = server_name.split(':')
                channel = grpc.insecure_channel(f'{host}:{port}')
                stub = kvstore_pb2_grpc.KVStoreStub(channel)
                request = kvstore_pb2.DieRequest(clean=clean)

                # Send the Die request to the server
                stub.Die(request)
                logging.info(f"Terminated server {server_name} with clean={clean}")
                success_count += 1  # Increment success count
                
            except grpc.RpcError as e:
                logging.error(f"Error terminating {server_name}: {e}")
                # Return -1 on the first failure
                return -1
            finally:
                channel.close()  # Close the channel to free resources

        # Return 0 if at least one server was successfully contacted
        return 0 if success_count > 0 else -1



def is_valid_key(key):
    """Validate key constraints."""
    if len(key) > 128 or any(c in key for c in ['[', ']']) or not all(32 <= ord(c) <= 126 for c in key):
        logging.error("Invalid key: Keys must be printable ASCII without special characters, 128 bytes or less, and cannot include '[' or ']' characters.")
        return False
    return True

def is_valid_value(value):
    """Validate value constraints."""
    if len(value) > 2048 or any(c in value for c in ['[', ']']) or not all(32 <= ord(c) <= 126 for c in value):
        logging.error("Invalid value: Values must be printable ASCII without special characters, 2048 bytes or less, and cannot include '[' or ']' characters.")
        return False
    return True 

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='KV739 Client Operations')
    parser.add_argument('operation', choices=['get', 'put', 'die'], help='Specify the operation (get, put, die)')
    parser.add_argument('key', help='The key for the GET/PUT operation or the server port for DIE')
    parser.add_argument('value', nargs='?', default='', help='The value for the PUT operation (optional for GET)')
    parser.add_argument('--clean', type=int, choices=[0, 1], help='Clean termination (1 for clean, 0 for immediate)')
    parser.add_argument('--config_file', type=str, default="server_config.txt", help='Path to config file with server instances')
    parser.add_argument('--timeout', type=int, default=5, help='Timeout for the GET operation (default: 5 seconds)')
    parser.add_argument('--cache_size', type=int, default=100, help='Maximum size of the cache (default: 100 entries)')
    parser.add_argument('--ttl', type=float, default=0.2, help='Time-to-Live for cache entries in seconds (default: 0.2)')
    parser.add_argument('--use_cache', action='store_true', help='Enable client-side cache')

    args = parser.parse_args()

    # Validate key and value
    if not is_valid_key(args.key):
        exit(1)  # Exit if the key is invalid
    if args.operation == 'put' and not is_valid_value(args.value):
        exit(1)  # Exit if the value is invalid for PUT
    if args.operation == 'get' and len(args.key) <= 2048:  # The string must be at least 1 byte larger than the max value size
        logging.error("Invalid operation: For GET, the key must be more than 2048 bytes long.")
        exit(1)

    client = KV739Client(cache_size=args.cache_size, ttl=args.ttl, use_cache=args.use_cache)

    if args.config_file:
        status = client.kv739_init(args.config_file)
    else:
        logging.error("Config file is required.")
        exit(1)

    if status == 0:
        logging.info("Connected to server.")
        if args.operation == 'put':
            if args.value:
                # Ensure old_value is more than the max size when doing a PUT
                if len(args.value) <= 2048:
                    logging.error("Invalid operation: Old value must be at least 1 byte larger than the maximum value size (2048 bytes).")
                    exit(1)
                client.kv739_put(args.key, args.value, args.timeout)
            else:
                logging.error("PUT operation requires both key and value.")
        elif args.operation == 'get':
            client.kv739_get(args.key, args.timeout)
        elif args.operation == 'die':
            if args.clean is not None:
                client.kv739_die(args.key, args.clean)
            else:
                logging.error("DIE operation requires --clean argument (0 or 1).")

        client.kv739_shutdown()
