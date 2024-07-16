import scapy.all as scapy
import mysql.connector
import time
import datetime
import json
import paho.mqtt.client as mqtt

# Função para carregar os dados dos fabricantes de um arquivo JSON
def load_mac_vendors(filename):
    with open(filename, 'r') as file:
        mac_vendors = json.load(file)
    return mac_vendors

# Função para encontrar o fabricante com base no prefixo MAC
def find_vendor(mac, mac_vendors):
    prefix = mac[:8].upper()
    for vendor in mac_vendors:
        if vendor['macPrefix'].upper() == prefix:
            return vendor['vendorName']
    return 'Unknown'

def generate_ip_list(network):
    ip_list = []
    network_prefix = ".".join(network.split(".")[:-1])  # Remove a parte final do endereço IP
    for i in range(1, 255):  # Gerar IPs de 1 a 254 no último octeto
        ip_list.append(network_prefix + "." + str(i))
    return ip_list

def scan_ip(ip):
    arp_request = scapy.ARP(pdst=ip)
    broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
    arp_request_broadcast = broadcast/arp_request
    answered_list, _ = scapy.srp(arp_request_broadcast, timeout=1, verbose=False)

    device_dict = {}
    if answered_list:
        device_dict = {"ip": ip, "mac": answered_list[0][1].hwsrc, "success": 1}
    else:
        device_dict = {"ip": ip, "mac": "Unknown", "success": 0}

    return device_dict

def save_to_db(devices_list, db_config, mac_vendors):
    connection = mysql.connector.connect(
        host=db_config['host'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['database']
    )
    cursor = connection.cursor()

    for device in devices_list:
        timestamp = int(time.time())
        fabricante = find_vendor(device['mac'], mac_vendors)
        sql = "INSERT INTO ping (ip, sucesso, mac_address, fabricante, timestamp) VALUES (%s, %s, %s, %s, %s)"
        values = (device["ip"], device["success"], device["mac"], fabricante, timestamp)
        cursor.execute(sql, values)

    connection.commit()
    cursor.close()
    connection.close()

def publish_to_mqtt(devices_list):
    broker = "aerisiot.com"
    topic = "test/ping"
    client = mqtt.Client()
    client.connect(broker)
    client.loop_start()

    # Filtrar apenas os dispositivos com success = 1
    successful_devices = [device for device in devices_list if device['success'] == 1]

    if successful_devices:
        payload = json.dumps(successful_devices)
        client.publish(topic, payload)

    client.loop_stop()
    client.disconnect()

def main():
    networks = ["172.16.20.0/21", "172.16.21.0/21"]  # Adicionando ambas as redes
    db_config = {
        'host': 'localhost',
        'user': 'seu_usuario_mysql',
        'password': 'sua_senha_mysql',
        'database': 'mendes'
    }
    mac_vendors = load_mac_vendors('mac-vendors-export.json')
    
    while True:
        all_devices = []
        for network in networks:
            ip_list = generate_ip_list(network)
            for ip in ip_list:
                device = scan_ip(ip)
                all_devices.append(device)
        save_to_db(all_devices, db_config, mac_vendors)
        publish_to_mqtt(all_devices)
        agora = datetime.datetime.now()
        print(str(agora) + " Varredura concluída. Esperando 1 minuto para a próxima varredura...")
        time.sleep(60)  # Espera 1 minuto antes de executar a próxima varredura

if __name__ == "__main__":
    main()
