from ConnectionManager import ConnectionManager
import socket

class ClientManager(ConnectionManager):
    def __init__(self, host='0.0.0.0', port=8000):
        super().__init__(host, port)
        self.connection_limits = 0

    def connect(self):
        try:
            self.socket.connect((self.host, self.port))
            self.running = True
            print(f"Connected to {self.host}:{self.port}")
        except Exception as e:
            print(f"Failed to connect: {e}")
            self.running = False
        finally:
            return self.running