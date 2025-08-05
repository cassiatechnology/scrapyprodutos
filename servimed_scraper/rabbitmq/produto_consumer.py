import pika
import json
import subprocess
import os
from datetime import datetime


def consumir():
    conexao = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    canal = conexao.channel()

    canal.queue_declare(queue='scraping_jobs')

    print('[*] Aguardando mensagens. Para sair pressione CTRL+C')
    canal.basic_consume(queue='scraping_jobs', on_message_callback=obtenha_lista_de_produtos_scrapy, auto_ack=True)
    canal.start_consuming()


def obtenha_lista_de_produtos_scrapy(ch, method, properties, body):
    print(f"[x] Mensagem recebida.")
    dados = json.loads(body)

    usuario = dados["usuario"]
    senha = dados["senha"]
    callback_url = dados["callback_url"]
    filtro = "277738"  # Nome do produto que deseja consultar

    # Caminho absoluto para a raiz do projeto
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    logs_dir = os.path.join(project_root, "logs")
    os.makedirs(logs_dir, exist_ok=True)

    # Caminho absoluto do arquivo de log
    log_file = os.path.join(logs_dir, f"servimed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

    comando = [
        "scrapy", "crawl", "servimed_produtos",
        "-a", f"usuario={usuario}",
        "-a", f"senha={senha}",
        "-a", f"callback_url={callback_url}",
        "-a", f"filtro={filtro}",
        "-s", f"LOG_FILE={log_file}"
    ]

    print("[+] Obtendo produtos...")
    print(f"Verifique o log de processamento em: {log_file}")
    subprocess.run(comando, check=True)

if __name__ == "__main__":
    consumir()
