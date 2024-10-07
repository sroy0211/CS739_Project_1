import socket
import re
import argparse

conn = None

def kv739_init(server_name):
    global conn
    try:
        HOST, PORT = server_name.split(':')
        PORT = int(PORT)

        ip_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
        if ip_pattern.match(HOST):
            pass
        else:
            try:
                HOST = socket.gethostbyname(HOST)
                print(f"Resolved DNS name to IP: {HOST}")
            except socket.gaierror:
                print("Failed to resolve DNS name")
                return -1

        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((HOST, PORT))
        print(f"Connected to {HOST}:{PORT}")
        return 0

    except Exception as e:
        print(f"Connection error: {e}")
        return -1

def kv739_shutdown():
    global conn
    try:
        if conn:
            conn.sendall(b'SHUTDOWN')
            response = conn.recv(1024)
            print(response.decode('utf-8'))
            
            conn.close()

            print("Connection closed and state freed.")
            return 0
        else:
            print("No active connection to close.")
            return -1
    except Exception as e:
        print(f"Error during shutdown: {e}")
        return -1

def kv739_get(key):
    global conn
    MAX_VALUE_SIZE = 2048

    try:
        conn.sendall(f'GET {key}'.encode('utf-8'))

        response = conn.recv(4096).decode('utf-8')

        if response.startswith('VALUE'):
            value = response.split(' ', 1)[1]

            if len(value) > MAX_VALUE_SIZE:
                print("Error: Retrieved value exceeds maximum allowed size.")
                return -1

            return (0, value)

        elif response == "KEY_NOT_FOUND":
            return 1
        else:
            print("Connection to server lost...")
            return -1
        
    except(ConnectionResetError, socket.error):
        print("Connection to server lost...")
        conn = None
        return -1

    except Exception as e:
        print(f"Error during GET: {e}")
        return -1

def kv739_put(key, new_value):
    global conn
    MAX_VALUE_SIZE = 2048

    try:
        conn.sendall(f'GET {key}'.encode('utf-8'))
        response = conn.recv(4096).decode('utf-8')

        if response.startswith('VALUE'):
            old_value = response.split(' ', 1)[1]
            has_old_value = True

        elif response == "KEY_NOT_FOUND":
            has_old_value = False
        else:
            print("Error: could not retrieve old value...")
            return -1

        if len(new_value) > MAX_VALUE_SIZE:
            print("Error: New value exceeds maximum allowed size...")
            return -1

        conn.sendall(f'PUT {key} {new_value}'.encode('utf-8'))
        response = conn.recv(1024).decode('utf-8')

        if response.startswith('UPDATED'):
            return (0, old_value, new_value) if has_old_value else 1
        elif response == "INSERTED":
            return (1, new_value)
        else:
            print("Error: could not insert new value...")
            return -1

    except(ConnectionResetError, socket.error):
        print("Connection to server lost...")
        conn = None
        return -1
    except Exception as e:
        print(f"Error during PUT: {e}")
        return -1

def main():
    global conn

    parser = argparse.ArgumentParser(description="Key-Value Store Client")
    parser.add_argument('--init', help="Server address in format host:port", required=True)

    args = parser.parse_args()

    if kv739_init(args.init) != 0:
        print("Failed to initialize connection.")
        return

    while True:

        command = input("Enter command (get <key>, put <key> <value>, shutdown): ").strip().split()

        if not command:
            continue

        elif command[0] == 'get' and len(command) == 2:
            response = kv739_get(command[1])
            if type(response) == int:
                if response == 1:
                    print("Key not found...")
                elif(response) == -1:
                    break
            else:
                print(f"Value: {response[1]}")

        elif command[0] == 'put' and len(command) == 3:
            response = kv739_put(command[1], command[2])
            if type(response) == int:
                break
            elif len(response) == 3:
                print(f"Old Value: {response[1]}\nNew Value: {response[2]}")
            elif len(response) == 2:
                print(f"New Value: {response[1]}")

        elif command[0] == 'shutdown':
            kv739_shutdown()
            break

        else:
            print("Invalid command. Available commands: get <key>, put <key> <value>, shutdown.")

        command = None

if __name__ == '__main__':
    main()
