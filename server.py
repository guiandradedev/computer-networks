import socket
import threading
import time
import psutil
from datetime import datetime

class Server:
    def __init__(self, host='0.0.0.0', port=8000):
        self.host = host
        self.port = port
        self._clients = {}
        self.connection_limits = 0
        self.running = True
        self.lock = threading.Lock()
        self.modes = ["basic", "advanced"]

    def create_thread(self, target, args, stop_event=True):
        stop_event = threading.Event()
        if stop_event:
            args = args + (stop_event,)
        thread = threading.Thread(target=target, args=args)
        thread.daemon = True
        thread.start()

    def help(self):
        help_msg = (
                    "Available commands:\n"
                    "/help - Show this help message\n"
                    "/exit - Close the connection\n"
                    "/cpu -t <seconds> -m <mode> - Start CPU monitoring\n"
                    "/mem -t <seconds> -m <mode> - Start Memory monitoring\n"
                    "/quit <id> - Stop monitoring by ID\n"
                    "/monitors - Show all monitoring views\n"
                    "Modes: basic, advanced\n"
                )
        return help_msg

    def _validate_and_format_request(self, request, base_timer, base_mode):
        if "-t=" in request:
            input_timer = request.split("-t=")[1].split(" ")[0]
            if not input_timer.isdigit():
                raise ValueError("Value must be an integer.")
            timer = int(input_timer)
        else:
            timer = base_timer

        if "-m=" in request:
            mode_string = request.split("-m=")[1].split(" ")[0]
            if mode_string not in self.modes:
                raise ValueError(f"Mode must be in {self.modes}.")
            mode = self.modes.index(mode_string)
        else:
            mode = base_mode

        return timer, mode
    
    def handle_client(self, client_socket, client_address):
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Accepted connection from {client_address[0]}:{client_address[1]}")

        while self.running:
            try:
                request = client_socket.recv(1024).decode("utf-8")
                # Caso não haja requisição, encerra a conexão
                if not request:
                    break

                # Comandos fixos sem parâmetros
                if request.lower() == "/exit":
                    client_socket.send("Connection ended".encode("utf-8"))
                    break

                if request.lower() == "/monitors":
                    # with self.lock:
                    #     monitors = "\n".join([f"{id}: {info['type']} - {info['mode']}" for id, info in self._clients.items()])
                    #     client_socket.send(monitors.encode("utf-8"))
                    # continue
                    client_socket.send("No active monitors.".encode("utf-8"))
                
                if request.lower() == "/help":
                    help_msg = self.help()
                    client_socket.send(help_msg.encode("utf-8"))
                    continue

                # Comandos com parâmetros
                req = request.strip()

                if req.lower().startswith("/cpu"):
                    try:
                        timer, mode = self._validate_and_format_request(req, 5, 0)
                    except ValueError as e:
                        client_socket.send(f"Error: {e}".encode("utf-8"))
                        continue
                    
                    print(f"Starting CPU monitoring for {client_address} every {timer} seconds in {self.modes[mode]} mode.")
                    self.create_thread(target=self.cpu, args=(client_socket, client_address, timer, mode))
                    continue
                
                elif req.lower().startswith("/mem"):
                    try:
                        timer, mode = self._validate_and_format_request(req, 5, 0)
                    except ValueError as e:
                        client_socket.send(f"Error: {e}".encode("utf-8"))
                        continue
                    
                    print(f"Starting Memory monitoring for {client_address} every {timer} seconds in {self.modes[mode]} mode.")
                    self.create_thread(target=self.mem, args=(client_socket, client_address, timer, mode))
                    continue
                
                else:
                    client_socket.send("Unknown command. Use /help to see available commands.".encode("utf-8"))
                    continue

            except Exception as e:
                print(f"Error handling client {client_address}: {e}")
                break

        client_socket.close()
        print(f"Connection to {client_address} closed")

    def mem(self, client_socket, client_address, seconds, mode, stop_event):
        while not stop_event.is_set():
            mem = psutil.virtual_memory()
            msg_lines = []
            msg_lines.append(f"💾 Memory Usage: {mem.percent:.1f}%")
            msg_lines.append(f"📊 Available: {mem.available / (1024**3):.2f} GB")
            msg_lines.append(f"📈 Used: {mem.used / (1024**3):.2f} GB")
            msg_lines.append(f"📉 Free: {mem.free / (1024**3):.2f} GB")
            
            try:
                client_socket.send("\n".join(msg_lines).encode("utf-8"))
            except:
                break
            
            time.sleep(seconds)

    def cpu(self, client_socket, client_address, seconds, mode, stop_event):
        while not stop_event.is_set():
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_times_per_core = psutil.cpu_times(percpu=True)
            load_avg = psutil.getloadavg()

            msg_lines = []
            msg_lines.append(f"📊 CPU Usage: {cpu_percent:.1f}%")
            
            if mode == 1:  # advanced mode
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

            try:
                client_socket.send("\n".join(msg_lines).encode("utf-8"))
            except:
                break

            time.sleep(seconds)

    def start(self):
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # ✅ Permitir reutilizar endereço
        host = (self.host, self.port)
        max_connections = 5
        self._server.bind(host)
        self._server.listen(max_connections)
        print("Server started")
        print(f"Listening on {host[0]}:{host[1]}...")

        while self.running:
            try:
                client_socket, client_address = self._server.accept()
                # ✅ Correção: ordem correta dos parâmetros
                thread = threading.Thread(target=self.handle_client, args=(client_socket, client_address))
                thread.start()
            except Exception as e:
                if self.running:
                    print(f"Error: {e}")
        
        self._server.close()
        print("Server stopped")

if __name__ == '__main__':
    server = Server()
    try:
        server.start()
    except KeyboardInterrupt:
        print('\nInterrupted')
        server.running = False