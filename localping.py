para completar a lista de IPs com sucesso 0
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

