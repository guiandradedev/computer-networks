import socket
from abc import ABC, abstractmethod
from Colors import Colors

class ConnectionManager(ABC):
    def __init__(self, host='127.0.0.1', port=8000):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = False

    def send_data(self, message, target_socket=None):
        socket_to_use = target_socket or self.socket
        # Pra definir se vai ser como um socket do servidor ou passado como parametro
        
        if not self.running and not target_socket:
            Colors.error("Not connected to server")
            return False
        
        try:
            socket_to_use.send(message.encode("utf-8"))
            return True
        except Exception as e:
            Colors.error(f"Error sending message: {e}")
            return False
    
    def receive_data(self, target_socket=None):
        socket_to_use = target_socket or self.socket
        if not self.running and not target_socket:
            Colors.error("Not connected to server")
            return False
        try:
            return socket_to_use.recv(4096)
        except Exception as e:
            Colors.error(f"Error receiving data: {e}")
            return None

    def close(self):
        self.running = False
        try:
            self.socket.close()
            self.socket.shutdown(socket.SHUT_RDWR)
        except:
            pass