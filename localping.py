import scapy.all as scapy
import json
import re
import paho.mqtt.client as mqtt
import time

def load_mac_vendors():
    with open("mac-vendors-export.json", "r") as f:
        return json.load(f)

def get_mac_vendor(mac, mac_vendors):
    mac_prefix = mac.replace(":", "").upper()[:6]  # Pegando os primeiros 6 caracteres do MAC
    for entry in mac_vendors:
        if mac_prefix.startswith(entry["macPrefix"].replace(":", "").upper()):
            return entry["vendorName"]
    return "UNK"

def generate_ip_list(network):
    ip_list = []
    network_prefix = ".".join(network.split(".")[:-1])  # Remove a parte final do endereço IP
    for i in range(1, 255):  # Gerar IPs de 1 a 254 no último octeto
        ip_list.append(network_prefix + "." + str(i))
    return ip_list

def scan_network(network):
    mac_vendors = load_mac_vendors()
    arp_request = scapy.ARP(pdst=network)
    broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
    arp_request_broadcast = broadcast/arp_request
    answered_list, _ = scapy.srp(arp_request_broadcast, timeout=1, verbose=False)

    devices_list = []
    for element in answered_list:
        success = 1
        device_dict = {"ip": element[1].psrc, "mac": element[1].hwsrc, "success": success}
        device_dict["vendor"] = get_mac_vendor(device_dict["mac"], mac_vendors) if device_dict["mac"] else "unk"
        devices_list.append(device_dict)
    
    # Adicionando dados para IPs sem resposta (sucesso 0)
    ips_scanned = [element[1].psrc for element in answered_list]
    for ip in generate_ip_list(network):
        if ip not in ips_scanned:
            device_dict = {"ip": ip, "mac":"XX", "success": 0, "vendor": "XX"}
            devices_list.append(device_dict)
    
    return devices_list

def publish_mqtt(devices_list):
    client = mqtt.Client()
    client.connect("aerisiot.com")
    client.publish("test/ping", json.dumps(devices_list))
    client.disconnect()

def main():
    networks = ["172.16.21.0/24"]
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
