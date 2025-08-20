import socket
import threading
import sys
import os
import json

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class Client:
    def __init__(self,host='127.0.0.1', port=8000):
        self.connection = ConnectionManager(host,port)
        self._stop_event = threading.Event()
        self._receiver_thread = None
    def start(self):
        self.connection.establish_connection()
        if not self.connection._is_connected:
            return

        self._stop_event = threading.Event()
        self._receiver_thread = threading.Thread(target=self.handle_response)
        self._receiver_thread.start()
        self.run_client()

    def send_message(self, message):
        self.connection.send_data(message)

    def close_connection(self):
        self._stop_event.set()
        self.connection.close()
        if self._receiver_thread and self._receiver_thread.is_alive():
            self._receiver_thread.join(timeout=2)
        print("Connection closed")
        # # Finaliza conexão em caso de erro ou disconnect
        # self._stop_event.set()
        # self._is_connected = False

        # # Caso seja disconnect, finaliza o socket e a thread
        # if self._client:
        #     try:
        #         self._client.close()
        #     except:
        #         pass
        
        # if self._receiver_thread and self._receiver_thread.is_alive():
        #     self._receiver_thread.join(timeout=2)

        # try:
        #     sys.exit(130)
        # except SystemExit:
        #     os._exit(130)

    def handle_response(self):
        while not self._stop_event.is_set() and self.connection._is_connected:
            try:
                response = self.connection.receive_data()
                if not response:
                    print("Server closed the connection.")
                    self.close_connection()
                    break
                response = response.decode("utf-8")
                try:
                    response_json = json.loads(response)
                    if isinstance(response_json, dict):
                        status = response_json.get("status", "error")
                        message = response_json.get("message", "")
                        if status == "info":
                            print(f"Server > {message}")
                        elif status == "warning":
                            print(f"{Colors.WARNING}Server > {message}{Colors.ENDC}")
                        elif status == "error":
                            print(f"{Colors.FAIL}Server > {message}{Colors.ENDC}")
                        elif status == "success":
                            print(f"{Colors.OKBLUE}Server > {message}{Colors.ENDC}")
                        else:
                            print(f"{Colors.UNDERLINE}Server > {message}{Colors.ENDC}")
                    else:
                        print(f"Recebido: {response_json}")
                except json.JSONDecodeError:
                    # Caso não seja JSON, imprime a mensagem bruta
                    print(f"Recebido: {response}")
            except Exception as e:
                print(f"Error receiving data: {e}")
                break


    def run_client(self):
        try:
            while self.connection._is_connected:
                msg = input("Enter message: ")
                
                if msg == "":
                    continue
                
                self.send_message(msg)
                    
                if msg.lower() == "/exit":
                    break

        except KeyboardInterrupt:
            print("interrupted by user")
        finally:
            self._stop_event.set()
            self.connection.close()
        
        self._receiver_thread.join()
        print("Connection to server closed")


class ConnectionManager:
    def __init__(self, host='127.0.0.1', port=8000):
        self.host = host
        self.port = port
        self._client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._is_connected = False
    
    def establish_connection(self):
        try:
            self._client.connect((self.host, self.port))
            self._is_connected = True
            print(f"Connected to {self.host}:{self.port}")
        except Exception as e:
            print(f"Failed to connect: {e}")
            self._is_connected = False

    def send_data(self,message:str):
        if not self._is_connected:
            print("Not connected to server")
            return False
        try:
            self._client.send(message.encode("utf-8")[:1024])
        except Exception as e:
            print(f"Error sending message: {e}") 
    
    def receive_data(self):
        try:
            return self._client.recv(4096)
        except Exception as e:
            print(f"Error receiving data: {e}")
            return None

    def close(self):
        self._is_connected = False
        try:
            self._client.close()
        except:
            pass

if __name__ == '__main__': 
    client = Client()
    try:
        client.start()
    except KeyboardInterrupt:
        print('\nInterrupted')