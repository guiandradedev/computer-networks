from ConnectionManager import ConnectionManager
from Colors import Colors

class ClientManager(ConnectionManager):
    def __init__(self, host='0.0.0.0', port=8000):
        super().__init__(host, port)
        self.connection_limits = 0

    def connect(self):
        """
        Estabelece uma conexão com o servidor.
        
        :return: True se a conexão foi bem-sucedida, False caso contrário.
        """
        try:
            self.socket.connect((self.host, self.port))
            self.running = True
            print(f"Connected to {self.host}:{self.port}")
        except ConnectionRefusedError:
            Colors.error("Connection refused by server")
            return False
        except TimeoutError:
            Colors.error("Connection Timeout")
            return False
        except OSError as e:
            Colors.error(f"Connection Error: {e}")
            return False
        except Exception as e:
            Colors.error(f"Failed to connect: {e}")
            self.running = False
        finally:
            return self.running