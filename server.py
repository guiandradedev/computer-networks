import socket
import threading
import time
import psutil
from datetime import datetime

class Server:
    def __init__(self, host='0.0.0.0', port=8000):
        self.host = host
        self.port = port
        self._clients = {}  # dicionário para armazenar informações dos clientes e suas threads/monitors ativas
        self.connection_limits = 0
        self.running = True
        self.lock = threading.Lock()
        self.modes = ["basic", "advanced"]

        self.timer = 10
        self.mode = 1

    def create_thread(self, target, args, stop_event):
        full_args = args + (stop_event,)
        
        thread = threading.Thread(target=target, args=full_args)
        thread.daemon = True
        thread.start()
        
        return thread

    def help(self):
        help_msg = (
                    "Available commands:\n"
                    "/help - Show this help message\n"
                    "/exit - Close the connection\n"
                    "/cpu -t=<seconds> -m=<mode> - Start CPU monitoring\n"
                    "/mem -t=<seconds> -m=<mode> - Start Memory monitoring\n"
                    "/quit <id> - Stop monitoring by ID\n"
                    "/monitors - Show all monitoring views\n"
                    "Modes: basic, advanced\n"
                )
        return help_msg

    def _validate_and_format_request(self, request):
        if "-t=" in request:
            input_timer = request.split("-t=")[1].split(" ")[0]
            if not input_timer.isdigit():
                raise ValueError("Value must be an integer.")
            timer = int(input_timer)
        else:
            timer = self.base_time

        if "-m=" in request:
            mode_string = request.split("-m=")[1].split(" ")[0]
            if mode_string not in self.modes:
                raise ValueError(f"Mode must be in {self.modes}.")
            mode = self.modes.index(mode_string)
        else:
            mode = self.base_mode

        return timer, mode
    
    def handle_client(self, client_socket, client_address):
        client_id = f"{client_address[0]}:{client_address[1]}"
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Accepted connection from {client_address[0]}:{client_address[1]}")
        
        with self.lock:
            self._clients[client_id] = {
                "monitor": {},
                "monitors_count": 0
            }
        try:
            while self.running:
                try:
                    request = client_socket.recv(1024).decode("utf-8")
                    # Caso não haja requisição, encerra a conexão
                    if not request:
                        break

                    # Separa a requisição por espaços
                    req = request.strip(" ")

                    # Comandos fixos sem parâmetros
                    if request.lower() == "/exit":
                        client_socket.send("Connection ended".encode("utf-8"))
                        break

                    elif request.lower() == "/monitors":
                        with self.lock:
                            client_monitors = self._clients.get(client_id, {}).get("monitor", {})
                            if not client_monitors:
                                client_socket.send("No active monitors.".encode("utf-8"))
                                continue
                                
                            monitors_list = [
                                f" - {id}: {info['type']} in '{self.modes[info['mode']]}' mode"
                                for id, info in client_monitors.items()
                            ]
                            response = "Active monitors:\n" + "\n".join(monitors_list)
                            client_socket.send(response.encode("utf-8"))
                    
                    elif request.lower() == "/help":
                        help_msg = self.help()
                        client_socket.send(help_msg.encode("utf-8"))
                        continue
                    
                    elif req.lower().startswith("/cpu") or req.lower().startswith("/mem"):
                        is_cpu = req.lower().startswith("/cpu")
                        monitor_type = "CPU" if is_cpu else "Memory"
                        target_func = self.cpu if is_cpu else self.mem

                        try:
                            timer, mode = self._validate_and_format_request(req)
                        except ValueError as e:
                            client_socket.send(f"Error: {e}".encode("utf-8"))
                            continue

                        stop_event = threading.Event()
                        thread_args = (client_socket, timer, mode)
                        thread = self.create_thread(
                            target=target_func, 
                            args=thread_args,
                            stop_event=stop_event
                        )

                        with self.lock:
                            client_data = self._clients[client_id]
                            task_id = f"{client_data["monitors_count"]}"
                            client_data["monitors_count"] += 1

                            client_data["monitor"][task_id] = {
                                "thread": thread,
                                "stop_event": stop_event,
                                "type": monitor_type,
                                "mode": mode
                            }

                        print(f"Starting {monitor_type} monitoring ({task_id}) for {client_id}")
                        client_socket.send(f"{monitor_type} monitoring started with ID: {task_id}".encode("utf-8"))
                        
                    elif req.lower().startswith("/quit"):
                        try:
                            task_id_to_quit = req.split(" ")[1]
                        except IndexError:
                            client_socket.send("Error: Please specify a monitor ID to quit.".encode("utf-8"))
                            continue
                        
                        with self.lock:
                            monitor_to_quit = self._clients.get(client_id, {}).get("monitor", {}).get(task_id_to_quit)
                            if monitor_to_quit:
                                monitor_to_quit["stop_event"].set()
                                del self._clients[client_id]["monitor"][task_id_to_quit]
                                client_socket.send(f"Monitor {task_id_to_quit} stopped.".encode("utf-8"))
                                print(f"Stopped monitoring ({task_id_to_quit}) for {client_id}")
                            else:
                                client_socket.send(f"Error: Monitor ID '{task_id_to_quit}' not found.".encode("utf-8"))

                    else:
                        client_socket.send("Unknown command. Use /help to see available commands.".encode("utf-8"))
                        continue

                except Exception as e:
                    print(f"Error handling client {client_address}: {e}")
                    break
        finally:
            print(f"Cleaning up thread and memory for {client_id}")
            with self.lock:
                if client_id in self._clients:
                    for task_id, monitor_info in self._clients[client_id]["monitor"].items():
                        monitor_info["stop_event"].set()
                        print(f"Stop signal for {task_id} from client {client_id}")
                    del self._clients[client_id]

        client_socket.close()
        print(f"Connection to {client_address} closed")

    def mem(self, client_socket, seconds, mode, stop_event):
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

    def cpu(self, client_socket, seconds, mode, stop_event):
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
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        host = (self.host, self.port)
        self._server.bind(host)
        self._server.listen(self.connection_limits)
        print("Server started")
        print(f"Listening on {host[0]}:{host[1]}...")

        while self.running:
            try:
                client_socket, client_address = self._server.accept()
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