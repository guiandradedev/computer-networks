# Computer Networks - System Monitor

Este projeto implementa um sistema cliente-servidor para monitoramento remoto de recursos do sistema (CPU e memória) via sockets TCP, conforme especificação prática da disciplina de Redes de Computadores do 6 período de Engenharia de Computação pela PUC Campinas.

## Funcionalidades

- Monitoramento remoto de CPU e memória de máquinas clientes.
- Comunicação via sockets TCP.
- Suporte a múltiplos clientes conectados simultaneamente.
- Modos de monitoramento: básico e avançado.
- Comandos para iniciar/parar monitoramento, listar monitores ativos e encerrar conexões.

## Como executar

### Requisitos

- Python 3.8+
- Instale as dependências:
	```bash
	pip install -r requirements.txt
	```

### Iniciando o servidor

```bash
python3 server.py
```

### Iniciando o cliente

```bash
python3 client.py
```

## Comandos disponíveis no cliente

- `/help` — Mostra a lista de comandos.
- `/exit` — Encerra a conexão.
- `/cpu -t=<segundos> -m=<modo>` — Inicia monitoramento da CPU.
- `/mem -t=<segundos> -m=<modo>` — Inicia monitoramento da memória.
- `/quit <id>` — Para um monitoramento ativo.
- `/monitors` — Lista todos os monitoramentos ativos.

## Estrutura do Projeto

- `server.py` — Lógica principal do servidor.
- `client.py` — Lógica principal do cliente.
- `ServerManager.py`, `ClientManager.py`, `ConnectionManager.py` — Gerenciamento de conexões.
- `Colors.py` — Saída colorida no terminal.
- `requirements.txt` — Dependências do projeto.
# Redes de Computadores