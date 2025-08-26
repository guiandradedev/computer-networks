import socket
import threading
import sys
import os
import json
from colors import Colors
from ClientManager import ClientManager

class Client:
    def __init__(self,host='127.0.0.1', port=8000):
        self.connection = ClientManager(host,port)
        self._stop_event = threading.Event()
        self._receiver_thread = None
        self.lock = threading.Lock()

    def start(self):
        self.connection.connect()
        if not self.connection.running:
            return

        self._stop_event = threading.Event()
        self._receiver_thread = threading.Thread(target=self.handle_response)
        self._receiver_thread.start()
        self.run_client()

    def send_message(self, message):
        self.connection.send_data(message)

    # def close_connection(self):
    #     print("Connection closed")
    #     # Finaliza conexão em caso de erro ou disconnect
    #     self._stop_event.set()
    #     self.running = False

    #     # Caso seja disconnect, finaliza o socket e a thread
    #     if self.connection:
    #         try:
    #             self.connection.close()
    #         except:
    #             pass
        
    #     if self._receiver_thread and self._receiver_thread.is_alive():
    #         self._receiver_thread.join(timeout=2)

    #     try:
    #         sys.exit(130)
    #     except SystemExit:
    #         os._exit(130)

    def close_connection(self):
        """Fecha a conexão de forma segura"""
        print("Connection closed")
        
        # Sinaliza parada
        self._stop_event.set()
        
        # Fecha a conexão
        if self.connection:
            try:
                self.connection.close()
            except:
                pass
            self.connection.running = False
            

    def cleanup(self):
        """Método separado para limpeza final"""
        # ✅ Só faz join da thread principal
        if (self._receiver_thread and 
            self._receiver_thread.is_alive() and 
            threading.current_thread() != self._receiver_thread):
            self._receiver_thread.join(timeout=2)

        try:
            sys.exit(130)
        except SystemExit:
            os._exit(130)

    def handle_response(self):
        while not self._stop_event.is_set() and self.connection.running:
            try:
                response = self.connection.receive_data()
                if not response:
                    print("Server closed the connection.")
                    # self.close_connection()
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
            while self.connection.running:
                msg = input("Enter message: ")
                
                if msg == "":
                    continue
                
                self.send_message(msg)
                    
                if msg.lower() == "/exit":
                    break

        except KeyboardInterrupt:
            print("interrupted by user")
        finally:
            self.close_connection()
            self.cleanup()  
        # finally:
        #     self._stop_event.set()
        #     self.connection.close()
        
        # self._receiver_thread.join()
        print("Connection to server closed")

if __name__ == '__main__': 
    client = Client()
    try:
        client.start()
    except KeyboardInterrupt:
        print('\nInterrupted')