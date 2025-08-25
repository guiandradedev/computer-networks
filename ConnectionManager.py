import socket
from abc import ABC, abstractmethod

class ConnectionManager(ABC):
    def __init__(self, host='127.0.0.1', port=8000):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = False

    def send_data(self,message:str):
        if not self.running:
            print("Not connected to server")
            return False
        try:
            self.socket.send(message.encode("utf-8")[:1024])
        except Exception as e:
            print(f"Error sending message: {e}") 
    
    def receive_data(self):
        try:
            return self.socket.recv(4096)
        except Exception as e:
            print(f"Error receiving data: {e}")
            return None

    def close(self):
        self.running = False
        try:
            self.socket.close()
        except:
            pass