import socket
import threading
import os

# Server configuration
HOST = '127.0.0.1'  # Localhost
PORT = 12345        # Port to listen on

# Directory to save received files
UPLOAD_DIR = 'uploads'
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Create a socket object
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

# List to keep track of connected clients and their usernames
clients = []
usernames = {}

# Broadcast a message to all connected clients
def broadcast(message):
    for client in clients:
        try:
            client.send(message)
        except:
            # Remove clients that failed to send the message
            clients.remove(client)

# Handle communication with a connected client
def handle_client(client):
    while True:
        try:
            # Receive the header to determine if the message is a file
            header = client.recv(1024).decode('utf-8')
            if not header:
                break

            # Check if the message is a file
            if header.startswith('FILE'):
                # Extract file info
                file_info = header.split('|')
                file_name = file_info[1]
                file_size = int(file_info[2])

                # Receive the file data
                file_data = b''
                while len(file_data) < file_size:
                    packet = client.recv(min(file_size - len(file_data), 4096))
                    if not packet:
                        break
                    file_data += packet

                # Save the received file
                file_path = os.path.join(UPLOAD_DIR, file_name)
                with open(file_path, 'wb') as f:
                    f.write(file_data)

                # Broadcast file path and type
                broadcast(f"FILE|{file_name}|{file_size}".encode('utf-8'))
            else:
                # Regular message
                broadcast(header.encode('utf-8'))
        except Exception as e:
            print(f"Error: {e}")
            clients.remove(client)
            username = usernames.pop(client, "Unknown")
            broadcast(f"{username} has left the chat.".encode('utf-8'))
            break

    client.close()

# Accept and handle new client connections
def receive():
    while True:
        client, address = server.accept()
        print(f"Connected with {str(address)}")

        client.send("".encode('utf-8'))
        username = client.recv(1024).decode('utf-8')
        usernames[client] = username
        clients.append(client)

        broadcast(f"{username} has joined the chat.".encode('utf-8'))

        thread = threading.Thread(target=handle_client, args=(client,))
        thread.start()

# Start the server
print("Server is running...")
receive()
