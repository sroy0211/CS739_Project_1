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
    def __init__(self, max_size=100, ttl=0.2):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.ttl = ttl

    def get(self, key):
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                logging.info(f"Cache hit for key: {key}")
                return value
            else:
                logging.info(f"Cache expired for key: {key}")
                del self.cache[key]
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
    def __init__(self, cache_size=100, ttl=0.2, use_cache=True):
        self.channel = None
        self.stub = None
        self.use_cache = use_cache
        if self.use_cache:
            self.cache = Cache(max_size=cache_size, ttl=ttl)
        else:
            self.cache = None  # Cache is disabled

    def kv739_init(self, server_name):
        try:
            host, port = server_name.split(":")
            self.channel = grpc.insecure_channel(f'{host}:{port}')
            self.stub = kvstore_pb2_grpc.KVStoreStub(self.channel)
            logging.info("Initialized kvclient and connected to %s", server_name)
            return 0
        except Exception as e:
            logging.error(f"Error during connection setup: {e}")
            return -1

    def kv739_shutdown(self):
        try:
            if self.channel:
                self.channel.close()
            logging.info("Shutdown kvclient")
            return 0
        except Exception as e:
            logging.error(f"Error during shutdown: {e}")
            return -1

    def kv739_get(self, key, timeout):
        if self.use_cache and self.cache:
            cached_value = self.cache.get(key)
            if cached_value is not None:
                return 0, cached_value

        try:
            response = self.stub.Get(kvstore_pb2.GetRequest(key=key), timeout=timeout)
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
            return -1, ''

    def kv739_put(self, key, value):
        try:
            response = self.stub.Put(kvstore_pb2.PutRequest(key=key, value=value))
            if response.old_value_found:
                logging.info("Put operation successful for key '%s'. Old value: %s", key, response.old_value)
            else:
                logging.info("Put operation successful for key '%s'. No old value.", key)

            if self.use_cache and self.cache:
                self.cache.put(key, value)
            return 0 if response.old_value_found else 1, response.old_value if response.old_value_found else ''
        except grpc.RpcError as e:
            logging.error(f"Error during PUT operation: {e}")
            if self.use_cache and self.cache:
                self.cache.clear()
            return -1, ''

# Command-line argument parsing
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='KV739 Client Operations')
    parser.add_argument('operation', choices=['get', 'put'], help='Specify whether to get or put')
    parser.add_argument('key', help='The key for the GET/PUT operation')
    parser.add_argument('value', nargs='?', default='', help='The value for the PUT operation (optional for GET)')
    parser.add_argument('--server', default="localhost:50051", help='Server address (default: localhost:50051)')
    parser.add_argument('--timeout', type=int, default=5, help='Timeout for the GET operation (default: 5 seconds)')
    parser.add_argument('--cache_size', type=int, default=100, help='Maximum size of the cache (default: 100 entries)')
    parser.add_argument('--ttl', type=float, default=2, help='Time-to-Live for cache entries in seconds (default: 0.2 seconds)')
    parser.add_argument('--use_cache', action='store_true', help='Enable client-side cache')

    args = parser.parse_args()

    client = KV739Client(cache_size=args.cache_size, ttl=args.ttl, use_cache=args.use_cache)

    if client.kv739_init(args.server) == 0:
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
