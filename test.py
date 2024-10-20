# test_script.py
import threading
import time
import random
import subprocess
import os
import psutil  # For CPU utilization
import logging
import json
from client_library import KV739Client

# Set up logging (if you still want to use it)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def start_master_and_replicas():
    """Starts the master and replica servers."""
    # Start the master server
    master_process = subprocess.Popen(["python3", "server.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(2)  # Wait for the master to start

    # Read the configuration to get replica ports
    with open('server_config.json', 'r') as f:
        config = json.load(f)
    replica_ports = config['child_ports']

    # Return the master process and replica ports for later use
    return master_process, replica_ports

def stop_master_and_replicas(master_process):
    """Stops the master and replica servers."""
    master_process.terminate()
    master_process.wait()
    print("Master and replicas terminated.")

def measure_throughput_latency(client, num_operations, workload_type='normal', replica_ports=None):
    """
    Measures throughput, latency, and CPU utilization under different workloads.
    workload_type: 'normal' or 'hot_cold'
    """
    keys = [f'key_{i}' for i in range(1000)]
    if workload_type == 'hot_cold':
        hot_keys = keys[:10]  # First 10 keys are hot
        cold_keys = keys[10:]
        key_distribution = hot_keys * 90 + cold_keys * 10  # 90% hot keys
    else:
        key_distribution = keys

    latencies = []
    cpu_usage_data = {}
    for port in replica_ports:
        cpu_usage_data[port] = []

    # Prepare CPU monitoring thread
    cpu_monitoring = threading.Event()
    cpu_thread = threading.Thread(target=monitor_cpu_usage, args=(replica_ports, cpu_usage_data, cpu_monitoring))
    cpu_thread.start()

    start_time = time.time()
    for _ in range(num_operations):
        key = random.choice(key_distribution)
        value = f'value_{random.randint(1, 1000)}'
        op_type = random.choice(['get', 'put'])

        op_start = time.time()
        if op_type == 'put':
            client.kv739_put(key, value)
        else:
            client.kv739_get(key)
        op_end = time.time()

        latencies.append(op_end - op_start)
    end_time = time.time()

    # Stop CPU monitoring
    cpu_monitoring.set()
    cpu_thread.join()

    throughput = num_operations / (end_time - start_time)
    average_latency = sum(latencies) / len(latencies)

    # Calculate average CPU usage per node
    average_cpu_per_node = {}
    for port in cpu_usage_data:
        if cpu_usage_data[port]:
            average_cpu_per_node[port] = sum(cpu_usage_data[port]) / len(cpu_usage_data[port])
        else:
            average_cpu_per_node[port] = 0.0

    return throughput, average_latency, average_cpu_per_node

def monitor_cpu_usage(replica_ports, cpu_usage_data, stop_event):
    """
    Monitors CPU utilization of the service instances during workload execution.
    """
    processes = {}
    for port in replica_ports:
        # Find the process running on the port
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if 'replica_server.py' in proc.info['cmdline'] and f'--port={port}' in proc.info['cmdline']:
                processes[port] = proc
                break

    while not stop_event.is_set():
        for port, proc in processes.items():
            if proc.is_running():
                cpu_percent = proc.cpu_percent(interval=0.1)
                cpu_usage_data[port].append(cpu_percent)
            else:
                cpu_usage_data[port].append(0.0)
        time.sleep(0.1)  # Sample every 0.1 seconds

def consistency_test(client):
    """
    Performs consistency tests to ensure the service provides consistent results.
    Adds debug information for each step.
    """
    test_key = 'consistency_key'
    initial_value = 'initial_value'
    updated_value = 'updated_value'
    
    print(f"Starting consistency test with key: '{test_key}'")

    # Step 1: Put the initial value
    print(f"PUT: Setting key '{test_key}' to '{initial_value}'")
    client.kv739_put(test_key, initial_value)

    # Step 2: Get and check the initial value
    print(f"GET: Retrieving key '{test_key}'")
    value = client.kv739_get(test_key)[1]
    print(f"GET Result: '{test_key}' = '{value}'")

    if value != initial_value:
        print(f"Consistency test failed: Expected '{initial_value}' but got '{value}'")
        return False
    else:
        print(f"Initial value matches: '{value}'")

    # Step 3: Update the value
    print(f"PUT: Updating key '{test_key}' to '{updated_value}'")
    client.kv739_put(test_key, updated_value)

    # Step 4: Get and check the updated value
    print(f"GET: Retrieving updated value for key '{test_key}'")
    value = client.kv739_get(test_key)[1]
    print(f"GET Result: '{test_key}' = '{value}'")

    if value != updated_value:
        print(f"Consistency test failed: Expected '{updated_value}' but got '{value}'")
        return False
    else:
        print(f"Updated value matches: '{value}'")

    print('Consistency test passed.')
    return True


def simulate_failures(client, replica_ports):
    """
    Simulates failures of different nodes.
    """
    # Simulate head failure
    print('Simulating head failure.')
    head_port = replica_ports[0]
    client.kv739_die('head', clean=1, server_ports=[head_port])
    time.sleep(2)  # Wait for the system to handle the failure

    # Test if the service is still available
    test_key = 'failure_test_key'
    client.kv739_put(test_key, 'value_after_head_failure')
    value = client.kv739_get(test_key)[1]
    if value != 'value_after_head_failure':
        print('Service unavailable after head failure.')
        return False

    # Simulate middle failure
    print('Simulating middle node failure.')
    if len(replica_ports) > 2:
        middle_port = replica_ports[1]
        client.kv739_die('middle', clean=1, server_ports=[middle_port])
        time.sleep(2)
        client.kv739_put(test_key, 'value_after_middle_failure')
        value = client.kv739_get(test_key)[1]
        if value != 'value_after_middle_failure':
            print('Service unavailable after middle node failure.')
            return False

    # Simulate tail failure
    print('Simulating tail failure.')
    tail_port = replica_ports[-1]
    client.kv739_die('tail', clean=1, server_ports=[tail_port])
    time.sleep(2)
    client.kv739_put(test_key, 'value_after_tail_failure')
    value = client.kv739_get(test_key)[1]
    if value != 'value_after_tail_failure':
        print('Service unavailable after tail failure.')
        return False

    print('Failure simulation tests passed.')
    return True

def availability_test(client, replica_ports):
    """
    Measures how many service instances need to be available for the service to be available.
    """
    total_instances = len(replica_ports)
    test_key = 'availability_key'
    client.kv739_put(test_key, 'initial_value')
    for i in range(total_instances):
        port_to_kill = replica_ports[i]
        print(f'Killing replica on port {port_to_kill}.')
        client.kv739_die('replica', clean=1, server_ports=[port_to_kill])
        time.sleep(2)

        # Test if the service is still available
        try:
            client.kv739_put(test_key, f'value_after_killing_{i+1}_instances')
            value = client.kv739_get(test_key)[1]
            if value != f'value_after_killing_{i+1}_instances':
                print(f'Service unavailable after killing {i+1} instances.')
                return i  # Return the number of instances required
        except Exception as e:
            print(f'Service unavailable after killing {i+1} instances. Exception: {e}')
            return i

    print('Service remained available after all instances were killed.')
    return total_instances

def main():
    # Start the master and replicas
    master_process, replica_ports = start_master_and_replicas()
    time.sleep(5)  # Wait for servers to be fully operational

    # Initialize the client
    client = KV739Client()
    client.kv739_init('server_config.json')

    # Throughput and latency measurements under normal workload
    print('Measuring throughput, latency, and CPU utilization under normal workload.')
    throughput_normal, latency_normal, cpu_normal = measure_throughput_latency(
        client, num_operations=1000, workload_type='normal', replica_ports=replica_ports)
    print(f'Normal workload - Throughput: {throughput_normal:.2f} ops/sec, Average Latency: {latency_normal:.4f} sec')
    print('Average CPU Utilization per Replica (Normal Workload):')
    for port, cpu_usage in cpu_normal.items():
        print(f'  Replica on port {port}: {cpu_usage:.2f}%')

    # Throughput and latency measurements under hot/cold workload
    print('Measuring throughput, latency, and CPU utilization under hot/cold workload.')
    throughput_hot_cold, latency_hot_cold, cpu_hot_cold = measure_throughput_latency(
        client, num_operations=1000, workload_type='hot_cold', replica_ports=replica_ports)
    print(f'Hot/Cold workload - Throughput: {throughput_hot_cold:.2f} ops/sec, Average Latency: {latency_hot_cold:.4f} sec')
    print('Average CPU Utilization per Replica (Hot/Cold Workload):')
    for port, cpu_usage in cpu_hot_cold.items():
        print(f'  Replica on port {port}: {cpu_usage:.2f}%')

    # Consistency tests
    print('Performing consistency tests.')
    consistency_passed = consistency_test(client)
    if not consistency_passed:
        print('Consistency tests failed.')

    # Simulate failures
    print('Simulating failures and testing service availability.')
    failures_handled = simulate_failures(client, replica_ports)
    if not failures_handled:
        print('Failure simulation tests failed.')

    # Availability tests
    print('Measuring minimum number of instances required for service availability.')
    min_instances_required = availability_test(client, replica_ports)
    print(f'Minimum instances required for service availability: {min_instances_required}')

    # Cleanup
    client.kv739_shutdown()
    stop_master_and_replicas(master_process)
    print('Test script completed.')

if __name__ == '__main__':
    main()
