import threading
import json
from Colors import Colors
from ClientManager import ClientManager
import time 

class Client:
    """
    Classe que representa o cliente do sistema de monitoramento.
    """
    def __init__(self,host='127.0.0.1', port=8000):
        self.connection = ClientManager(host,port)
        self._stop_event = threading.Event()
        self._receiver_thread = None
        self._connection_lock = threading.Lock()


    def start(self):
        """
        Inicia a conexão com o servidor e o loop principal do cliente.
        """
        self.header()
        
        self.connection.connect()

        if not self.connection.running:
            return
        
        self._stop_event.clear() 

        self._receiver_thread = threading.Thread(target=self.handle_response)
        self._receiver_thread.start()

        time.sleep(0.1)
        # Delay de 10ms para que a mensagem inicial de ajuda não seja cortada pelo client
        self.run_client()
        

    def header(self):
        """ 
        Exibe o cabeçalho do cliente. 
        """
        Colors.header("System Monitor")
        print("Here you can visualize system monitor data in real time.")
        print()


    def send_message(self, message):
        """ 
        Envia uma mensagem para o servidor.
        
        :param message: Mensagem a ser enviada.
        :type message: str
        :return: True se a mensagem foi enviada com sucesso, False caso contrário.
        :rtype: bool
        """
        if self.connection.running:
            try:
                self.connection.send_data(message)
            except Exception as e:
                Colors.error("Server > Error sending message: {e}")
        return False
    
        
    def close_connection(self):
        """
        Fecha a conexão com o servidor e encerra a thread de recepção.
        """
        print("Starting close connection")
        with self._connection_lock:
            if not self.connection.running:
                return

            self._stop_event.set()
            self.connection.running = False
            try:
                self.connection.shutdown()
            except Exception:
                pass

            try:
                self.connection.close()
            except Exception as e:
                Colors.error(f"Server > Error closing connection: {e}")

        if self._receiver_thread and self._receiver_thread.is_alive():
            self._receiver_thread.join(timeout=1)

    def handle_response(self):
        """
        Lida com as respostas recebidas do servidor.
        """
        while not self._stop_event.is_set() and self.connection.running:
            try:
                if self._stop_event.is_set() or not self.connection.running:
                    break

                response = self.connection.receive_data()

                if not response:
                    print("Server closed the connection.")
                    self.connection.running = False
                    self._stop_event.set()
                    return

                response = response.decode("utf-8")
                try:
                    response_json = json.loads(response)
                    if isinstance(response_json, dict):
                        status = response_json.get("status", "error")
                        message = response_json.get("message", "")
                        if status == "info":
                            print(f"Server > {message}")
                        elif status == "warning":
                            Colors.warning(f"Server > {message}")
                        elif status == "error":
                            Colors.error(f"Server > {message}")
                        elif status == "success":
                            Colors.success(f"Server > {message}")
                        else:
                            Colors.underline(f"Server > {message}")
                    else:
                        Colors.underline(f"Server > {response_json}")
                except json.JSONDecodeError:
                    Colors.underline(f"Server > {response}")
                    print(f"Recebido: {response}")

            except ConnectionResetError:
                Colors.error("Conexão encerrada pelo servidor (reset).")
                self._stop_event.set() # Sinaliza a thread principal para parar
                return
            
            except KeyboardInterrupt:
                Colors.ok("Connection interrupted by user")
                return
            
            except Exception as e:
                Colors.error(f"Server > Error receiving data: {e}")
                self._stop_event.set() # Sinaliza a thread principal para parar
                return



    def run_client(self):
            """
            Loop principal do cliente para enviar mensagens ao servidor.
            """
            try:
                while not self._stop_event.is_set():
                    msg = input("Request > ")
                    
                    if msg == "":
                        continue

                    if self._stop_event.is_set():
                        break
                    
                    if msg.lower() == "/exit":
                        break

                    self.send_message(msg)

            except ConnectionResetError:
                Colors.error("Connection ended by server (reset).")

            except KeyboardInterrupt:
                Colors.ok("Connection interrupted by user")

            finally:
                self.close_connection()

            Colors.success("Connection to server closed")


if __name__ == '__main__': 
    client = Client()
    try:
        client.start()
    except KeyboardInterrupt:
        Colors.warning("Interrupted by user")