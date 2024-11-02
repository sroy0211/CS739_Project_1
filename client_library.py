import grpc
import kvstore_pb2
import kvstore_pb2_grpc
import logging
import argparse
import time
from collections import OrderedDict
import json
import sys
from typing import List

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
        logging.info("Clearing cache.")
        self.cache.clear()

class KV739Client:
    def __init__(self, cache_size=100, ttl=0.2, use_cache=False, verbose=False, retries=4, host='localhost'):
        self.channels = []
        self.use_cache = use_cache
        self.cache = Cache(max_size=cache_size, ttl=ttl) if use_cache else None
        self.master_stub = None
        self.head_stub = self.head_port = None
        self.tail_stub = self.tail_port = None
        self.verbose = verbose
        self.retries = retries
        self.host = host
        
        if not verbose:
            logging.disable(logging.INFO)
        self.initialized = False
        
    def kv739_init(self, config_file):
        """Initialize connections to the master and tail servers."""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f) 

            # Connect to the master server
            self.master_port = config['master_port']
            master_channel = grpc.insecure_channel(f'{self.host}:{self.master_port}')
            self.master_stub = kvstore_pb2_grpc.MasterNodeStub(master_channel)
            logging.info(f"Connected to master server at port: {self.master_port}")

            # Connect to the tail server
            self._get_tail_stub()
            logging.info(f"Connected to tail server at port: {self.tail_port}")

            self._get_head_stub()            
            logging.info(f"Connected to head server port: {self.head_port}")
            
            self.initialized = True
            return 0
    
        except Exception as e:
            logging.error(f"Error reading config file '{config_file}': {e}")
            return -1

    def _get_tail_stub(self, replace=False):
        """Fetches the tail address from the master and returns the tail stub."""
        try:
            response = self.master_stub.GetTail(kvstore_pb2.GetTailRequest(replace=replace))
            host, port = response.hostname, response.port
            self.tail_port = port
            logging.info(f"Retrieved tail address: {host}:{port}")
            
            # Check if tail_stub is already initialized; if not, create it
            if self.tail_stub is None or self.tail_port != port:
                tail_channel = grpc.insecure_channel(f'{host}:{port}')
                self.tail_stub = kvstore_pb2_grpc.KVStoreStub(tail_channel)
                logging.info(f"Initialized tail stub for: {host}:{port}")
                
            return self.tail_stub

        except grpc.RpcError as e:
            logging.error(f"Error during GetTail call: {e}")
            
        return None

    def _get_head_stub(self, replace=False):
        """Fetches the head address from the master and returns the head stub."""
        try:
            # Check if the head server is alive
            
            response = self.master_stub.GetHead(kvstore_pb2.GetHeadRequest(replace=replace))
            host, port = response.hostname, response.port
            self.head_port = port
            logging.info(f"Retrieved head address: {host}:{port}")

            # Check if head_stub is already initialized; if not, create it
            if self.head_stub is None or self.head_port != port:
                head_channel = grpc.insecure_channel(f'{host}:{port}')
                self.head_stub = kvstore_pb2_grpc.KVStoreStub(head_channel)
                logging.info(f"Initialized head stub for: {host}:{port}")

            return self.head_stub

        except grpc.RpcError as e:
            logging.error(f"Error during GetHead call: {e}")



    def _get_middle_stub(self):
        """Fetches the middle server's stub from the master."""
        try:
            response = self.master_stub.GetMiddle(kvstore_pb2.GetMiddleRequest())
            host, port = response.hostname, response.port
            logging.info(f"Retrieved middle address: {host}:{port}")
            
            # Check if middle_stub is already initialized; if not, create it
            if self.middle_stub is None:
                middle_channel = grpc.insecure_channel(f'{host}:{port}')
                self.middle_stub = kvstore_pb2_grpc.KVStoreStub(middle_channel)
                logging.info(f"Initialized middle stub for: {host}:{port}")
                
            return self.middle_stub

        except grpc.RpcError as e:
            logging.error(f"Error during GetMiddle call: {e}")

        return None

    def kv739_get(self, key, timeout=5, retries=3, debug_port=None):
        """Fetches a key's value from the tail server."""
        if not self.initialized:
            raise Exception("Client not initialized. Call kv739_init() first.")
        
        # Check if the value is in the cache
        if self.use_cache and (value := self.cache.get(key)) is not None:
            return 0, value

        try:
            if debug_port is not None:
                temp_stub = kvstore_pb2_grpc.KVStoreStub(grpc.insecure_channel(f'{self.host}:{debug_port}'))
                response = temp_stub.Get(kvstore_pb2.GetRequest(key=key), timeout=timeout)
            else:
                # Make a Get request to the tail server
                response = self.tail_stub.Get(kvstore_pb2.GetRequest(key=key), timeout=timeout)

            # if not success, reach master for tail
            if not response.success and retries > 0:
                logging.info(f"Server {self.tail_port} rejected the request. Maybe it's not the tail? Remaining retries: {retries}")
                self._get_tail_stub()
                return self.kv739_get(key, timeout, retries - 1)
            
            # Check if the key was found and handle the response
            if response.found:
                if self.use_cache:
                    self.cache.put(key, response.value)  # Cache the value if caching is enabled
                logging.info(f"Successfully retrieved key '{key}' with value '{response.value}' from tail server {self.tail_port}")
                return 0, response.value  # Return success and the value
            else:
                logging.info(f"Key '{key}' not found at tail server {self.tail_port}")
                return 1, ''  # Key not found, return code 1
        
        except grpc.RpcError as e:
            logging.error(f"GET operation failed: {e}")
            self._get_tail_stub(replace=False)  # Tail server crashed
            if self.use_cache:
                self.cache.clear()  # Clear the cache on error
            if retries > 0:
                return self.kv739_get(key, timeout, retries - 1)
            else:
                return -2, ''  # Return -2 on communication failure
        
        except Exception as e:
            logging.error(f"Unexpected error: {e} in contacting tail server {self.tail_port}")
            return -1, ''


    def kv739_put(self, key, value, timeout=5, retries=4):
        """Performs a PUT operation using the head server."""
        if not self.initialized:
            raise Exception("Client not initialized. Call kv739_init() first.")
        if retries < 0:
            logging.error("PUT operation failed after multiple retries.")
            return -3, ''
        
        try:
            response = self.head_stub.Put(kvstore_pb2.PutRequest(key=key, value=value), timeout=timeout)
            # Get new head from master
            if not response.success:
                logging.info(f"Head server {self.head_port} rejected the request. Reaching master for new head.")
                self._get_head_stub()
                return self.kv739_put(key, value, timeout, retries - 1)
            
            # Check if an old value was found and the operation succeeded
            if response.old_value_found:
                old_value = response.old_value
                logging.info(f"Updated key '{key}' from old value '{old_value}' to new value '{value}' at head server {self.head_port}")
                return 0, old_value  # Return 0 on success with old value
            else:
                logging.info(f"Successfully put key '{key}' with new value '{value}' at head server {self.head_port}")
                return 1, ''  # Return 1 on success without old value

        except grpc.RpcError as e:
            logging.error(f"PUT operation failed: {e}")
            if retries > 0:
                self._get_head_stub() # Reset head stub for next attempt
                logging.info(f"Retrying... attempts left: {retries}")
                return self.kv739_put(key, value, timeout, retries - 1)  # Retry the operation

            logging.error("Max retries exceeded; operation failed.")
            return -2, ''  # Return -2 on communication failure

        except Exception as e:
            logging.error(f"Unexpected error: {e} in contacting head server {self.head_port}")
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


    def kv739_die(self, server_type: str, clean: int = 0, server_ports: List[int] = None, host='localhost'):
        """Kills the specified server using its stub."""
        if not self.initialized:
            raise Exception("Client not initialized. Call kv739_init() first.")
        
        try:
            if server_ports is not None:
                # Kill the specified server
                for server_port in server_ports:
                    stub = kvstore_pb2_grpc.KVStoreStub(grpc.insecure_channel(f'{host}:{server_port}'))
                    logging.info(f"Connected to server at port: {server_port}")
                    stub.Die(kvstore_pb2.DieRequest(clean=clean))
                    
            elif server_type == 'head':
                # Use the existing method to get the middle server's stub
                head_stub = self._get_head_stub()
                if head_stub is None:
                    logging.error("Failed to retrieve head server stub.")
                    return -1
    
                logging.info(f"Attempting to kill the head Server...")
                if clean == 1:
                    # Allow the middle server to clean up before shutting down
                    die_request = kvstore_pb2.DieRequest(clean=True)
                    head_stub.Die(die_request)
                    logging.info("Head Server terminated cleanly.")
                else:
                    # Force the middle server to exit immediately
                    logging.info("Forcing head server to terminate non-clean.")
                    head_stub.Die(kvstore_pb2.DieRequest(clean=False))
    
            elif server_type == 'tail':
                # Use the existing method to get the tail server's stub
                tail_stub = self._get_tail_stub()
                if tail_stub is None:
                    logging.error("Failed to retrieve tail server stub.")
                    return -1
    
                logging.info(f"Attempting to kill the Tail Server...")
                if clean == 1:
                    # Allow the tail server to clean up before shutting down
                    die_request = kvstore_pb2.DieRequest(clean=True)
                    tail_stub.Die(die_request)
                    logging.info("Tail Server terminated cleanly.")
                else:
                    # Force the tail server to exit immediately
                    logging.info("Forcing Tail Server to terminate immediately.")
                    tail_stub.Die(kvstore_pb2.DieRequest(clean=False))
    
            return 0  # Success
    
        except grpc.RpcError as e:
            logging.error(f"gRPC error while killing {server_type} server: {e}")
            return -1  # Failure on gRPC error
    
        except Exception as e:
            logging.error(f"Unexpected error while killing {server_type} server: {e}")
            return -1  # Failure on other exceptions

    def kv739_start(self, server_port: List[int] = None, host='localhost', new: int = 1):
        """Starts a new server by asking the master stub."""
        if not self.initialized:
            raise Exception("Client not initialized. Call kv739_init() first.")
        try:
            res = self.master_stub.StartServer(kvstore_pb2.StartServerRequest(new=new, ports=server_port, hostname=host))
            if res.success:
                logging.info(f"Successfully started new server at port: {server_port}")
                return 0
            else:
                logging.error(f"Failed to start new server at port: {server_port}")
                return -1
        except grpc.RpcError as e:
            logging.error(f"gRPC error while starting new server at port {server_port}: {e}")
            return -1
        

    def kv739_leave(self, server_type: str, clean: int = 0, server_ports: List[int] = None, host='localhost'):
        """Kills the specified server using its stub."""
        if not self.initialized:
            raise Exception("Client not initialized. Call kv739_init() first.")
        
        try:
            if server_ports is not None:
                # Kill the specified server
                for server_port in server_ports:
                    stub = kvstore_pb2_grpc.KVStoreStub(grpc.insecure_channel(f'{host}:{server_port}'))
                    logging.info(f"Connected to server at port: {server_port}")
                    stub.Leave(kvstore_pb2.LeaveRequest(clean=clean))
                    
            elif server_type == 'head':
                # Use the existing method to get the middle server's stub
                head_stub = self._get_head_stub()
                if head_stub is None:
                    logging.error("Failed to retrieve head server stub.")
                    return -1
    
                logging.info(f"Attempting to kill the head Server...")
                if clean == 1:
                    # Allow the middle server to clean up before shutting down
                    leave_request = kvstore_pb2.LeaveRequest(clean=True)
                    head_stub.Leave(leave_request)
                    logging.info("Head Server terminated cleanly.")
                else:
                    # Force the middle server to exit immediately
                    logging.info("Forcing head server to terminate non-clean.")
                    head_stub.Leave(kvstore_pb2.LeaveRequest(clean=False))
    
            elif server_type == 'tail':
                # Use the existing method to get the tail server's stub
                tail_stub = self._get_tail_stub()
                if tail_stub is None:
                    logging.error("Failed to retrieve tail server stub.")
                    return -1
    
                logging.info(f"Attempting to kill the Tail Server...")
                if clean == 1:
                    # Allow the tail server to clean up before shutting down
                    leave_request = kvstore_pb2.LeaveRequest(clean=True)
                    tail_stub.Leave(leave_request)
                    logging.info("Tail Server terminated cleanly.")
                else:
                    # Force the tail server to exit immediately
                    logging.info("Forcing Tail Server to terminate immediately.")
                    tail_stub.Leave(kvstore_pb2.LeaveRequest(clean=False))
    
            return 0  # Success
    
        except grpc.RpcError as e:
            logging.error(f"gRPC error while leaving {server_type} server: {e}")
            return -1  # Failure on gRPC error
    
        except Exception as e:
            logging.error(f"Unexpected error while leaving {server_type} server: {e}")
            return -1  # Failure on other exceptions



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
    parser.add_argument('operation', choices=['get', 'put', 'die', 'start', 'leave'], help='Specify the operation (get, put, die, start, leave)')
    parser.add_argument('key', nargs='?', default='', help='The key for the GET/PUT operation')
    parser.add_argument('value', nargs='?', default='', help='The value for the PUT operation (optional for GET)')
    parser.add_argument("--kill_type", default="head", choices=["head", "tail", "middle"], help="The server type to terminate for die function")
    parser.add_argument("--debug_port", type=int, default=None, help="Connect to the replica at this port for debugging")
    parser.add_argument('--new', type=int, choices=[0, 1], help="1 to start a new instance, 0 to recover for the start function.")
    parser.add_argument('--clean', type=int, choices=[0, 1], help='Clean termination (1 for clean, 0 for immediate) for (die and leave) function.')
    parser.add_argument('--config_file', type=str, default="server_config.json", help='Path to config file with server instances')
    parser.add_argument('--timeout', type=int, default=5, help='Timeout for the GET operation (default: 5 seconds)')
    parser.add_argument('--cache_size', type=int, default=100, help='Maximum size of the cache (default: 100 entries)')
    parser.add_argument('--ttl', type=float, default=0.5, help='Time-to-Live for cache entries in seconds (default: 0.2)')
    parser.add_argument('--use_cache', default=True, action='store_true', help='Enable client-side cache')
    parser.add_argument('--verbose', default=True, type=eval, help='Enable debug logging')
    parser.add_argument('--kill_ports', nargs='+', type=int, help='List of ports to kill')
    parser.add_argument("--start_port", type=int, default=None, help="Port to start the new server")
    parser.add_argument('--host', type=str, default='localhost', help='Host address for the server to do operations')
    args = parser.parse_args()
    # Validate args
    if args.operation in ['get', 'put']:
        if not args.key:
            parser.error(f"The '{args.operation}' operation requires a key argument.")
        if args.operation == 'put' and not args.value:
            parser.error("The 'put' operation requires a value argument.")
            
        # Check key and value format
        if not is_valid_key(args.key):
            exit(1)  # Exit if the key is invalid
        if args.operation == 'put' and not is_valid_value(args.value):
            exit(1)  # Exit if the value is invalid for PUT


    client = KV739Client(cache_size=args.cache_size, ttl=args.ttl, use_cache=args.use_cache, verbose=args.verbose)

    if args.config_file:
        status = client.kv739_init(args.config_file)
    else:
        logging.error("Config file is required.")
        exit(1)

    if status == 0:
        logging.info("Client initialized.")
        if args.operation == 'put':
            if args.value:
                client.kv739_put(args.key, args.value, args.timeout)
            else:
                logging.error("PUT operation requires both key and value.")
        elif args.operation == 'get':
            return_code, value = client.kv739_get(args.key, args.timeout, debug_port=args.debug_port)
            if args.verbose and return_code == 0:
                logging.info(f"Client retrieved {args.key}: {value}")
            elif return_code == 1:
                logging.info(f"Key '{args.key}' not found.")
            else:
                logging.error(f"GET operation failed for key '{args.key}'.")
                
        elif args.operation == 'die':
            if args.clean is not None:
                client.kv739_die(args.kill_type, args.clean, args.kill_ports, host=args.host)
            else:
                logging.error("DIE operation requires --clean argument (0 or 1).")
        elif args.operation == 'start':
            if args.new is not None:
                client.kv739_start(args.start_port, args.host, args.new)
            else:
                logging.error("Failed to start a new instance of the service. --new argument (0 or 1).")
        elif args.operation == 'leave':
            if args.clean is not None:
                client.kv739_leave(args.kill_type, args.clean, args.kill_ports, host=args.host)
            else:
                logging.error("Failed to remove the instance of the service. --clean argument (0 or 1).")

        client.kv739_shutdown()
