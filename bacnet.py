import paho.mqtt.client as mqtt
import json
import mysql.connector
import time
import logging

# Configurações do MQTT
MQTT_BROKER_ADDRESS = "aerisiot.com"
MQTT_TOPIC = "+/update/sensor/BACNET"

# Configurações do banco de dados MySQL
MYSQL_HOST = "localhost"
MYSQL_USER = "seu_usuario_mysql"
MYSQL_PASSWORD = "sua_senha_mysql"
MYSQL_DB_NAME = "mendes"
MYSQL_BACNET_TABLE_NAME = "bacnet"

# Configurações de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")

# Cache para armazenar os dados recentes
recent_data_cache = {}

# Função de callback para quando a conexão com o MQTT é estabelecida
def on_connect(client, userdata, flags, rc):
    logging.info("Conectado ao broker MQTT com sucesso.")
    client.subscribe(MQTT_TOPIC)

# Função de callback para quando uma mensagem do MQTT é recebida
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        topic = msg.topic

        # Check if the topic is the expected one
        if "BACNET" in topic:
            # Criação de um identificador único para o dado recebido baseado em seus valores
            unique_id = (topic, payload.get("Panel"), payload.get("cmdstatus"), payload.get("cmdnumber"), 
                         payload.get("eventName"), payload.get("laco"), payload.get("endereco"), 
                         payload.get("dispositivo"), payload.get("analogue"), payload.get("Texto"))

            # Verifica se os dados recebidos são iguais aos dados armazenados no cache
            if unique_id in recent_data_cache:
                cached_data = recent_data_cache[unique_id]
                if cached_data != payload:
                    # Atualiza o cache com os novos dados
                    recent_data_cache[unique_id] = payload

                    # Atualizar o timestamp do registro existente no banco de dados
                    connection = mysql.connector.connect(
                        host=MYSQL_HOST,
                        user=MYSQL_USER,
                        password=MYSQL_PASSWORD,
                        database=MYSQL_DB_NAME
                    )
                    cursor = connection.cursor()

                    update_query = """
                    UPDATE {} SET timestamp=%s WHERE topic=%s AND panel=%s AND cmdstatus=%s AND cmdnumber=%s 
                    AND eventName=%s AND laco=%s AND endereco=%s AND dispositivo=%s AND analogue=%s AND Texto=%s
                    """.format(MYSQL_BACNET_TABLE_NAME)
                    update_data = (
                        payload.get("ts"), topic, payload.get("Panel"), payload.get("cmdstatus"), 
                        payload.get("cmdnumber"), payload.get("eventName"), payload.get("laco"), 
                        payload.get("endereco"), payload.get("dispositivo"), payload.get("analogue"), 
                        payload.get("Texto")
                    )
                    cursor.execute(update_query, update_data)
                    connection.commit()

                    cursor.close()
                    connection.close()
                    logging.info("Timestamp atualizado com sucesso.")
                else:
                    logging.info("Dados recebidos são iguais aos dados recentes. Nenhuma atualização necessária.")
            else:
                # Atualiza o cache com os novos dados
                recent_data_cache[unique_id] = payload

                # Inserir novos dados na tabela bacnet
                connection = mysql.connector.connect(
                    host=MYSQL_HOST,
                    user=MYSQL_USER,
                    password=MYSQL_PASSWORD,
                    database=MYSQL_DB_NAME
                )
                cursor = connection.cursor()

                insert_query = """
                INSERT INTO {} (topic, panel, cmdstatus, cmdnumber, eventName, laco, endereco, dispositivo, analogue, Texto, timestamp) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """.format(MYSQL_BACNET_TABLE_NAME)
                insert_data = (
                    topic, payload.get("Panel"), payload.get("cmdstatus"), payload.get("cmdnumber"), 
                    payload.get("eventName"), payload.get("laco"), payload.get("endereco"), 
                    payload.get("dispositivo"), payload.get("analogue"), payload.get("Texto"), 
                    payload.get("ts")
                )
                cursor.execute(insert_query, insert_data)
                connection.commit()

                cursor.close()
                connection.close()
                logging.info("Dados inseridos com sucesso.")
        else:
            logging.info("Skipped processing data from topic:", topic)
    except Exception as e:
        logging.error("Erro ao processar dados:", e)

# Configurar o cliente MQTT
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# Conectar ao broker MQTT
client.connect(MQTT_BROKER_ADDRESS, 1883, 60)

# Iniciar o loop para ficar escutando mensagens
client.loop_start()

# Manter o script rodando
while True:
    time.sleep(1)
