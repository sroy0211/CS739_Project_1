import multiprocessing
import time
import argparse
from client_library import KV739Client

NUM_CLIENTS = 10  # Number of concurrent clients to simulate
NUM_OPERATIONS = 20  # Number of operations per client

# Flags to keep track of test results
test_results = {
    "Correctness Test": False,
    "Reliability Test": False,
    "Performance Test": False,
    "Overall Test": False,
}

def run_put_test(client_id, server_address):
    """Function to perform put operations for testing."""
    client = KV739Client()
    client.kv739_init(server_address)

    for i in range(NUM_OPERATIONS):
        key = f"key_{client_id}_{i}"
        value = f"value_{client_id}_{i}"
        status, old_value = client.kv739_put(key, value)
        print(f"[Client {client_id}] PUT {key} -> {value}, Status: {status}, Old Value: {old_value}")

    client.kv739_shutdown()

def run_get_test(client_id, server_address):
    """Function to perform get operations for testing."""
    client = KV739Client()
    client.kv739_init(server_address)

    for i in range(NUM_OPERATIONS):
        key = f"key_{client_id}_{i}"
        status, value = client.kv739_get(key, 5)  # Timeout of 5 seconds
        print(f"[Client {client_id}] GET {key} -> {value}, Status: {status}")

    client.kv739_shutdown()

def correctness_test(server_address):
    """Test to ensure correct store and retrieve operations."""
    try:
        client = KV739Client()
        client.kv739_init(server_address)

        key = "correctness_key"
        value = "correctness_value"
        client.kv739_put(key, value)
        status, retrieved_value = client.kv739_get(key, 5)

        assert status == 0 and retrieved_value == value, "[Correctness Test] Failed!"
        print("[Correctness Test] Passed!")
        test_results["Correctness Test"] = True

        client.kv739_shutdown()
    except Exception as e:
        print(f"[Correctness Test] Failed with error: {e}")

def reliability_test(server_address):
    """Test the server's durability and recovery after crashes."""
    try:
        client = KV739Client()
        client.kv739_init(server_address)

        key = "reliability_key"
        value = "reliability_value"
        client.kv739_put(key, value)

        print("[Reliability Test] Simulate server crash: manually restart the server now.")
        input("Press Enter after restarting the server...")

        status, retrieved_value = client.kv739_get(key, 5)
        assert status == 0 and retrieved_value == value, "[Reliability Test] Failed!"

        print("[Reliability Test] Passed!")
        test_results["Reliability Test"] = True
        client.kv739_shutdown()
    except Exception as e:
        print(f"[Reliability Test] Failed with error: {e}")

def performance_test(server_address):
    """Measure latency and throughput with multiple clients."""
    try:
        start_time = time.time()

        processes = []
        for i in range(NUM_CLIENTS):
            p = multiprocessing.Process(target=run_put_test, args=(i, server_address))
            processes.append(p)
            p.start()

        for p in processes:
            p.join()

        end_time = time.time()
        total_time = end_time - start_time
        total_operations = NUM_CLIENTS * NUM_OPERATIONS
        throughput = total_operations / total_time if total_time > 0 else 0

        print(f"[Performance Test] {NUM_CLIENTS} clients with {NUM_OPERATIONS} operations each.")
        print(f"[Performance Test] Total time: {total_time:.2f} seconds")
        print(f"[Performance Test] Throughput: {throughput:.2f} ops/sec")

        test_results["Performance Test"] = True
    except Exception as e:
        print(f"[Performance Test] Failed with error: {e}")

def run_multiple_clients_test(server_address):
    """Run correctness, reliability, and performance tests under multiple clients."""
    print("\n--- Running Multiple Clients Test ---")

    try:
        # Run multiple clients performing PUT operations
        processes = []
        for i in range(NUM_CLIENTS):
            p = multiprocessing.Process(target=run_put_test, args=(i, server_address))
            processes.append(p)
            p.start()

        for p in processes:
            p.join()

        # Run correctness test under multiple client scenario
        print("\n--- Correctness Test ---")
        correctness_test(server_address)

        # Run reliability test under multiple client scenario
        print("\n--- Reliability Test ---")
        reliability_test(server_address)

        # Run performance test under multiple client scenario
        print("\n--- Performance Test ---")
        performance_test(server_address)

        # Run multiple clients performing GET operations
        processes = []
        for i in range(NUM_CLIENTS):
            p = multiprocessing.Process(target=run_get_test, args=(i, server_address))
            processes.append(p)
            p.start()

        for p in processes:
            p.join()

        test_results["Overall Test"] = True
        print("Test completed.")
    except Exception as e:
        print(f"Test failed with error: {e}")

def print_summary():
    """Prints the summary of all test results."""
    print("\n--- Test Summary ---")
    for test, result in test_results.items():
        status = "PASSED" if result else "FAILED"
        print(f"{test}: {status}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the key-value store service.")
    parser.add_argument('--server', required=True, help='Server address in the format host:port')
    args = parser.parse_args()
    server_address = args.server

    # Run all tests under multiple clients
    run_multiple_clients_test(server_address)

    # Print the summary of test results
    print_summary()
