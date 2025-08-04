import requests
import os
from urllib.parse import urljoin
from dotenv import load_dotenv


def cadastre_produto(callback_url, produtos, logger):
    token = obtenha_auth_token(callback_url, logger)
    if not token:
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    resposta = requests.post(
        f"{callback_url}/produto",
        json=produtos,
        headers=headers
    )

    logger.info(f"Enviando produtos para {callback_url}/produto")

    if resposta.status_code == 201:
        logger.info("Produtos enviados com sucesso.")
    else:
        logger.error(f"Erro ao enviar produtos: {resposta.status_code} - {resposta.text}")


def obtenha_auth_token(callback_url, logger):
    load_dotenv()  # Carrega variáveis de ambiente do arquivo .env

    # ussername e senha criados em /oauth/signup
    USERNAME = os.getenv("USERNAME_COTEFACIL", "")
    PASSWORD = os.getenv("PASSWORD_COTEFACIL", "")

    url = urljoin(callback_url, "/oauth/token")
    data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    resposta = requests.post(url, data=data, headers=headers)

    if resposta.status_code == 200:
        logger.info("Token de acesso obtido com sucesso.")
        return resposta.json().get("access_token")
    else:
        logger.error("Erro ao autenticar no callback")
        return None