import threading
import time
import psutil
from datetime import datetime
from typing import Literal
import json
from ServerManager import ServerManager
from Colors import Colors

class Server:
    """
    Classe principal do servidor, responsável por gerenciar conexões, comandos e monitoramentos.
    """
    def __init__(self, host='0.0.0.0', port=8000):
        # Inicializa o servidor com host, porta e variáveis de controle
        self._clients = {}  # dicionário para armazenar informações dos clientes e suas threads/monitors ativas
        self.lock = threading.Lock()

        self.modes = ["basic", "advanced"]
        self.timer = 10
        self.mode = 0

        self.manager = ServerManager(connection_limits=1)

    def send_message(self, client_socket, message, status: Literal["info", "warning", "error", "success"]):
        """
        Padroniza o formato de envio de mensagens JSON para o socket.

        :param client_socket: O socket do cliente.
        :type client_socket: socket.socket
        :param message: A mensagem a ser enviada.
        :type message: str
        :param status: O status da mensagem ('info', 'warning', 'error', 'success').
        :type status: str
        """
        if status not in {"info", "warning", "error", "success"}:
            raise ValueError("status must be 'info', 'warning', 'error' or 'success'")

        try:
            response = json.dumps({"status": status, "message": message})
            self.manager.send_data(response, client_socket)
        except Exception as e:
            Colors.error(f"Error sending message to {client_socket.getpeername()}: {e}")

    def create_thread(self, target, args, stop_event):
        """
        Cria e inicia uma thread para monitoramento.
        """

        # Adiciona o stop_event da thread dentro do argumento da funcão que será executada para poder ser finalizada depois
        full_args = args + (stop_event,)
        
        thread = threading.Thread(target=target, args=full_args)
        thread.daemon = True
        thread.start()
        
        return thread
    

    def help(self):
        """
        Retorna a mensagem de ajuda com os comandos disponíveis.
        """
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
        """
        Valida e extrai os parâmetros de tempo e modo de um comando recebido.

        :param request: O comando recebido do cliente.
        :type request: str
        """
        if "-t=" in request:
            input_timer = request.split("-t=")[1].split(" ")[0]
            if not input_timer.isdigit():
                raise ValueError("Value must be an integer.")
            timer = int(input_timer)
        else:
            timer = self.timer

        if "-m=" in request:
            mode_string = request.split("-m=")[1].split(" ")[0]
            if mode_string not in self.modes:
                raise ValueError(f"Mode must be in {self.modes}.")
            mode = self.modes.index(mode_string)
        else:
            mode = self.mode

        return timer, mode
    
    def monitors(self, client_id, client_socket, client_address):
        """
        Retorna a lista de monitores ativos para o cliente.

        :param client_id: O ID do cliente.
        :type client_id: str
        :param client_socket: O socket do cliente.
        :type client_socket: socket.socket
        :param client_address: O endereço do cliente.
        :type client_address: tuple
        """
        client_monitors = self._clients.get(client_id, {}).get("monitor", {})
        if not client_monitors:
            return False, "No active monitors."
            
        monitors_list = [
            f" - {id}: {info['type']} in '{self.modes[info['mode']]}' mode"
            for id, info in client_monitors.items()
        ]
        response = "Active monitors:\n" + "\n".join(monitors_list)
        return True, response

    
    def handle_client(self, client_socket, client_address):
        """
        Função principal de atendimento ao cliente. Processa comandos e gerencia monitores.

        :param client_socket: O socket do cliente.
        :type client_socket: socket.socket
        :param client_address: O endereço do cliente.
        :type client_address: tuple
        """

        client_id = f"{client_address[0]}:{client_address[1]}"
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Accepted connection from {client_address[0]}:{client_address[1]}")
        self.send_message(client_socket, f"Connected to server at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "info")
        self.send_message(client_socket, self.help(), "info")
        with self.lock:
            self._clients[client_id] = {
                "monitor": {},
                "monitors_count": 0
            }
        try:
            # Loop principal de atendimento ao cliente
            while self.manager.running:
                try:
                    # Recebe comando do cliente
                    data = self.manager.receive_data(client_socket)
                    if not data:
                        # Se não houver comando, encerra a conexão
                        break
                    request = data.decode('utf-8')

                    # Separa a requisição por espaços
                    req = request.strip(" ")  # Remove espaços extras

                    # Comandos fixos sem parâmetros
                    if request.lower() == "/exit":
                        # Encerra a conexão com o cliente
                        self.send_message(client_socket=client_socket, message="Connection ended", status="success")
                        break

                    elif request.lower() == "/monitors":
                        # Lista monitores ativos
                        success, response = self.monitors(client_id, client_socket, client_address)
                        if not success:
                            self.send_message(client_socket, response, "error")
                        else:
                            self.send_message(client_socket, response, "info")
                        continue

                    elif request.lower() == "/help":
                        # Envia mensagem de ajuda
                        self.send_message(client_socket, self.help(), "info")
                        continue
                    
                    elif req.lower().startswith("/cpu") or req.lower().startswith("/mem"):
                        # Inicia monitoramento de CPU ou Memória
                        is_cpu = req.lower().startswith("/cpu")
                        monitor_type = "CPU" if is_cpu else "Memory"
                        target_func = self.cpu if is_cpu else self.mem

                        try:
                            timer, mode = self._validate_and_format_request(req)
                            
                        except ValueError as e:
                            self.send_message(client_socket, e, "error")
                            continue

                        # Cria e inicia thread de monitoramento
                        stop_event = threading.Event()
                        thread_args = (client_socket, timer, mode)
                        thread = self.create_thread(
                            target=target_func, 
                            args=thread_args,
                            stop_event=stop_event
                        )

                        # Registra o monitoramento no dicionário do cliente
                        with self.lock:
                            client_data = self._clients[client_id]
                            task_id = f"{client_data['monitors_count']}"
                            client_data["monitors_count"] += 1

                            client_data["monitor"][task_id] = {
                                "thread": thread,
                                "stop_event": stop_event,
                                "type": monitor_type,
                                "mode": mode
                            }

                        Colors.ok(f"Starting {monitor_type} monitoring ({task_id}) for {client_id}")
                        self.send_message(client_socket, f"{monitor_type} monitoring started with ID: {task_id}", "success")
                        
                    elif req.lower().startswith("/quit"):
                        # Encerra monitoramento específico
                        try:
                            task_id_to_quit = req.split(" ")[1]
                        except IndexError:
                            self.send_message(client_socket, "Please specify a monitor ID to quit.", "error")
                            continue
                        
                        with self.lock:
                            monitor_to_quit = self._clients.get(client_id, {}).get("monitor", {}).get(task_id_to_quit)
                            if monitor_to_quit:
                                # Sinaliza para a thread parar
                                monitor_to_quit["stop_event"].set()
                                del self._clients[client_id]["monitor"][task_id_to_quit]
                                self.send_message(client_socket, f"Stopped monitoring ({task_id_to_quit}) for {client_id}", "success")
                                Colors.success(f"Stopped monitoring ({task_id_to_quit}) for {client_id}")
                            else:
                                self.send_message(message=f"Monitor ID '{task_id_to_quit}' not found.", client_socket=client_socket, status="error")

                    else:
                        # Comando desconhecido
                        self.send_message(client_socket, "Unknown command. Use /help to see available commands.", "error")
                        continue

                except Exception as e:
                    Colors.error(f"Error handling client {client_address}: {Colors.OKBLUE}{e}")
                    break
        finally:
            # Limpeza de recursos ao encerrar o atendimento ao cliente
            Colors.success(f"Cleaning up thread and memory for {client_id}")
            with self.lock:
                if client_id in self._clients:
                    for task_id, monitor_info in self._clients[client_id]["monitor"].items():
                        # Sinaliza para todas as threads de monitoramento pararem
                        monitor_info["stop_event"].set()
                        print(f"Stop signal for {task_id} from client {client_id}")
                    del self._clients[client_id]

        client_socket.close()
        Colors.success(f"Connection to {client_address} closed")

    def mem(self, client_socket, seconds, mode, stop_event):
        """
        Função de monitoramento de memória. Envia informações periodicamente ao cliente.
        
        :param client_socket: O socket do cliente.
        :type client_socket: socket.socket
        :param seconds: Intervalo de tempo entre as verificações.
        :type seconds: int
        :param mode: Modo de operação (0 = básico, 1 = avançado).
        :type mode: int
        :param stop_event: Evento para sinalizar a parada da thread.
        :type stop_event: threading.Event
        """
        while not stop_event.is_set():
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            msg_lines = []
            msg_lines.append(f"💾 Memory Usage: {mem.percent:.1f}%")
            msg_lines.append(f"📊 Available: {mem.available / (1024**3):.2f} GB")
            msg_lines.append(f"📈 Used: {mem.used / (1024**3):.2f} GB")
            msg_lines.append(f"📉 Free: {mem.free / (1024**3):.2f} GB")
            
            if mode == 1:  # advanced
                msg_lines.append(f"🔄 Swap Usage: {swap.percent:.1f}%")
                msg_lines.append(f"↔️ Swap Total: {swap.total / (1024**3):.2f} GB")
                msg_lines.append(f"⬆️ Swap Used: {swap.used / (1024**3):.2f} GB")
                msg_lines.append(f"⬇️ Swap Free: {swap.free / (1024**3):.2f} GB")
                msg_lines.append(f"🧠 Buffers: {getattr(mem, 'buffers', 0) / (1024**2):.2f} MB")
                msg_lines.append(f"🗄️ Cached: {getattr(mem, 'cached', 0) / (1024**2):.2f} MB")
                msg_lines.append(f"🔁 Shared: {getattr(mem, 'shared', 0) / (1024**2):.2f} MB")

            try:
                self.send_message(client_socket, "\n".join(msg_lines), status="info")
            except:
                break

            time.sleep(seconds)

    def cpu(self, client_socket, seconds, mode, stop_event):
        """
        Função de monitoramento de CPU. Envia informações periodicamente ao cliente.

        :param client_socket: O socket do cliente.
        :type client_socket: socket.socket
        :param seconds: Intervalo de tempo entre as verificações.
        :type seconds: int
        :param mode: Modo de operação (0 = básico, 1 = avançado).
        :type mode: int
        :param stop_event: Evento para sinalizar a parada da thread.
        :type stop_event: threading.Event
        """
        while not stop_event.is_set():
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_times_per_core = psutil.cpu_times(percpu=True)
            load_avg = psutil.getloadavg()

            msg_lines = []
            msg_lines.append(f"📊 CPU Usage: {cpu_percent:.1f}%")
            
            if mode == 1:  # advanced
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
                self.send_message(client_socket, "\n".join(msg_lines), status="info")
            except:
                break

            time.sleep(seconds)

    def start(self):
        """
        Inicia o servidor e aceita conexões de clientes.
        """
        self.manager.start(target_function=self.handle_client)

if __name__ == '__main__': 
    server = Server()
    try:
        server.start()
    except KeyboardInterrupt:
        Colors.ok('\nInterrupted')
        server.manager.running = False