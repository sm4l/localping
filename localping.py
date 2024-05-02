import scapy.all as scapy
import json
import paho.mqtt.client as mqtt
import time
import datetime

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

def publish_mqtt(devices_list):
    client = mqtt.Client()
    client.connect("aerisiot.com")
    client.publish("test/ping", json.dumps([device for device in devices_list if device["success"] == 1]))
    client.disconnect()


def main():
    networks = ["172.16.20.0/21", "172.16.21.0/21"]  # Adicionando ambas as redes
    while True:
        all_devices = []
        for network in networks:
            ip_list = generate_ip_list(network)
            for ip in ip_list:
                device = scan_ip(ip)
                all_devices.append(device)
        publish_mqtt(all_devices)
        agora = datetime.datetime.now()
        print(str(agora)+ " Varredura concluída. Esperando 1 minuto para a próxima varredura...")
        time.sleep(60)  # Espera 1 minuto antes de executar a próxima varredura

if __name__ == "__main__":
    main()

