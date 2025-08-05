import pika
import json
import os
from dotenv import load_dotenv

load_dotenv()  # Carrega variáveis de ambiente do arquivo .env

mensagem = {
    "usuario": os.getenv("USUARIO_SERVIMED", ""),
    "senha": os.getenv("SENHA_SERVIMED", ""),
    "callback_url": "https://desafio.cotefacil.net"
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
