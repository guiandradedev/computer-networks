import socket
import threading
import sys
import os
import json
from Colors import Colors
from ClientManager import ClientManager
import time

class Client:
    def __init__(self,host='127.0.0.1', port=8000):
        self.connection = ClientManager(host,port)
        self._stop_event = threading.Event()
        self._receiver_thread = None
        self._connection_lock = threading.Lock()



    def start(self):
        self.connection.connect()
        if not self.connection.running:
            return
        
        self._stop_event.clear() 

        # self._stop_event = threading.Event()
        self._receiver_thread = threading.Thread(target=self.handle_response)
        self._receiver_thread.start()
        self.run_client()
        print("pos run")

    def send_message(self, message):
        with self._connection_lock:
            if self.connection.running:
                return self.connection.send_data(message)
        return False
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
        
    #     # if self._receiver_thread and self._receiver_thread.is_alive():
    #     #     self._receiver_thread.join(timeout=2)

    #     # try:
    #     #     sys.exit(130)
    #     # except SystemExit:
    #     #     os._exit(130)

    def close_connection(self):
        """Fecha a conexão de forma segura"""
        print("Connection closed")
        print("aaaa1")
        
        with self._connection_lock:
            print(self._connection_lock, self.connection.running)
            if not self.connection.running:
                return
        print("aaaa2")
        
        # Sinaliza parada
        self._stop_event.set()
        self.connection.running = False

        time.sleep(0.1)
        print("aaaa")
        
        if self.connection.socket:
            try:
                self.connection.close()
            except:
                print("erro")
                pass
        print("asdsa")

        if self._receiver_thread and self._receiver_thread.is_alive():
            print("d")
            self._receiver_thread.join(timeout=2)
        
        print("a")
        # Fecha a conexão
        with self._connection_lock:
            if self.connection:
                try:
                    self.connection.close()
                except:
                    pass
                self.connection.running = False
        print("c")


    # def close_connection(self):
    #     """Fecha a conexão de forma segura"""
    #     print("Connection closed")
        
    #     # ✅ CORREÇÃO: Sinaliza parada PRIMEIRO
    #     self._stop_event.set()
        
    #     # ✅ CORREÇÃO: Aguarda um pouco para thread processar sinal
    #     time.sleep(0.1)
        
    #     # ✅ CORREÇÃO: Só faz join se não for a própria thread
    #     current_thread = threading.current_thread()
    #     if (self._receiver_thread and 
    #         self._receiver_thread.is_alive() and 
    #         self._receiver_thread != current_thread):
    #         self._receiver_thread.join(timeout=2)
        
    #     # ✅ CORREÇÃO: Fecha conexão com lock
    #     with self._connection_lock:
    #         if self.connection:
    #             try:
    #                 self.connection.close()
    #             except:
    #                 pass

    def handle_response(self):
        while not self._stop_event.is_set() or self.connection.running:
            try:
                if self._stop_event.is_set():
                    break

                with self._connection_lock:
                    if not self.connection.running:
                        break
                    response = self.connection.receive_data()

                if not response:
                    print("Server closed the connection.")
                    # self.close_connection()
                    self._stop_event.set()
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
        self.close_connection()

    def run_client(self):
        try:
            while self.connection.running:
                msg = input("Enter message: ")
                
                if msg == "":
                    continue

                if not self.connection.running or self._stop_event.is_set():
                    break
                
                if msg.lower() == "/exit":
                    break

                self.send_message(msg)

        except KeyboardInterrupt:
            print("interrupted by user")
        finally:
            # self._stop_event.set()
            # self.connection.close()
            self.close_connection()
            # self._receiver_thread.join()
        
        # self._receiver_thread.join()
        print("Connection to server closed")
        
if __name__ == '__main__': 
    client = Client()
    try:
        client.start()
    except KeyboardInterrupt:
        print('\nInterrupted')