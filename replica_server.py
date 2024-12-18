import grpc
from concurrent import futures
import kvstore_pb2_grpc
import kvstore_pb2
import logging
import argparse
import sqlite3
import os
import time
import threading
from typing import Iterable, Tuple
import socket
from functools import partial
from collections import defaultdict

# Set up logging to file
logging.basicConfig(
    filename='replica_server.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

DB_PATH = "./db_files/"
# Define SQLite-based storage backend
class KeyValueStore:
    def __init__(self,
                 server_port,
                 debug_mode=False,
                 crash_db=True
                 ):
        """
        Initialize the key-value store.
        Args:
            server_port: The port on which the server is running.
            debug_mode: Whether to print debug info.
            crash_db: Whether to clear the database(local file system) on failure.
        """
        
        self.db_file = os.path.join(DB_PATH, f"kvstore_{server_port}.db")
        self.port = server_port
        self.crash_db = crash_db
        
        try:
            self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
            self.conn.execute("PRAGMA journal_mode=WAL;")
            self.conn.execute("PRAGMA busy_timeout = 5000;")
            self.conn.execute('''CREATE TABLE IF NOT EXISTS kvstore
                                 (key TEXT PRIMARY KEY, value TEXT)''')
        except Exception as e:
            logging.error(f"Database error for server {self.port}: {e} accessing {self.db_file}")
            raise
        
        
    def get(self, key):
        try:
            cursor = self.conn.execute("SELECT value FROM kvstore WHERE key=?", (key,))
            result = cursor.fetchone()
            if result:
                return result[0], True
            # logging.info(f"Key '{key}' not found in server {self.port}.")
            return None, False
        except sqlite3.Error as e:
            logging.error(f"Error fetching key '{key}': {e}")
            return None, False

    def put(self, key, value):
        old_value, found = self.get(key)
        try:
            with self.conn:
                if found:
                    if value == old_value:
                        return old_value, found
                    self.conn.execute("UPDATE kvstore SET value=? WHERE key=?", (value, key))
                else:
                    self.conn.execute("INSERT INTO kvstore (key, value) VALUES (?, ?)", (key, value))
            # logging.info("Put operation successful for key: %s", key)
            return old_value, found
        except sqlite3.Error as e:
            logging.error(f"Error writing to database for key '{key}': {e}")
            return None, False

    def get_cursor(self):
        """Return a cursor to traverse the database."""
        return self.conn.cursor()
        
    def get_new_connection(self):
        return sqlite3.connect(self.db_file, check_same_thread=False)

    def crash(self):
        """
        Simulate the server crashing. 
        If hit by a missle, all db data is lost and use chain forwarding to recover.
        """
        if self.crash_db:
            logging.info(f"Server {self.port} hit by a missile. All data lost.")
            self.conn.close()
            os.remove(self.db_file)
        else:
            logging.info("Server crashed.")
            self.conn.close()
            
class KeyValueStoreServicer(kvstore_pb2_grpc.KVStoreServicer):
    """gRPC server for the key-value store."""

    def __init__(self,
                 store: KeyValueStore,
                 server: grpc.Server,
                 master_port,
                 heartbeat_gap=1,
                 prev_port=None,
                 next_port=None,
                 retries=3,
                 retry_interval=0.5,
                 notify_tail=False
                 ):
        """
        Initialize the key-value store servicer for gRPC comm.
        Args:
            store: The KeyValueStore object.
            server: The gRPC server object.
            master_port: The port of the master node.
            heartbeat_gap: The interval between heartbeats.
            prev_port: The port of the previous server in the chain.
            next_port: The port of the next server in the chain.
            retries: The number of retries for forwarding
            
        """
        self.port = store.port
        self.store = store
        self.server = server
        self.master_port = master_port
        self.heartbeat_gap = heartbeat_gap
        self.retries = retries
        self.retry_interval = retry_interval
        self.db_file = os.path.join(DB_PATH, f"kvstore_{self.port}.db")
        
        # Init comm along the chain and to the master
        self.master_stub = kvstore_pb2_grpc.MasterNodeStub(grpc.insecure_channel(f'localhost:{master_port}'))
        assert prev_port is not None or next_port is not None, "Must be either head, tail or middle node"
        self.prev_port = prev_port
        self.next_port = next_port
        self.fwd_failed_count = defaultdict(int)
        self.forward_fail_limit = 8
        
        self.is_tail = next_port is None
        self.is_head = prev_port is None
        self.next_stub = None
        self.updating_tail = False
        if next_port:
            self.next_stub = kvstore_pb2_grpc.KVStoreStub(grpc.insecure_channel(f'localhost:{next_port}'))
        
        if notify_tail:
            self.notify_tail()
        # Start heartbeat thread
        self.stop_heartbeat = threading.Event()
        self.heartbeat_thread = threading.Thread(target=self.send_heartbeat)
        self.heartbeat_thread.start()
        
    def notify_tail(self):
        prev_stub = kvstore_pb2_grpc.KVStoreStub(grpc.insecure_channel(f'localhost:{self.prev_port}'))  
        try:
            prev_stub.TransferTail(kvstore_pb2.TransferTailRequest(new_tail_port=self.port))
            logging.info(f"Tail server {self.port} notified temp tail {self.prev_port} that it's up.")
        except grpc.RpcError as e:
            logging.error(f"New tail on port {self.port} fail to notify old tail {self.prev_port}  {e}")

    def TransferTail(self, request, context, retries=3):
        """Request the current tail to transfer to new replacement tail."""
        if not self.is_tail:
            logging.info(f"Server {self.port} is not the tail. Rejecting update tail request.")
            return kvstore_pb2.TransferTailResponse(success=False)
        
        if request.new_tail_port is None:
            logging.info(f"Server {self.port} got invalid new tail port None in TransferTail.")
            return kvstore_pb2.TransferTailResponse(success=False)
        
        self.next_port = request.new_tail_port 
        try:
            self.next_stub = kvstore_pb2_grpc.KVStoreStub(grpc.insecure_channel(f'localhost:{self.next_port}'))
            # Spawn another thread to forward all KV pairs to the new tail.
            # NOTE: seems two-way connection inside one RPC call causes deadlock.
            # i.e. you can't use launch another RPC the calls back the caller before TransferTail returns.
            # so we must use a callback. 
            context.add_callback(threading.Thread(target=self.ForwardAll,).start)
        
            logging.info(f"Server {self.port} committed data to new tail {self.next_port}.")
            return kvstore_pb2.TransferTailResponse(success=True)
        except Exception as e:
            if retries > 0:
                logging.info(f"Server {self.port} error in updating tail. Retrying...")
                time.sleep(self.retry_interval)
                return self.TransferTail(request, context, retries - 1)
            
            logging.error(f"Server {self.port} error in updating tail: {e}")
            return kvstore_pb2.TransferTailResponse(success=False)    

    def PromoteToHead(self, request, context):
        self.prev_port = None
        self.is_head = True
        logging.info(f"Server {self.port} acknowledged its new head status.")
        return kvstore_pb2.PromoteToHeadResponse(success=True)


    def send_heartbeat(self, is_alive=True):
        """Send heartbeat to master to signal that the server is alive."""
        try:
            # Send at least once
            self.master_stub.SendHeartBeat(kvstore_pb2.SendHeartBeatRequest(is_alive=is_alive, port=self.port))
            time.sleep(self.heartbeat_gap)  
            while not self.stop_heartbeat.is_set():
                self.master_stub.SendHeartBeat(kvstore_pb2.SendHeartBeatRequest(is_alive=is_alive, port=self.port))
                time.sleep(self.heartbeat_gap) 
            
        except Exception as e:
            logging.error(f"Error in sending heartbeat heartbeat on port {self.port}: {e}")
            

    def Get(self, request, context):
        """Handle 'Get' requests."""
        # Not tail, reject req and ask client to go to master for new tail.
        if not self.is_tail:
            logging.info(f"Server on port {self.port} is not the tail. Rejecting Get request.")
            return kvstore_pb2.GetResponse(success=True, rejected=True)
        
        try:
            value, return_code = self.store.get(request.key)
            if return_code:
                logging.info(f"Server {self.port} get request for key: {request.key} - Found value: {value}")
                return kvstore_pb2.GetResponse(value=value, success=True, found=True)
            else:
                logging.info(f"Server {self.port} get request for key: {request.key} - Not found.")
                return kvstore_pb2.GetResponse(success=True, found=False)
            
        except sqlite3.Error as e:
            logging.error(f"Server {self.port} error processing Get request for key {request.key}: {e}")
            return kvstore_pb2.GetResponse(success=False, found=False)
        

    def Put(self, request, context):
        """Handle 'Put' requests."""
        # Not head, reject req and ask client to go to master for new head.
        if not self.is_head and not request.is_forward:
            logging.info(f"Server on port {self.port} is not the head. Rejecting Put request.")
            return kvstore_pb2.PutResponse(success=True, rejected=True)
        
        try:
            # Perform the Put operation
            key, value = request.key, request.value
            old_value, old_value_found = self.store.put(key, value)
            if self.is_tail:
                logging.info(f"Tail server {self.port} committed {key}:{value} locally. No need to forward.")
            else:
                # Forward to next in chain. NOTE: Do NOT wait until tail replies. 
                context.add_callback(partial(self.ForwardToNext, key, value))
                # self.ForwardToNext(key, value)
            
            # Construct the response
            response = kvstore_pb2.PutResponse(
                old_value=old_value if old_value_found else '',
                old_value_found=old_value_found,
                success=True,
                version=0  # Use an appropriate version number if applicable
            )
            return response

        except sqlite3.Error as e:
            logging.error(f"Server {self.port}  error processing Put request for key {key}: {e}")
            return kvstore_pb2.PutResponse(success=False)
        except grpc.RpcError as e:
            logging.error(f"Server {self.port}  error forwarding Put request for key {key}: {e}")
            return kvstore_pb2.PutResponse(success=False)


    def ForwardToNext(self, key, value, to_new_tail=False):
        """Forward key-value pairs to the next node in the chain."""
        if (not self.is_tail and self.next_stub is not None) or to_new_tail:
            for i in range(self.retries):
                try:
                    response = self.next_stub.Put(kvstore_pb2.PutRequest(key=key, value=value, is_forward=True))
                    if response.success:
                        logging.info(f"Server {self.port} forwarded KV pair '{key}:{value}' to next node {self.next_port} in chain.")
                        break
                    
                except grpc.RpcError as e:
                    self.fwd_failed_count[self.next_port] += 1
                    if self.fwd_failed_count[self.next_port] > self.forward_fail_limit:
                        logging.error(f"Server {self.port} failed to forward to {self.next_port} more than {self.forward_fail_limit} times. Asking master to replace it.")
                        replace = True
                        self.fwd_failed_count[self.next_port] = 0 # replace next node and reset 
                    else:
                        logging.error(f"Error forwarding key '{key}' to next node {self.next_port}: {e}. Remaining retries: {self.retries - i}")
                        time.sleep(self.retry_interval)
                        replace = False
                    
                    if not to_new_tail:
                        response = self.master_stub.GetNextInChain(kvstore_pb2.GetNextInChainRequest(port=self.port, hostname=socket.gethostname(), replace=replace))
                        if response.you_are_tail:
                            self.is_tail = True
                            self.next_port = None
                            self.next_stub = None
                            logging.info(f"Server {self.port} notified by master that it's the tail via GetNextInChain.")
                        else:
                            logging.info(f"Server {self.port} updated next node in chain to {response.port}.")
                            self.next_port = response.port
                            hostname = response.hostname
                            self.next_stub = kvstore_pb2_grpc.KVStoreStub(grpc.insecure_channel(f'localhost:{self.next_port}'))
                    else:
                        logging.error(f"ForwardToNext: temp tail {self.port} failed to forward to new tail {self.next_port}. Remaining retries: {self.retries - i}")
            
    def ForwardAll(self,):
        """
        Forward all key-value pairs to the new tail node in the chain.
        Upon completion, relinquish the tail status.
        """
        try:
            if not self.next_stub:
                logging.info(f"Server {self.port} next stub not initialized in ForwardAll.")
                return
            conn = self.store.get_new_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM kvstore")
            rows = cursor.fetchall()
            # Check if rows is empty
            if rows:
                logging.info(f"Server {self.port} forwarding all data to node {self.next_port}.")
                for key, value in rows:
                    if not self.next_stub:
                        logging.info(f"Server {self.port} next stub not initialized in ForwardAll.")
                        return
                    self.ForwardToNext(key, value, to_new_tail=True)
        
        except Exception as e:
            logging.error(f"Error in ForwardAll on server {self.port} to node {self.next_port}: {e}. Data can be lost.")
        finally:
            # Relinquish tail status
            self.is_tail = False 
            logging.info(f"Server {self.port} telling master that it's transferred tail status to node {self.next_port}.")
            self.master_stub.TransferTailDone(kvstore_pb2.TailUpdated(new_tail_port=self.next_port))
        
    def stop_server(self, ):
        """Schedule the server to stop after a short delay to allow responding to client."""
        self.server.stop(0)  # Graceful shutdown
        self.server.wait_for_termination()
        self.store.crash()
        logging.info(f"Server {self.port} shut down successfully.")
    
    def Die(self, request, context):
        """Terminate the server to simulate failure."""
        self.stop_heartbeat.set()  # Stops the heartbeat thread
        clean = request.clean

        if clean:
            logging.info(f"Server on port {self.port} crashed by clean kill. Notifying master.")  
            self.send_heartbeat(is_alive=False)
        else:
            logging.info(f"Server on port {self.port} crashed by non-clean kill.")

        # Prepare the response
        response = kvstore_pb2.DieResponse(success=True)
        # Send the response before shutting down
        context.set_code(grpc.StatusCode.OK)
        context.set_details("Server is shutting down.")
        if clean:
            context.add_callback(self.stop_server)

        return response
    
    def stop_server(self, ):
        """Schedule the server to stop after a short delay to allow responding to client."""
        self.server.stop(0)  # Graceful shutdown
        self.server.wait_for_termination()
        self.store.crash()
        logging.info(f"Server {self.port} shut down successfully.")
    
    def Leave(self, request, context):
        """Terminate the server to simulate failure."""
        self.stop_heartbeat.set()  # Stops the heartbeat thread
        clean = request.clean

        if clean:
            logging.info(f"Server on port {self.port} crashed by clean kill. Notifying master.")  
            self.send_heartbeat(is_alive=False)
        else:
            logging.info(f"Server on port {self.port} crashed by non-clean kill.")

        # Prepare the response
        response = kvstore_pb2.LeaveResponse(success=True)
        # Send the response before shutting down
        context.set_code(grpc.StatusCode.OK)
        context.set_details("Server is shutting down.")
        if clean:
            context.add_callback(self.stop_server)

        return response


def serve(args):
    """Run the gRPC server."""
    port, master_port = args.port, args.master_port,
    
    store = KeyValueStore(port, crash_db=args.crash_db)
    server = grpc.server(futures.ThreadPoolExecutor())
    servicer = KeyValueStoreServicer(store,
                                    server,
                                    master_port,
                                    args.heartbeat_gap,
                                    args.prev_port,
                                    args.next_port,
                                    notify_tail=args.notify_tail
                                    )
    kvstore_pb2_grpc.add_KVStoreServicer_to_server(servicer, server)

    server.add_insecure_port(f'[::]:{port}') # ipv6
    server.add_insecure_port(f'0.0.0.0:{port}') # ipv4
    server.start()
    if servicer.is_tail:
        logging.info(f"Tail node started on port {port}. prev_port: {servicer.prev_port}")
    elif servicer.is_head:
        logging.info(f"Head node started on port {port}. next_port: {servicer.next_port}")
    else:
        logging.info(f"Server started on port {port}." +
            f"next_port: {servicer.next_port}, prev_port: {servicer.prev_port}.")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(0)
        logging.info(f"Server on port {port} shutting down.")
        servicer.stop_heartbeat.set()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Start a replica server.')
    parser.add_argument('--port', type=int, required=True, help='Port to run the server on.')
    parser.add_argument('-m', '--master_port', type=int, required=True, help='Master node port.')
    parser.add_argument("--prev_port", type=int, default=None, help='Port of the previous server in the chain (if any).')
    parser.add_argument('--next_port', type=int, default=None,
                        help='Child port of the next server in the chain (if any).')
    parser.add_argument('-i', "--heartbeat_gap", type=int, default=1, help='Heartbeat interval in seconds.')
    parser.add_argument("--crash_db", type=eval, default=True,
                        help="Whether to crash the database in failure simulation, which requires tail data forwarding to recover.")
    parser.add_argument("--notify_tail", action='store_true', help="Notify master of a running new tail")
    parser.add_argument("--verbose", type=eval, default=True, help="Whether to print debug info.")
    args = parser.parse_args()
    if not args.verbose:
        logging.disable(logging.INFO)

    # Ensure the DB directory exists
    os.makedirs(DB_PATH, exist_ok=True)

    # Start the server with the provided arguments
    serve(args)
