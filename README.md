# CS739_Project_3 : Variable Membership KV Store

This project implements a durable key-value store with client and server components, providing PUT and GET operations with durability guarantees. The system supports multiple clients, ensures data persistence across crashes, and uses a chain replication approach to handle node failures efficiently.

## Environment Setup

1. **Create a Python Virtual Environment:**
python3 -m venv venv
source venv/bin/activate

2. **Install Required Packages:**
pip install grpcio==1.66.1 protobuf==5.28.2 setuptools==59.6.0 psutil==5.9.0


## Running the Server

To start the key-value store server, run the following command in the terminal:
python3 server.py &

## Running the Client

The client supports both `PUT` and `GET` operations. To interact with the server, use the following commands:

### PUT Operation

 
```bash
python3 client.py put <key> <value> --server <server_address:50051> --timeout <timeout> 
```


### GET Operation

```bash 
python3 client.py get <key> --server <server_address:50051> --timeout <timeout>
```
### Server Failure Simulation
The client also supports simulating server failures (clean or unclean shutdown). Use the following command to terminate a server:

```bash
python3 client.py die <server_type> --clean <0_or_1> --kill_ports <port_numbers>
```
<server_type>: Specify whether to kill the head, tail, or middle server.
<clean>: A clean termination (1) ensures state is flushed before the server shuts down, while 0 terminates immediately.
<kill_ports>: Provide the port number of the server to terminate.

### Server Leave Simulation
The client also supports simulating server for leaving (clean or unclean). Use the following command to make the server leave:

```bash
python3 client.py leave <port_number_for_head_or_tail> --kill_type <head_or_tail> --clean <0_or_1>
```

## Testing the System

```bash 
python3 test.py  
```
