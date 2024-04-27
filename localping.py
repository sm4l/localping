import paho.mqtt.client as mqtt
import json
import time
import mysql.connector

# Configuração MQTT
mqtt_config = {
    'broker': 'aerisiot.com',
    'port': 1883,
    'topic': 'test/ping'
}

# Configuração MySQL
mysql_config = {
    'host': 'localhost',
    'user': 'seu_usuario_mysql',
    'password': 'sua_senha_mysql',
    'database': 'mendes'
}

# Lista de sub-redes
subredes = ['172.16.20', '172.16.21']

# Carregar o arquivo JSON de fabricantes
with open('mac-vendors-export.json', 'r') as f:
    fabricantes = json.load(f)

# Função para processar o ping recebido
def processar_ping(ping):
    # 3.5. Criar um timestamp int epoch
    timestamp = int(time.time())

    # Buscar o MAC address no JSON e completar com o fabricante
    mac = ping.get('mac')
    if mac:
        fabricante = consultar_fabricante(mac)
    else:
        fabricante = 'unk'

    # Obter o IP e o sucesso do ping
    ip = ping.get('ip')
    success = ping.get('success', 0)

    # Consultar a tabela ping do banco de dados e atualizar os valores
    atualizar_registro(ip, success, mac, fabricante, timestamp)

    # Imprimir os valores processados
   # print("IP:", ip)
   # print("Success:", success)
   # print("MAC:", mac)
   # print("Fabricante:", fabricante)
   # print("Timestamp:", timestamp)

# Função para consultar o fabricante com base no MAC address
def consultar_fabricante(mac):
    # Extrair o prefixo MAC
    prefixo_mac = mac[:8].upper().replace(':', '')

    # Procurar o fabricante com base no prefixo MAC
    for fabricante in fabricantes:
        if fabricante['macPrefix'].replace(':', '') == prefixo_mac:
            return fabricante['vendorName']

    # Se o fabricante não for encontrado, retornar 'unk'
    return 'unk'

# Função para atualizar o registro no banco de dados
def atualizar_registro(ip, success, mac, fabricante, timestamp):
    try:
        # Conectar ao banco de dados MySQL
        connection = mysql.connector.connect(
            host=mysql_config['host'],
            user=mysql_config['user'],
            password=mysql_config['password'],
            database=mysql_config['database']
        )

        cursor = connection.cursor()

        # Consultar se o IP já existe na tabela ping
        cursor.execute("SELECT * FROM ping WHERE ip = %s", (ip,))
        resultado = cursor.fetchone()

        if resultado:
            # Atualizar registro existente
            cursor.execute("UPDATE ping SET sucesso = %s, mac_address = %s, fabricante = %s, timestamp = %s WHERE ip = %s",
                        (success, mac, fabricante, timestamp, ip))
        else:
            # Inserir novo registro
            cursor.execute("INSERT INTO ping (ip, sucesso, mac_address, fabricante, timestamp) VALUES (%s, %s, %s, %s, %s)",
                        (ip, success, mac, fabricante, timestamp))
            print(f"Adicionado IP {ip} com sucesso {success} na tabela.")

        # Commit das alterações
        connection.commit()

    except mysql.connector.Error as error:
        print("Erro ao conectar ao banco de dados MySQL:", error)

    finally:
        if (connection.is_connected()):
            cursor.close()
            connection.close()
            print("Conexão ao banco de dados MySQL encerrada.")

# Função para consultar os IPs com sucesso 1 no banco de dados
def consultar_ips_sucesso():
    try:
        # Conectar ao banco de dados MySQL
        connection = mysql.connector.connect(
            host=mysql_config['host'],
            user=mysql_config['user'],
            password=mysql_config['password'],
            database=mysql_config['database']
        )

        cursor = connection.cursor()

        # Consultar os IPs com sucesso 1 na tabela ping
        cursor.execute("SELECT ip FROM ping WHERE sucesso = 1")
        ips_sucesso = [result[0] for result in cursor.fetchall()]

        return ips_sucesso

    except mysql.connector.Error as error:
        print("Erro ao conectar ao banco de dados MySQL:", error)
        return []

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("Conexão ao banco de dados MySQL encerrada.")

# Função para completar a lista de IPs com sucesso 0
def completar_ips_sem_sucesso(ips_sucesso):
    for subrede in subredes:
        for i in range(256):
            ip = f'{subrede}.{i}'
            if ip not in ips_sucesso:
                # Se o IP não estiver na lista de IPs com sucesso, definir sucesso como 0
                processar_ping({'ip': ip, 'success': 0})

# Callback para quando a conexão MQTT for estabelecida
def on_connect(client, userdata, flags, rc):
    print("Conectado com código de resultado: "+str(rc))
    # Subscrever ao tópico
    client.subscribe(mqtt_config['topic'])

# Callback para quando uma nova mensagem MQTT for recebida
def on_message(client, userdata, msg):
    print("Mensagem recebida no tópico "+msg.topic+": "+str(msg.payload.decode('utf-8')))
    # Decodificar a mensagem JSON
    pings = json.loads(msg.payload.decode('utf-8'))
    
    # Verificar se a mensagem é uma lista
    if isinstance(pings, list):
        # Iterar sobre cada objeto JSON na lista
        for ping in pings:
            # Processar cada ping individualmente
            processar_ping(ping)
    else:
        # Se não for uma lista, processar o ping como único
        processar_ping(pings)

# Criar um cliente MQTT
client = mqtt.Client()

# Configurar os callbacks
client.on_connect = on_connect
client.on_message = on_message

# Conectar ao broker MQTT
client.connect(mqtt_config['broker'], mqtt_config['port'], 60)

# No início do script, antes de entrar no loop MQTT, obtemos os IPs com sucesso 1
ips_sucesso = consultar_ips_sucesso()
# Completamos a lista de IPs com sucesso 0
completar_ips_sem_sucesso(ips_sucesso)

# Manter a conexão MQTT ativa
client.loop_forever()
