import subprocess
import paho.mqtt.client as mqtt
import json
import time

# Configurações do MQTT
broker_address = "aerisiot.com"  # Endereço do broker MQTT
topic = "test/services"  # Tópico MQTT

# Função para verificar o status de um serviço
def check_service_status(service):
    try:
        # Verifica o status do serviço usando o comando systemctl status
        output = subprocess.check_output(["systemctl", "status", service]).decode("utf-8")
        if "Active: active (running)" in output:
            return "ON"
        else:
            return "OFF"
    except Exception as e:
        return "OFF"

# Função de callback para quando a conexão ao broker MQTT for estabelecida
def on_connect(client, userdata, flags, rc):
    print("Conectado ao broker MQTT com código de resultado: " + str(rc))

# Função para enviar o status dos serviços via MQTT em um único JSON
def send_service_status(services):
    payload = json.dumps(services)
    client.publish(topic, payload)

# Configuração e inicialização do cliente MQTT
client = mqtt.Client()
client.on_connect = on_connect
client.connect(broker_address)

# Lista de serviços a serem monitorados
services = ["readings", "timeseries", "mariadb", "status", "decoder"]  # Adicione aqui os serviços que deseja monitorar

try:
    while True:
        services_status = {}
        for service in services:
            status = check_service_status(service)
            services_status[service] = status
            print(f"{service} está {status}")
        send_service_status(services_status)
        time.sleep(60)  # Aguarda 60 segundos antes de verificar novamente
except KeyboardInterrupt:
    print("Encerrando o monitoramento.")
    client.disconnect()
