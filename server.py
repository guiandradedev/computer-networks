import socket
import threading
import time
import psutil

def handle_client(client_socket, client_address):
    print(f"Accepted connection from {client_address[0]}:{client_address[1]}")

    while True:
        request = client_socket.recv(1024).decode("utf-8")
        if not request:
            break

        if request.lower() == "close":
            client_socket.send("closed".encode("utf-8"))
            break

        if request.lower().startswith("cpu"):
            seconds = request.split("cpu-")[1]
            if not seconds.isdigit():
                client_socket.send("Invalid CPU request".encode("utf-8"))
                continue
            seconds = int(seconds)
            thread = threading.Thread(target=cpu, args=(client_socket, client_address, seconds))
            thread.daemon = True
            thread.start()

        if request.lower().startswith("mem"):
            print(f"Memory request from {client_address}: {request}")

        if request.lower().startswith("quit"):
            print("dasdas")

        print(f"Received from {client_address}: {request}")
        client_socket.send("accepted".encode("utf-8"))

    client_socket.close()
    print(f"Connection to {client_address} closed")

def cpu(client_socket, client_address, seconds):
    while True:
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_times_per_core = psutil.cpu_times(percpu=True)
        load_avg = psutil.getloadavg()

        msg_lines = []
        msg_lines.append(f"📊 CPU Usage: {cpu_percent:.1f}%")
        msg_lines.append("🖥️  CPU Times per Core:")
        for i, core_time in enumerate(cpu_times_per_core, start=1):
            msg_lines.append(
                f"   Core {i}: user={core_time.user:.2f}s, "
                f"system={core_time.system:.2f}s, "
                f"idle={core_time.idle:.2f}s"
            )
        msg_lines.append(
            f"📈 Load Average (1m, 5m, 15m): "
            f"{load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}"
        )

        msg = "\n".join(msg_lines) + "\n"

        print(f"Sending CPU info to client {client_address}")

        try:
            client_socket.send(msg.encode("utf-8"))
        except:
            print(f"Cliente {client_address} desconectou, encerrando thread CPU.")
            break

        time.sleep(seconds)


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = ("localhost", 8000)
    max_connections = 5
    server.bind(host)
    server.listen(max_connections)
    print(f"Ouvindo {host[0]}:{host[1]}...")

    while True:
        client_socket, client_address = server.accept()
        thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        thread.start()


if __name__ == "__main__":
    start_server()
