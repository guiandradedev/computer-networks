import threading
import time
from ClientManager import ClientManager
from ServerManager import ServerManager

def test_server():
    """Função para executar o servidor em uma thread separada"""
    try:
        server = ServerManager(host='127.0.0.1', port=8001)
        print("Starting server...")
        server.start(target_function=handle_client)
        
        # Simula aceitar uma conexão (você precisará implementar isso no ServerManager)
        # server.accept_connections()
        
    except Exception as e:
        print(f"Server error: {e}")

def test_client():
    """Função para executar o cliente"""
    try:
        # Aguarda um pouco para o servidor iniciar
        time.sleep(1)
        
        print("Starting client...")
        client = ClientManager(host='127.0.0.1', port=8001)
        
        # Conecta ao servidor
        if client.connect():
            print("Client connected successfully!")
            
            # Envia algumas mensagens de teste
            test_messages = [
                "Hello Server!",
                "Test message 1",
                "Test message 2",
                "/exit"
            ]
            
            for msg in test_messages:
                print(f"Sending: {msg}")
                client.send_data(msg)
                time.sleep(0.5)
                
                # Tenta receber resposta
                response = client.receive_data()
                if response:
                    print(f"Received: {response.decode('utf-8')}")
                
                if msg == "/exit":
                    break
            
            client.close()
            
        else:
            print("Failed to connect to server")
            
    except Exception as e:
        print(f"Client error: {e}")

def run_test():
    """Executa o teste completo"""
    print("=== Starting Network Test ===")
    
    # Inicia servidor em thread separada
    server_thread = threading.Thread(target=test_server, daemon=True)
    server_thread.start()
    
    # Inicia cliente na thread principal
    test_client()
    
    print("=== Test completed ===")


def handle_client(address, client):
    print(address, client)

if __name__ == "__main__":
    try:
        run_test()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test failed: {e}")