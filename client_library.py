import grpc
import kvstore_pb2
import kvstore_pb2_grpc
import logging
import argparse
import time
from collections import OrderedDict

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Cache:
    def __init__(self, max_size=100, ttl=0.2):  # Corrected constructor
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
    def __init__(self, port, cache_size=100, ttl=0.2, use_cache=True):  # Corrected constructor
        self.channels = []  # List to hold channels
        self.use_cache = use_cache
        self.cache = Cache(max_size=cache_size, ttl=ttl) if use_cache else None
        self.head_stub # write to the head of the chain
        self.tail_stub # read from the tail of the chain
        self.master_stub: kvstore_pb2_grpc.MasterNodeStub = kvstore_pb2_grpc.MasterNodeStub(grpc.insecure_channel(f'localhost:{port}'))

    def kv739_init(self, config_file):
        """Initialize connections to the provided list of server ports."""
        try:
            with open(config_file, 'r') as f:
                lines = f.readlines()
                server_ports = [line.strip() for line in lines if line.strip()]
        except FileNotFoundError:
            logging.error(f"Config file '{config_file}' not found.")
            return -1
        except Exception as e:
            logging.error(f"Error reading config file '{config_file}': {e}")
            return -1
        
        for endpoint in server_ports:
            try:
                host, port = endpoint.split(':')
                channel = grpc.insecure_channel(f'{host}:{port}')
                stub = kvstore_pb2_grpc.KVStoreStub(channel)
                logging.info("Initialized kvclient and connected to %s", endpoint)

                # Try to ping the server
                stub.Ping(kvstore_pb2.PingRequest())
                logging.info("Successfully connected to server on %s", endpoint)

                self.current_stub: kvstore_pb2_grpc.KVStoreStub = stub
                self.channels.append(channel)  # Store the channel
                return 0  # Connection successful

            except grpc.RpcError as e:
                logging.error(f"Failed to connect to server on {endpoint}: {e}")
            except Exception as e:
                logging.error(f"Error during connection setup on {endpoint}: {e}")

        logging.error("Failed to connect to any server ports.")
        return -1
    

    def _get_tail_stub(self):
        """Fetches the current tail address from the master and creates a gRPC stub."""
        try:
            # Request the current tail address from the master
            response = self.master_stub.GetHead(kvstore_pb2.Empty())
            if response.success:
                port, host = response.port, response.host
                logging.info(f"Client retrieved tail address: {host}:{port}")

                # Create and return a gRPC stub for the tail server
                tail_channel = grpc.insecure_channel(f'{host}:{port}')
                return kvstore_pb2_grpc.KVStoreStub(tail_channel)
            else:
                logging.error("Master failed to return a valid tail address.")
                return None
        except grpc.RpcError as e:
            logging.error(f"gRPC error during GetTailAddress call: {e}")
            return None  # Return None if an error occurs

    def _get_head_stub(self):
        """ Fetches the current head address from the master and creates a gRPC stub."""
        try:
            # Request the current head address from the master
            response = self.master_stub.GetHead(kvstore_pb2.Empty())
            if response.success:
                port, host = response.port, response.host
                logging.info(f"Client retrieved head address: {host}:{port}")

                # Create and return a gRPC stub for the head server
                head_channel = grpc.insecure_channel(f'{host}:{port}')
                return kvstore_pb2_grpc.KVStoreStub(head_channel)
            else:
                logging.error("Master failed to return a valid head address.")
                return None
        except grpc.RpcError as e:
            logging.error(f"Error during GetHeadAddress call: {e}")
            return None
        
    def kv739_get(self, key, timeout):
        """Contacts the master to get the tail address, 
        then communicates with the tail. If the tail fails, 
        contacts the master again to get a new tail."""

        # Step 1: Check the cache first
        if self.use_cache and self.cache:
            cached_value = self.cache.get(key)
            if cached_value is not None:
                return 0, cached_value  # Cache hit

        # Step 2: Retrieve a valid tail stub
        if not self.current_stub:  # If no current tail stub, get one from master
            self.current_stub = self._get_tail_stub()
            if not self.current_stub:
                logging.error("Failed to retrieve a valid tail stub.")
                return -1  # Could not proceed without a valid tail

        # Step 3: Attempt to GET from the tail server
        try:
            response = self.current_stub.Get(
                kvstore_pb2.GetRequest(key=key), timeout=timeout
            )
            if response.found:
                logging.info("Retrieved value for key '%s': %s", key, response.value)
                if self.use_cache and self.cache:
                    self.cache.put(key, response.value)  # Cache the result
                return 0, response.value  # Return the found value
            else:
                logging.info("Key '%s' not found", key)
                return 1, ''  # Key not found

        except grpc.RpcError as e:
            logging.error(f"Error during GET operation: {e}")

            # Step 4: If the tail fails, retry by fetching a new tail address
            logging.info("Retrying GET by contacting master for a new tail address...")
            self.current_stub = self._get_tail_stub()  # Get a new tail stub
            if self.current_stub:  # Retry the GET operation with the new stub
                return self.kv739_get(key, timeout)
            else:
                logging.error("Failed to get a new tail stub.")
                return -1  # Return failure if no new stub is available

        return -1  # Return failure if all attempts fail

    

    def kv739_put(self, key, value, timeout):
        """
        Contacts the master once to get the tail address and then performs a PUT operation using the tail.
        If the tail is down, contacts the master again to get a new tail and retries the operation.
        """

        # Step 1: Ensure we have a valid tail stub; if not, get it from the master.
        if not self.current_stub:
            self.current_stub = self._get_head_stub()
            if not self.current_stub:
                logging.error("Failed to retrieve a valid tail stub.")
                return -1, ''  # Return failure if no tail stub is available.

        # Step 2: Attempt the PUT operation with the current tail stub.
        try:
            response = self.current_stub.Put(
                kvstore_pb2.PutRequest(key=key, value=value), timeout=timeout
            )
            if response.old_value_found:
                logging.info(
                    "Put operation successful for key '%s'. Old value: %s",
                    key, response.old_value
                )
                return 0, response.old_value  # Return old value if it existed.
            else:
                logging.info("Put operation successful for key '%s'. No old value found", key)
                return 0, ''  # No previous value for the key.

        except grpc.RpcError as e:
            logging.error(f"Error during PUT operation: {e}")
            self.current_stub = None  # Mark current stub as invalid.

            # Step 3: Retry by fetching a new tail stub from the master.
            logging.info("Retrying PUT by contacting master for a new tail address...")
            self.current_stub = self._get_head_stub()

            if self.current_stub:  # If a new tail stub is obtained, retry the PUT operation.
                return self.kv739_put(key, value, timeout)

            logging.error("Failed to get a new tail stub for PUT operation.")
            return -1, ''  # Return failure if no new stub is available.
        # return -1, ''  # Return failure if all attempts fail.


    def kv739_shutdown(self):
        logging.info("Starting shutdown process.")
        if self.use_cache and self.cache:
            self.cache.clear()

        for channel in self.channels:
            try:
                channel.close()
                logging.info("Closed channel for stub connected to server.")
            except Exception as e:
                logging.error(f"Error during shutdown: {e}")

        time.sleep(1)  # Delay to ensure resources are released
        logging.info("Shutdown kvclient completed.")
        return 0
    
    def kv739_die(self, server_names, clean=False):
        """
        Sends termination requests to one or multiple servers. 
        If the master or tail node is terminated, the server handles reassignment automatically.

        Args:
            server_names (list or str): A single server name or a list of server names to terminate.
            clean (bool): If True, perform a clean shutdown. Defaults to False.

        Returns:
            int: 0 if all termination requests are successful, -1 if any failure occurs.
        """
        # Ensure server_names is treated as a list, even if a single server name is provided.
        if isinstance(server_names, str):
            server_names = [server_names]

        success = True  # Track overall success.

        for server_name in server_names:
            try:
                response = self.head_stub.Die(
                    kvstore_pb2.DieRequest(server_name=server_name, clean=clean)
                )
                if response.success:
                    logging.info("Successfully terminated server: %s", server_name)
                else:
                    logging.error("Failed to terminate server: %s", server_name)
                    success = False  # Mark failure.
            except grpc.RpcError as e:
                logging.error(f"Error during DIE operation on {server_name}: {e}")
                self.current_stub = None  # Mark current stub as invalid.
                success = False  # Mark failure.

        # Acknowledge the result to the client.
        if success:
            logging.info("All termination requests completed successfully.")
            return 0  # All operations succeeded.
        else:
            logging.error("One or more termination requests failed.")
            return -1  # At least one operation failed.
    

# Command-line argument parsing
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

    client = KV739Client(cache_size=args.cache_size, ttl=args.ttl, use_cache=args.use_cache)

    if args.config_file:
        status = client.kv739_init_from_file(args.config_file)
    else:
        logging.error("Config file is required.")
        exit(1)

    if status == 0:
        logging.info("Connected to server.")
        if args.operation == 'put':
            if args.value:
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
