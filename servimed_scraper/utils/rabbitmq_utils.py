import pika
import json

def enviar_para_fila(queue_name, mensagem):
    conexao = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    canal = conexao.channel()
    canal.queue_declare(queue=queue_name)
    canal.basic_publish(exchange="", routing_key=queue_name, body=json.dumps(mensagem))
    conexao.close()