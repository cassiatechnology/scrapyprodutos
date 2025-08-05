import pika
import json
import os


with open("parametros.json", "r", encoding="utf-8") as f:
    parametros = json.load(f)

mensagem = {
    "usuario": parametros["usuario"],
    "senha": parametros["senha"],
    "callback_url": parametros["callback_url"],
    "filtro": parametros["filtro"],  # Nome ou código do produto que deseja consultar
}

conexao = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
canal = conexao.channel()
canal.queue_declare(queue='scraping_jobs')

canal.basic_publish(exchange='', 
                    routing_key='scraping_jobs', 
                    body=json.dumps(mensagem)
                    )
print("[x] Tarefa enviada para a fila 'scraping_jobs'")
conexao.close()
