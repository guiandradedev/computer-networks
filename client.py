import socket
import threading
import sys
import os
import json

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def handle_response(client, stop_event):
    while not stop_event.is_set():
        try:
            response = client.recv(1024)
            if not response:
                print("Server closed the connection.")
                stop_event.set()
                try:
                    sys.exit(130)
                except SystemExit:
                    os._exit(130)
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
                        print(f"{bcolors.WARNING}Server > {message}{bcolors.ENDC}")
                    elif status == "error":
                        print(f"{bcolors.FAIL}Server > {message}{bcolors.ENDC}")
                    elif status == "success":
                        print(f"{bcolors.OKBLUE}Server > {message}{bcolors.ENDC}")
                    else:
                        print(f"{bcolors.UNDERLINE}Server > {message}{bcolors.ENDC}")
                else:
                    print(f"Recebido: {response_json}")
            except json.JSONDecodeError:
                # Caso não seja JSON, imprime a mensagem bruta
                print(f"Recebido: {response}")
        except Exception as e:
            print(f"Error receiving data: {e}")
            break


def run_client():
    # create a socket object
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_ip = "127.0.0.1"  # replace with the server's IP address
    server_port = 8000  # replace with the server's port number
    # establish connection with server
    client.connect((server_ip, server_port))

    # msg = input("Enter message: ")
    # client.send(msg.encode("utf-8")[:1024])
    
    stop_event = threading.Event()
    receiver_thread = threading.Thread(target=handle_response, args=(client, stop_event))
    receiver_thread.start()

    try:
        while True:
            msg = input("Enter message: ")
            
            if msg == "":
                continue
            
            client.send(msg.encode("utf-8")[:1024])
                
            # Check if user wants to exit before sending to server
            if msg.lower() == "/exit":
                client.send(msg.encode("utf-8")[:1024])
                break
    except KeyboardInterrupt:
        print("interrupted by user")
    finally:
        stop_event.set()
        client.close()
    
    receiver_thread.join()
    # close client socket (connection to the server)
    print("Connection to server closed")
    
    
run_client()
