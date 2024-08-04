
import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox, filedialog
from PIL import Image, ImageTk
import io
import os
from plyer import notification

# Client configuration
HOST = '127.0.0.1'  # Server IP address
PORT = 12345        # Server port

# Create a socket object
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

# GUI class for the chat client
class ChatClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat Application")
        self.root.geometry("600x600")

        self.chat_frame = tk.Frame(self.root)
        self.chat_frame.pack(padx=20, pady=5, fill=tk.BOTH, expand=True)

        self.chat_area = scrolledtext.ScrolledText(self.chat_frame, wrap=tk.WORD)
        self.chat_area.pack(fill=tk.BOTH, expand=True)
        self.chat_area.config(state='disabled')

        self.entry_frame = tk.Frame(self.root)
        self.entry_frame.pack(padx=20, pady=5, fill=tk.X)

        self.message_entry = tk.Entry(self.entry_frame, width=40)
        self.message_entry.pack(side=tk.LEFT, padx=(0, 5), pady=5, fill=tk.X, expand=True)
        self.message_entry.bind("<Return>", self.send_message)

        self.send_button = tk.Button(self.entry_frame, text="Send", command=self.send_message)
        self.send_button.pack(side=tk.RIGHT, pady=5)

        self.file_button = tk.Button(self.entry_frame, text="Send File", command=self.send_file)
        self.file_button.pack(side=tk.RIGHT, pady=5)

        self.username = simpledialog.askstring("Username", "Please enter your username:", parent=self.root)
        if not self.username:
            self.root.destroy()
            return
        client.send(self.username.encode('utf-8'))

        self.receive_thread = threading.Thread(target=self.receive_messages)
        self.receive_thread.start()

    def send_message(self, event=None):
        message = self.message_entry.get()
        if message.strip() == "":
            messagebox.showwarning("Warning", "Please type a message first")
            return
        message = f"{self.username}: {message}"
        self.message_entry.delete(0, tk.END)
        client.send(message.encode('utf-8'))

    def send_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            file_ext = os.path.splitext(file_name)[1].lower()
            file_type = 'unknown'

            if file_ext in ['.png', '.jpg', '.jpeg', '.gif']:
                file_type = 'image'
            elif file_ext in ['.mp4', '.avi', '.mov']:
                file_type = 'video'

            client.send(f"FILE|{file_name}|{file_size}|{file_type}".encode('utf-8'))

            with open(file_path, 'rb') as f:
                file_data = f.read()
                client.send(file_data)

            self.show_notification(f"Sent {file_type}: {file_name}")

    def receive_messages(self):
        while True:
            try:
                header = client.recv(1024).decode('utf-8')
                if header.startswith('FILE'):
                    file_info = header.split('|')
                    file_name = file_info[1]
                    file_size = int(file_info[2])
                    self.receive_file(file_name, file_size)
                else:
                    self.chat_area.config(state='normal')
                    self.chat_area.insert(tk.END, header + "\n")
                    self.chat_area.config(state='disabled')
                    self.chat_area.yview(tk.END)
                    self.show_notification(header)
            except Exception as e:
                print(f"Error: {e}")
                client.close()
                break

    def receive_file(self, file_name, file_size):
        file_data = b''
        while len(file_data) < file_size:
            packet = client.recv(min(file_size - len(file_data), 4096))
            if not packet:
                break
            file_data += packet

        file_path = os.path.join('uploads', file_name)
        with open(file_path, 'wb') as f:
            f.write(file_data)

        self.chat_area.config(state='normal')
        if file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            image = Image.open(file_path)
            image.thumbnail((300, 300))
            photo = ImageTk.PhotoImage(image)
            self.chat_area.image_create(tk.END, image=photo)
            self.chat_area.insert(tk.END, f"Image received: {file_name}\n")
        elif file_name.lower().endswith(('.mp4', '.avi', '.mov')):
            self.chat_area.insert(tk.END, f"Video received: {file_name}\n")
        self.chat_area.config(state='disabled')
        self.chat_area.yview(tk.END)

    def show_notification(self, message):
        notification.notify(
            title='New Message',
            message=message,
            app_name='Chat Application',
            timeout=5
        )

# Run the Tkinter event loop
root = tk.Tk()
client_gui = ChatClient(root)
root.mainloop()
