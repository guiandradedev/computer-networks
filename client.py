import socket


def run_client():
    # create a socket object
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_ip = "127.0.0.1"  # replace with the server's IP address
    server_port = 8000  # replace with the server's port number
    # establish connection with server
    client.connect((server_ip, server_port))

    # msg = input("Enter message: ")
    # client.send(msg.encode("utf-8")[:1024])

    while True:
        msg = input("Enter message: ")
        
        # Check if user wants to exit before sending to server
        if msg.lower() == "/exit":
            client.send(msg.encode("utf-8")[:1024])
            break
            
        client.send(msg.encode("utf-8")[:1024])
        # input message and send it to the server
        # receive message from the server
        response = client.recv(1024)
        response = response.decode("utf-8")

        print(f"Received: {response}")

    # close client socket (connection to the server)
    client.close()
    print("Connection to server closed")

run_client()
