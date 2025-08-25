from ConnectionManager import ConnectionManager
import socket
import threading

class ServerManager(ConnectionManager):
    def __init__(self, host='0.0.0.0', port=8000, connection_limits=5):

        super().__init__(host=host, port=port)
        self.connection_limits = connection_limits

    def start(self, target_function, args=()):
        """
        Inicia o servidor e aceita conexões de clientes.
        """

        # Instância o server com os protocolos de rede
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Define a execução
        host = (self.host, self.port)

        self.socket.bind(host)
        self.socket.listen(self.connection_limits)
        self.running = True
        print("Server started")
        print(f"Listening on {host[0]}:{host[1]}...")

        self._accept_connections(target_function, args)

        self.socket.close()
        print("Server stopped")

    def _accept_connections(self, target_function, args):
        while self.running:
            try:
                client_socket, client_address = self.socket.accept()
                new_args = (client_socket, client_address,) + args
                print(args)
                thread = threading.Thread(target=target_function, args=new_args)
                thread.start()
            except Exception as e:
                if self.running:
                    print(f"Error: {e}")