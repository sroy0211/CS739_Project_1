# CS739_Project_1

This project implements a durable key-value store with client and server components, providing PUT and GET operations with durability guarantees. The system is designed to handle multiple clients, ensure data persistence across crashes, and optimize performance with client-side caching.

## Environment Setup

1. **Create a Python Virtual Environment:**
python3 -m venv venv
source venv/bin/activate

2. **Install Required Packages:**
pip install grpcio==1.66.1 protobuf==5.28.2 setuptools==59.6.0


## Running the Server

To start the key-value store server, run the following command in the terminal:
python3 server.py

## Running the Client

The client supports both `PUT` and `GET` operations. To interact with the server, use the following commands:

### PUT Operation

 
```bash python3 client.py put <key> <value> --server <server_address:50051> --timeout <timeout> --use_cache```


### GET Operation

```bash python3 client.py get <key> --server <server_address:50051> --timeout <timeout> --use_cache ```

## Testing the System

### Correctness Tests

To run correctness tests with multiple clients, use:

```bash python3 test.py --test_type correctness --num_clients <number_of_clients> --num_iterations <iterations_per_client> ```

### Reliability Tests

To run reliability tests simulating server crashes:

```bash python3 test.py --test_type reliability --num_clients <number_of_clients> --simulate_crash ```

### Performance Tests
To run performance tests with a hot/cold workload(use client-side cache):

```bash python3 test.py --test_type performance --duration <test_duration> --num_clients <number_of_clients> --use_cache```

### Please refer to code for details command use.... 

