import socket
import threading
import time
import psutil

# Comandos possíveis:
# /help
# /exit
# /cpu -t -m # -t=<seconds>; -m=<basic>
# /mem -t -m # -t=<seconds>; -m=<advanced>
# /quit <id> # <id>=<id>

# Flags
# -t=<seconds>; default=10 -> timer in seconds
# -m=<basic/advanced>; default=basic -> mode


# TODO
# - Implementar a função de memória
# - Implementar a escolha dos modos de monitoramento (básico ou avançado)
# - Implementar POO
# - Refatorar código para melhorar legibilidade e manutenção
# - Implementar logs para monitorar atividades
# - Implementar tratamento de erros

# Funcoes helpers
def validate_and_format_request(request, base_timer, base_mode, modes):
    if "-t=" in request:
        input_timer = request.split("-t=")[1].split(" ")[0]
        if not input_timer.isdigit():
            raise ValueError("Value must be an integer.")
        timer = int(input_timer)
    else:
        timer = base_timer


    if "-m=" in request:
        mode_string = request.split("-m=")[1].split(" ")[0]
        if mode_string not in modes:
            raise ValueError(f"Mode must be in {modes}.")
        mode = modes.index(mode_string)
    else:
        mode = base_mode

    return timer, mode


def handle_client(client_socket, client_address):
    print(f"Accepted connection from {client_address[0]}:{client_address[1]}")

    monitors = []
    index_map = {}
    monitor_id = 1

    def add_thread(id_, thread, stop_event, type_, timer, mode):
        monitors.append((id_, thread, stop_event, type_, timer, mode))
        index_map[id_] = len(monitors) - 1

    def get_thread(id_):
        idx = index_map.get(id_)
        return monitors[idx] if idx is not None else None

    def remove_thread(id_):
        idx = index_map.pop(id_, None)
        thread_tuple = monitors[idx] if idx is not None else None
        if idx is not None:
            monitors[idx] = None  # marca como removido
        return thread_tuple

    timer = 10
    mode = 0
    modes = ["basic", "advanced"]

    while True:
        request = client_socket.recv(1024).decode("utf-8")
        if not request:
            break

        if request.lower() == "/exit":
            client_socket.send("Connection ended".encode("utf-8"))
            break
        # Pode ser feito via client, mas existe as duas opções pra facilitar

        if request.lower().startswith("/cpu"):
            try:
                timer, mode = validate_and_format_request(request, timer, mode, modes)
            except ValueError as e:
                client_socket.send(f"Invalid request: {e}".encode("utf-8"))
                continue

            stop_event = threading.Event()
            thread = threading.Thread(target=cpu, args=(client_socket, client_address, timer, mode, stop_event))
            add_thread(monitor_id, thread, stop_event, "cpu", timer, mode)
            thread.daemon = True
            thread.start()
            monitor_id += 1
            continue

        if request.lower().startswith("/mem"):
            try:
                timer, mode = validate_and_format_request(request, timer, mode, modes)
            except ValueError as e:
                client_socket.send(f"Invalid request: {e}".encode("utf-8"))
                continue
            print(f"Starting Memory monitoring with id {monitor_id} for {client_address} every {timer} seconds in {mode} mode.")
            stop_event = threading.Event()
            thread = threading.Thread(target=mem, args=(client_socket, client_address, timer, mode, stop_event))
            add_thread(monitor_id, thread, stop_event, "mem", timer, mode)
            thread.daemon = True
            thread.start()
            monitor_id += 1
            continue

        if request.lower() == "/help":
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
            client_socket.send(help_msg.encode("utf-8"))
            continue

        if request.lower().startswith("/quit"):
            try:
                id_to_remove = int(request.split(" ")[1])
                thread_tuple = remove_thread(id_to_remove)
                if thread_tuple:
                    _, thread_obj, stop_event, _, _, _ = thread_tuple
                    stop_event.set()  # sinaliza para a thread parar
                    client_socket.send(f"Stopped monitoring with id {id_to_remove}".encode("utf-8"))
                else:
                    client_socket.send(f"No monitoring found with id {id_to_remove}".encode("utf-8"))
            except (ValueError, IndexError):
                client_socket.send("Invalid request format. Use /quit <id>".encode("utf-8"))
            continue

        if request.lower() == "/monitors":
            msg = f"You are monitoring {len(monitors)} threads."
            for id in index_map:
                thread_tuple = get_thread(id)
                if thread_tuple:
                    _, _, _, type_, timer, mode = thread_tuple
                    msg += f"\nID: {id}, Type: {type_}, Interval: {timer}s, Mode: {modes[mode]}"
            client_socket.send(msg.encode("utf-8"))
            continue

        print(f"Received from {client_address}: {request}")
        client_socket.send("Error: Invalid command, try use /help to see the list of available commands.".encode("utf-8"))

    client_socket.close()
    print(f"Connection to {client_address} closed")

def mem(client_socket, client_address, seconds, mode):
    print("dasdas")

def cpu(client_socket, client_address, seconds, mode, stop_event):
    while not stop_event.is_set():
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

        try:
            client_socket.send("\n".join(msg_lines).encode("utf-8"))
        except:
            break

        time.sleep(seconds)



def start_server():
    print()
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
