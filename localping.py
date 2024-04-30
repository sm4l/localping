import scapy.all as scapy
import json
import paho.mqtt.client as mqtt
import time

def generate_ip_list(network):
    ip_list = []
    network_prefix = ".".join(network.split(".")[:-1])  # Remove a parte final do endereço IP
    for i in range(1, 255):  # Gerar IPs de 1 a 254 no último octeto
        ip_list.append(network_prefix + "." + str(i))
    return ip_list

def scan_network(network):
    arp_request = scapy.ARP(pdst=network)
    broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
    arp_request_broadcast = broadcast/arp_request
    answered_list, _ = scapy.srp(arp_request_broadcast, timeout=1, verbose=False)

    devices_list = []
    for element in answered_list:
        success = 1
        device_dict = {"ip": element[1].psrc, "mac": element[1].hwsrc, "success": success}
        devices_list.append(device_dict)
    
    return devices_list

def publish_mqtt(devices_list):
    client = mqtt.Client()
    client.connect("aerisiot.com")
    client.publish("test/ping", json.dumps(devices_list))
    client.disconnect()

def main():
    networks = ["172.16.20.0/21", "172.16.21.0/21"]  # Adicionando ambas as redes
    while True:
        all_devices = []
        for network in networks:
            devices = scan_network(network)
            all_devices.extend(devices)
        publish_mqtt(all_devices)
        print("Varredura concluída. Esperando 1 minuto para a próxima varredura...")
        time.sleep(60)  # Espera 1 minuto antes de executar a próxima varredura

if __name__ == "__main__":
    main()
