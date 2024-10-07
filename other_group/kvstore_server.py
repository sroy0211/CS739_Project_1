import sqlite3
import socket
import threading
import string

HOST = socket.gethostname()
PORT = 4000
DATABASE = 'kvstore.db'

db_lock = threading.Lock()

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('PRAGMA journal_mode=WAL;')
    cursor.execute('''CREATE TABLE IF NOT EXISTS kvstore (
                        key TEXT PRIMARY KEY,
                        value TEXT
                      )''')
    conn.commit()
    conn.close()

def is_valid_key(key):
    if len(key) > 128:
        return False
    valid_chars = string.ascii_letters + string.digits + string.punctuation + ' '
    if all(c in valid_chars for c in key) and '[' not in key and ']' not in key:
        return True
    return False

def is_valid_value(value):
    if len(value) > 2048:
        return False
    valid_chars = string.ascii_letters + string.digits + string.punctuation + ' '
    if all(c in valid_chars for c in value) and '[' not in value and ']' not in value:
        return True
    return False

def put_value(key, value):
    with db_lock:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO kvstore (key, value) VALUES (?, ?)", (key, value))
        conn.commit()
        conn.close()

def get_value(key):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM kvstore WHERE key = ?", (key,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def clear_db_contents():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM kvstore")
    result = cursor.fetchone()
    conn.close()

def handle_client(conn, addr):
    print(f"Connected by {addr}")
    try:
        while True:
            data = conn.recv(1024).decode('utf-8')
            if not data:
                break
            command = data.split()

            if command[0] == 'GET':
                key = command[1]
                if not is_valid_key(key):
                    conn.sendall(b"INVALID_KEY")
                    continue

                value = get_value(key)
                if value:
                    conn.sendall(f"VALUE {value}".encode('utf-8'))
                else:
                    conn.sendall(b"KEY_NOT_FOUND")

            elif command[0] == 'PUT':
                key = command[1]
                value = command[2]

                if not is_valid_key(key):
                    conn.sendall(b"INVALID_KEY")
                    continue
                if not is_valid_value(value):
                    conn.sendall(b"INVALID_VALUE")
                    continue

                old_value = get_value(key)
                put_value(key, value)
                if old_value:
                    conn.sendall(f"UPDATED {old_value}".encode('utf-8'))
                else:
                    conn.sendall(b"INSERTED")

            elif command[0] == 'SHUTDOWN':
                conn.sendall(b"Goodbye! Closing client connection.")
                print(f"Client at {addr} is shutting down.")
                break
            
            elif command[0] == 'CLEAR':
                clear_db_contents()
                conn.sendall(b"reset done. Db contents cleared.")
                break
            else:
                conn.sendall(b"INVALID_COMMAND")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

def start_server():
    init_db()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server started on {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            client_handler = threading.Thread(target=handle_client, args=(conn, addr))
            client_handler.start()

if __name__ == "__main__":
    start_server()