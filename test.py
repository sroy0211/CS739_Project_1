import argparse
import logging
import time
import random
from client_library import KV739Client  # Adjust this import based on your actual client library file name
import multiprocessing

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_correctness_tests(args):
    logging.info("Starting correctness tests with multiple clients.")

    num_clients = args.num_clients
    num_iterations = args.num_iterations  # Number of operations each client will perform
    keys = ['correctness_test_key_{}'.format(i) for i in range(num_iterations)]
    value = 'correctness_test_value'

    manager = multiprocessing.Manager()
    failure_flag = manager.Value('i', 0)  # Shared flag to indicate if any client encounters a failure

    def client_worker(client_id):
        client = KV739Client(cache_size=args.cache_size, ttl=args.ttl, use_cache=args.use_cache)
        if client.kv739_init(args.server) != 0:
            logging.error('Client %d: Failed to initialize.', client_id)
            failure_flag.value = 1
            return

        for i in range(num_iterations):
            key = keys[i]
            status, old_value = client.kv739_put(key, value)
            if status not in [0, 1]:
                logging.error('Client %d: PUT operation failed.', client_id)
                failure_flag.value = 1
                break

            status, returned_value = client.kv739_get(key, args.timeout)
            if status == 0:
                if returned_value != value:
                    logging.error('Client %d: GET operation returned incorrect value.', client_id)
                    failure_flag.value = 1
                    break
            else:
                logging.error('Client %d: GET operation failed with status %d.', client_id, status)
                failure_flag.value = 1
                break

        if client.kv739_shutdown() != 0:
            logging.error('Client %d: Failed to shutdown.', client_id)
            failure_flag.value = 1

    # Start client processes
    processes = []
    for client_id in range(num_clients):
        p = multiprocessing.Process(target=client_worker, args=(client_id,))
        processes.append(p)
        p.start()

    # Wait for all clients to finish
    for p in processes:
        p.join()

    if failure_flag.value == 0:
        logging.info("Correctness tests completed successfully.")
    else:
        logging.error("Correctness tests failed.")

def run_reliability_tests(args):
    logging.info("Starting reliability tests with multiple clients.")

    num_clients = args.num_clients
    key = 'reliability_test_key'
    value = 'reliability_test_value'
    manager = multiprocessing.Manager()
    failure_flag = manager.Value('i', 0)  # Shared flag to indicate if any client encounters a failure
    pause_event = manager.Event()  # Event to pause clients during the server restart

    def client_worker(client_id, pause_event):
        client = KV739Client(cache_size=args.cache_size, ttl=args.ttl, use_cache=args.use_cache)
        if client.kv739_init(args.server) != 0:
            logging.error('Client %d: Failed to initialize.', client_id)
            failure_flag.value = 1
            return

        # Each client performs a put operation
        status, _ = client.kv739_put(key, value)
        if status not in [0, 1]:
            logging.error('Client %d: PUT operation failed.', client_id)
            failure_flag.value = 1
            return

        # Wait for the main process to signal that the server has been restarted
        pause_event.wait()

        # Get the value after server restart
        status, returned_value = client.kv739_get(key, args.timeout)
        if status == 0:
            if returned_value != value:
                logging.error('Client %d: GET operation after server restart returned incorrect value.', client_id)
                failure_flag.value = 1
        else:
            logging.error('Client %d: GET operation after server restart failed with status %d.', client_id, status)
            failure_flag.value = 1

        if client.kv739_shutdown() != 0:
            logging.error('Client %d: Failed to shutdown.', client_id)
            failure_flag.value = 1

    # Start client processes
    processes = []
    for client_id in range(num_clients):
        p = multiprocessing.Process(target=client_worker, args=(client_id, pause_event))
        processes.append(p)
        p.start()

    # Simulate server crash in the main process
    if args.simulate_crash:
        logging.info('Simulating server crash. Please stop the server now.')
        input('Press Enter after the server has been stopped...')
        logging.info('Restart the server now.')
        input('Press Enter after the server has been restarted...')

    # Signal child processes to continue after server restart
    pause_event.set()

    # Wait for all clients to finish
    for p in processes:
        p.join()

    if failure_flag.value == 0:
        logging.info("Reliability tests completed successfully.")
    else:
        logging.error("Reliability tests failed.")

def run_performance_tests(args):
    logging.info("Starting performance tests with modified 'hot_cold' workload to increase cache hits.")

    num_clients = args.num_clients
    duration = args.duration
    num_keys = args.num_keys
    key_length = args.key_length
    value_length = args.value_length

    # Generate keys and values
    keys = ['key' + str(i).zfill(key_length - 3) for i in range(num_keys)]
    values = ['value' + str(i).zfill(value_length - 5) for i in range(num_keys)]

    # Modify 'hot_cold' workload to increase cache hits
    hot_ratio = args.hot_ratio  # Fraction of hot keys
    hot_fraction = args.hot_fraction  # Fraction of accesses to hot keys

    # Increase hot_fraction to favor hot keys more
    hot_fraction = min(hot_fraction, 1.0)  # Ensure it stays within valid bounds
    args.hot_fraction = hot_fraction  # Update in args for consistency

    num_hot_keys = max(1, int(num_keys * hot_ratio))
    hot_keys = keys[:num_hot_keys]
    cold_keys = keys[num_hot_keys:]

    # Assign higher weights to hot keys to increase cache hits
    key_weights = []
    for key in keys:
        if key in hot_keys:
            key_weights.append(hot_fraction / num_hot_keys)
        else:
            key_weights.append((1 - hot_fraction) / max(1, num_keys - num_hot_keys))

    # Shared variables for processes
    manager = multiprocessing.Manager()
    total_operations = manager.Value('i', 0)
    total_latency = manager.Value('d', 0.0)
    latency_lock = manager.Lock()

    # Since processes do not share memory, we need to share keys, values, and weights
    shared_keys = manager.list(keys)
    shared_values = manager.list(values)
    shared_key_weights = manager.list(key_weights)
    shared_hot_keys = manager.list(hot_keys)

    def worker(process_id):
        # Each process needs its own client instance
        thread_client = KV739Client(cache_size=args.cache_size, ttl=args.ttl, use_cache=args.use_cache)
        init_status = thread_client.kv739_init(args.server)
        if init_status != 0:
            logging.error('Process %d: Failed to initialize client.', process_id)
            return

        end_time = time.time() + duration
        random.seed(process_id)  # Seed random number generator for each process

        while time.time() < end_time:
            # Favor 'get' operations to utilize cache
            operation = random.choices(['get', 'put'], weights=[0.8, 0.2], k=1)[0]

            key = random.choices(shared_keys, weights=shared_key_weights, k=1)[0]
            value = random.choice(shared_values)

            start_time = time.time()
            if operation == 'put':
                status, _ = thread_client.kv739_put(key, value)
            else:
                status, _ = thread_client.kv739_get(key, args.timeout)
            latency = time.time() - start_time

            if status == -1:
                logging.error('Process %d: Operation failed.', process_id)
                continue

            with latency_lock:
                total_operations.value += 1
                total_latency.value += latency
        shutdown_status = thread_client.kv739_shutdown()
        if shutdown_status != 0:
            logging.error('Process %d: Failed to shutdown client.', process_id)

    # Start client processes
    processes = []
    start_time = time.time()
    for i in range(num_clients):
        p = multiprocessing.Process(target=worker, args=(i,))
        processes.append(p)
        p.start()
    # Wait for processes to finish
    for p in processes:
        p.join()
    total_time = time.time() - start_time

    # Compute and print results
    avg_latency = total_latency.value / total_operations.value if total_operations.value > 0 else 0
    throughput = total_operations.value / total_time if total_time > 0 else 0
    logging.info('Total operations: %d', total_operations.value)
    logging.info('Total time: %.2f seconds', total_time)
    logging.info('Throughput: %.2f operations per second', throughput)
    logging.info('Average latency: %.6f seconds', avg_latency)
    logging.info("Performance tests completed.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='KVStore Test Suite')
    parser.add_argument('--server', default='localhost:50051', help='Server address (default: localhost:50051)')
    parser.add_argument('--test_type', choices=['correctness', 'reliability', 'performance'], required=True, help='Type of test to run')
    parser.add_argument('--duration', type=int, default=60, help='Duration of the test in seconds (default: 60)')
    parser.add_argument('--num_clients', type=int, default=4, help='Number of client processes (default: 4)')
    parser.add_argument('--num_keys', type=int, default=100, help='Number of keys to use (default: 100)')
    parser.add_argument('--key_length', type=int, default=10, help='Length of keys (default: 10)')
    parser.add_argument('--value_length', type=int, default=100, help='Length of values (default: 100)')
    parser.add_argument('--workload', choices=['uniform', 'hot_cold'], default='hot_cold', help='Type of workload distribution (default: hot_cold)')
    parser.add_argument('--hot_ratio', type=float, default=0.1, help='Ratio of hot keys in hot_cold workload (default: 0.1)')
    parser.add_argument('--hot_fraction', type=float, default=0.9, help='Fraction of requests to hot keys in hot_cold workload (default: 0.9)')
    parser.add_argument('--num_iterations', type=int, default=10, help='Number of iterations per client in correctness tests (default: 10)')
    parser.add_argument('--simulate_crash', action='store_true', help='Simulate server crashes (for reliability tests)')
    parser.add_argument('--cache_size', type=int, default=500, help='Cache size for the client (default: 500)')
    parser.add_argument('--ttl', type=float, default=5, help='TTL for the client cache in seconds (default: 5)')
    parser.add_argument('--timeout', type=int, default=5, help='Timeout for GET operations (default: 5 seconds)')
    parser.add_argument('--use_cache', action='store_true', help='Enable client-side cache')
    parser.add_argument('--log_level', default='INFO', help='Logging level (default: INFO)')

    args = parser.parse_args()

    logging.getLogger().setLevel(args.log_level.upper())

    if args.test_type == 'correctness':
        run_correctness_tests(args)
    elif args.test_type == 'reliability':
        run_reliability_tests(args)
    elif args.test_type == 'performance':
        run_performance_tests(args)
    else:
        logging.error('Unknown test type.')
