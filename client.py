import socket
import threading

def handle_response(client, stop_event):
    while not stop_event.is_set():
        try:
            response = client.recv(1024)
            if not response:
                print("Server closed the connection.")
                stop_event.set()
                break
            response = response.decode("utf-8")
            print(f"Received: {response}")
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
