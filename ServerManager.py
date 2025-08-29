from ConnectionManager import ConnectionManager
import socket
import threading
from Colors import Colors
from datetime import datetime
import json

class ServerManager(ConnectionManager):
    """ 
    Classe que gerencia o servidor, aceitando conexões de clientes e delegando o atendimento a threads.
    """
    def __init__(self, host='0.0.0.0', port=8000):

        super().__init__(host=host, port=port)
        # self.connection_limits = connection_limits

    def set_connection_limits(self, connection_limits):
        if connection_limits <= 0:
            raise ValueError("Connection Limits must be greather than 0")
        self.connection_limits = connection_limits

    def start(self, target_function, args=()):
        """
        Inicia o servidor e aceita conexões de clientes.
        
        :param target_function: Função alvo para lidar com conexões de clientes.
        :param args: Argumentos adicionais para a função alvo.
        :return: None
        """

        # Instância o server com os protocolos de rede
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        if not self.connection_limits:
            Colors.error("Connection Limits must exists")
            return
        
        self.connection_semaphore = threading.Semaphore(self.connection_limits)

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
        """
        Aceita conexões de clientes e inicia uma nova thread para cada conexão.
        
        :param target_function: Função alvo para lidar com conexões de clientes.
        :param args: Argumentos adicionais para a função alvo.
        :return: None
        """
        while self.running:
            try:
                client_socket, client_address = self.socket.accept()

                if not self.connection_semaphore.acquire(blocking=False):
                    Colors.error(f"Rejected connection from {client_address}: too many connections")

                    # Envia mensagem de erro pro client
                    date = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"
                    message = f"{date} Too many connections, connection closed."
                    response = json.dumps({"status": "error", "message": message})
                    self.send_data(response, client_socket)

                    client_socket.close()
                    continue

                new_args = (target_function, client_socket, client_address,) + args
                thread = threading.Thread(target=self.client_wrapper, args=new_args)
                thread.start()
            except Exception as e:
                if self.running:
                    print(f"Error: {e}")


    def client_wrapper(self, target_function, sock, addr, *args):
        try:
            target_function(sock, addr, *args)
        except Exception as e:
            Colors.error(f"An error occurred on connection address {addr}: {e}")
        finally:
            self.connection_semaphore.release()
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except:
                pass

            sock.close()
