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
        self.stubs = []  # List to hold multiple stubs
        self.channels = []  # List to hold channels
        self.use_cache = use_cache
        self.cache = Cache(max_size=cache_size, ttl=ttl) if use_cache else None

    def kv739_init(self, server_ports):
        for port in server_ports:
            try:
                host = 'localhost'
                channel = grpc.insecure_channel(f'{host}:{port}')
                stub = kvstore_pb2_grpc.KVStoreStub(channel)
                logging.info("Initialized kvclient and connected to %s", f'{host}:{port}')
                # Try to ping the server
                stub.Ping(kvstore_pb2.PingRequest())
                logging.info("Successfully connected to server on port %s", port)
                self.stubs.append(stub)  # Add stub to the list
                self.channels.append(channel)  # Store the channel
            except grpc.RpcError as e:
                logging.error(f"Failed to connect to server on port {port}: {e}")
            except Exception as e:
                logging.error(f"Error during connection setup on port {port}: {e}")

        if not self.stubs:
            logging.error("Failed to connect to any server ports.")
            return -1
        return 0

    def kv739_shutdown(self):
        logging.info("Starting shutdown process.")
        for channel in self.channels:
            try:
                channel.close()  # Close the channel for each stub
                logging.info("Closed channel for stub connected to server.")
            except Exception as e:
                logging.error(f"Error during shutdown: {e}")

        # Delay to ensure resources are released
        time.sleep(1)

        logging.info("Shutdown kvclient completed.")
        return 0

    def kv739_get(self, key, timeout):
        if self.use_cache and self.cache:
            cached_value = self.cache.get(key)
            if cached_value is not None:
                return 0, cached_value

        # Loop through available stubs to attempt to get the value
        for stub in self.stubs:
            try:
                response = stub.Get(kvstore_pb2.GetRequest(key=key), timeout=timeout)
                if response.found:
                    logging.info("Retrieved value for key '%s': %s", key, response.value)
                    if self.use_cache and self.cache:
                        self.cache.put(key, response.value)
                    return 0, response.value
                else:
                    logging.info("Key '%s' not found", key)
                    return 1, ''
            except grpc.RpcError as e:
                if e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                    logging.error("GET operation timed out after %s seconds", timeout)
                else:
                    logging.error(f"Error during GET operation: {e}")
                continue  # Attempt with the next stub
        return -1, ''

    def kv739_put(self, key, value):
        for stub in self.stubs:
            try:
                response = stub.Put(kvstore_pb2.PutRequest(key=key, value=value))
                if response.old_value_found:
                    logging.info("Put operation successful for key '%s'. Old value: %s", key, response.old_value)
                    return 0, response.old_value  # Return a tuple with status and old value
                else:
                    logging.info("Put operation successful for key '%s'. No old value found", key)
                    return 0, ''  # Return a tuple with status and empty string for old value
            except grpc.RpcError as e:
                logging.error(f"Error during PUT operation: {e}")
                continue  # Attempt with the next stub
        return -1, ''  # Return a tuple on error

# Command-line argument parsing
if __name__ == "__main__":  # Corrected name check
    parser = argparse.ArgumentParser(description='KV739 Client Operations')
    parser.add_argument('operation', choices=['get', 'put'], help='Specify whether to get or put')
    parser.add_argument('key', help='The key for the GET/PUT operation')
    parser.add_argument('value', nargs='?', default='', help='The value for the PUT operation (optional for GET)')
    parser.add_argument('--ports', type=int, nargs='+', default=[50051, 50052, 50053], help='List of server ports to try (default: 50051 50052 50053)')
    parser.add_argument('--timeout', type=int, default=5, help='Timeout for the GET operation (default: 5 seconds)')
    parser.add_argument('--cache_size', type=int, default=100, help='Maximum size of the cache (default: 100 entries)')
    parser.add_argument('--ttl', type=float, default=0.2, help='Time-to-Live for cache entries in seconds (default: 0.2 seconds)')
    parser.add_argument('--use_cache', action='store_true', help='Enable client-side cache')

    args = parser.parse_args()

    client = KV739Client(cache_size=args.cache_size, ttl=args.ttl, use_cache=args.use_cache)

    if client.kv739_init(args.ports) == 0:
        logging.info("Connected to server.")

        if args.operation == 'put':
            if args.value:
                status, old_value = client.kv739_put(args.key, args.value)
                if status == 0:
                    logging.info(f"Status = {status}. Put operation successful. Old value: {old_value}")
                elif status == 1:
                    logging.info(f"Status = {status}. Put operation successful. No old value.")
                elif status == -1:
                    logging.error(f"Status = {status}. Put operation failed.")
            else:
                logging.error("PUT operation requires both key and value.")

        elif args.operation == 'get':
            status, value = client.kv739_get(args.key, args.timeout)
            if status == 0:
                logging.info(f"Status = {status}. Retrieved value for '{args.key}': {value}")
            elif status == 1:
                logging.info(f"Status = {status}. Key '{args.key}' not found.")
            elif status == -1:
                logging.error(f"Status = {status}. GET operation failed.")

        if client.kv739_shutdown() == 0:
            logging.info("Connection closed.")
