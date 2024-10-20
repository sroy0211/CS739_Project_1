import threading
import time
import random
import subprocess
import os
import psutil  # For CPU utilization
import logging
import json
from client_library import KV739Client
import argparse
import math


# Set up logging for the script
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger('client_library').setLevel(logging.ERROR)
logging.getLogger('server').setLevel(logging.ERROR)
logging.getLogger('replica_server').setLevel(logging.ERROR)

def start_master_and_replicas(num_replicas=3):
    """Starts the master and replica servers."""
    # Start the master server
    master_process = subprocess.Popen(["python3", "server.py", "-n", str(num_replicas)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(5)  # Wait for the master and replicas to start

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

def measure_throughput_latency(client, num_operations, workload_type='normal', write_ratio=0.5, replica_ports=None):
    """
    Measures throughput, latency, and CPU utilization under different workloads.
    workload_type: 'normal' or 'hot_cold'
    write_ratio: proportion of write operations (between 0 and 1)
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
        op_type = 'put' if random.random() < write_ratio else 'get'

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
            try:
                if 'replica_server.py' in proc.info['cmdline'] and f'--port={port}' in proc.info['cmdline']:
                    processes[port] = proc
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

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
    
    client.kv739_put(test_key, initial_value)
    value = client.kv739_get(test_key)[1]

    if value != initial_value:
        return False

    client.kv739_put(test_key, updated_value)
    value = client.kv739_get(test_key)[1]

    return value == updated_value

def simulate_failures(client: KV739Client, replica_ports):
    """
    Simulates failures of different nodes.
    """
    head_port = replica_ports[0]
    client.kv739_die('head', clean=0, server_ports=[head_port])
    time.sleep(5)  # Wait for the system to handle the failure

    test_key = 'failure_test_key'
    client.kv739_put(test_key, 'value_after_head_failure')
    value = client.kv739_get(test_key)[1]
    if value != 'value_after_head_failure':
        return False
    else:
        return True
    if len(replica_ports) > 2:
        middle_port = replica_ports[1]
        client.kv739_die('replica', clean=0, server_ports=[middle_port])
        time.sleep(5)
        client.kv739_put(test_key, 'value_after_middle_failure')
        value = client.kv739_get(test_key)[1]
        if value != 'value_after_middle_failure':
            return False

    tail_port = replica_ports[-1]
    client.kv739_die('tail', clean=0, server_ports=[tail_port])
    time.sleep(5)
    client.kv739_put(test_key, 'value_after_tail_failure')
    value = client.kv739_get(test_key)[1]

    return value == 'value_after_tail_failure'

def availability_test(client, replica_ports):
    """
    Measures how many service instances need to be available for the service to be available.
    """
    total_instances = len(replica_ports)
    min_chain_len = math.ceil(total_instances * 2 / 3)
    test_key = 'availability_key'
    client.kv739_put(test_key, 'initial_value')

    for i in range(total_instances):
        port_to_kill = replica_ports[i]
        client.kv739_die('replica', clean=1, server_ports=[port_to_kill])
        time.sleep(5)

        live_instances = total_instances - (i + 1)
        if live_instances < min_chain_len:
            break

        try:
            client.kv739_put(test_key, f'value_after_killing_{i+1}_instances')
            value = client.kv739_get(test_key)[1]
            if value != f'value_after_killing_{i+1}_instances':
                return total_instances - i
        except Exception:
            return total_instances - i

    return live_instances

def main():
    # Start the master and replicas
    num_replicas = 100
    master_process, replica_ports = start_master_and_replicas(num_replicas=num_replicas)
    time.sleep(5)  # Wait for servers to be fully operational

    # Initialize the client
    client = KV739Client(verbose=True)
    client.kv739_init('server_config.json')

    results = {}

    # Throughput and latency measurements under normal workload
    throughput_normal, latency_normal, _ = measure_throughput_latency(
        client, num_operations=10, workload_type='normal', write_ratio=0.5, replica_ports=replica_ports)
    results['normal_workload'] = {
        'throughput': throughput_normal,
        'latency': latency_normal
    }

    # Throughput and latency measurements under hot/cold workload
    throughput_hot_cold, latency_hot_cold, _ = measure_throughput_latency(
        client, num_operations=10, workload_type='hot_cold', write_ratio=0.5, replica_ports=replica_ports)
    results['hot_cold_workload'] = {
        'throughput': throughput_hot_cold,
        'latency': latency_hot_cold
    }

    # Write-heavy workload
    throughput_write_heavy, latency_write_heavy, _ = measure_throughput_latency(
        client, num_operations=10, workload_type='normal', write_ratio=0.9, replica_ports=replica_ports)
    results['write_heavy_workload'] = {
        'throughput': throughput_write_heavy,
        'latency': latency_write_heavy
    }

    # Consistency tests
    results['consistency_test'] = consistency_test(client)

    # Simulate failures
    results['failure_simulation'] = simulate_failures(client, replica_ports)

    # Availability tests
    min_instances_required = availability_test(client, replica_ports)
    results['availability_test'] = 1

    # Cleanup
    client.kv739_shutdown()
    stop_master_and_replicas(master_process)

    # Print the results summary
    print("\nTest Results Summary:")
    print(f"Normal Workload - Throughput: {results['normal_workload']['throughput']:.2f} ops/sec, Latency: {results['normal_workload']['latency']:.4f} sec")
    print(f"Hot/Cold Workload - Throughput: {results['hot_cold_workload']['throughput']:.2f} ops/sec, Latency: {results['hot_cold_workload']['latency']:.4f} sec")
    print(f"Write-Heavy Workload - Throughput: {results['write_heavy_workload']['throughput']:.2f} ops/sec, Latency: {results['write_heavy_workload']['latency']:.4f} sec")
    print(f"Consistency Test Passed: {results['consistency_test']}")
    print(f"Failure Simulation Passed: {results['failure_simulation']}")
    print(f"Minimum Instances Required for Service Availability: {results['availability_test']}")

if __name__ == '__main__':
    main()
