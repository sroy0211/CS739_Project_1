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
    def __init__(self, cache_size=100, ttl=0.2, use_cache=True):  # Corrected constructor
        self.channels = []  # List to hold channels
        self.use_cache = use_cache
        self.cache = Cache(max_size=cache_size, ttl=ttl) if use_cache else None
        self.head_stub # write to the head of the chain
        self.tail_stub # read from the tail of the chain
        
    # def kv739_init_from_file(self, config_file):
    #     """Initialize the client by reading service instances from a config file."""
    #     try:
    #         with open(config_file, 'r') as f:
    #             lines = f.readlines()
    #             server_ports = [line.strip() for line in lines if line.strip()]

    #         # Call the existing initialization logic with parsed ports
    #         return self.kv739_init(server_ports)

    #     except FileNotFoundError:
    #         logging.error(f"Config file '{config_file}' not found.")
    #         return -1
    #     except Exception as e:
    #         logging.error(f"Error reading config file '{config_file}': {e}")
    #         return -1

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

                self.current_stub = stub  # Set the current stub to the first available one
                self.channels.append(channel)  # Store the channel
                return 0  # Connection successful

            except grpc.RpcError as e:
                logging.error(f"Failed to connect to server on {endpoint}: {e}")
            except Exception as e:
                logging.error(f"Error during connection setup on {endpoint}: {e}")

        logging.error("Failed to connect to any server ports.")
        return -1

    def kv739_get(self, key, timeout):
        """Contacts the master once, get tail address and then contacts the tail directly via stub.
            If tail is down; contact the master again to get the new tail.
        """
        if self.use_cache and self.cache:
            cached_value = self.cache.get(key)
            if cached_value is not None:
                return 0, cached_value

        if self.current_stub:  # Check if we have a valid stub
            try:
                response = self.current_stub.Get(kvstore_pb2.GetRequest(key=key))
                if response.found:
                    logging.info("Retrieved value for key '%s': %s", key, response.value)
                    if self.use_cache and self.cache:
                        self.cache.put(key, response.value)
                    return 0, response.value
                else:
                    logging.info("Key '%s' not found", key)
                    return 1, ''
            except grpc.RpcError as e:
                logging.error(f"Error during GET operation: {e}")
                self.current_stub = None  # Mark current stub as invalid
                return self.kv739_get(key, timeout)  # Retry to find an alternative server
        return -1  # No available stub

    def kv739_put(self, key, value, timeout):
        """
            Contacts the master once, get head address and then establish a stub with the tail.
            If tails is down; contact the master to get the new tail.
        """
        if self.current_stub:  # Check if we have a valid stub
            try:
                response = self.current_stub.Put(
                    kvstore_pb2.PutRequest(key=key, value=value), timeout=timeout
                )
                if response.old_value_found:
                    logging.info("Put operation successful for key '%s'. Old value: %s", key, response.old_value)
                    return 0, response.old_value
                else:
                    logging.info("Put operation successful for key '%s'. No old value found", key)
                    return 0, ''
            except grpc.RpcError as e:
                logging.error(f"Error during PUT operation: {e}")
                self.current_stub = None  # Mark current stub as invalid
                return self.kv739_put(key, value, timeout)  # Retry to find an alternative server
        return -1, ''  # No available stub

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
    
    def kv739_die(self, server_name, clean=False):
        """Tell the a replica to terminate itself. 
            For now, just testing killing the head some number of times.        
        """
        if self.current_stub:  # Check if we have a valid stub
            try:
                response = self.current_stub.Die(
                    kvstore_pb2.DieRequest(server_name=server_name, clean=clean)
                )
                if response.success:
                    logging.info("Successfully contacted server %s to initiate self-destruction.", server_name)
                    return 0  # Successful termination request
                else:
                    logging.error("Failed to initiate self-destruction on server %s.", server_name)
                    return -1  # Failure in the response
            except grpc.RpcError as e:
                logging.error(f"Error during DIE operation: {e}")
                self.current_stub = None  # Mark current stub as invalid
                return -1  # No available stub
        logging.error("No available stub to contact for self-destruction.")
        return -1  # No available stub
    

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
