import scrapy
import json

from servimed_scraper.utils.auth_accesstoken import extraia_access_token_dos_cookies, decode_jwt_token
from servimed_scraper.utils.payload_carrinho import obtenha_body_carrinho
from servimed_scraper.callback.api_cotefacil import cadastre_produto


class ServimedProdutosSpider(scrapy.Spider):
    name = "servimed_produtos"

    def __init__(self, usuario=None, senha=None, filtro="", callback_url="https://desafio.cotefacil.net", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario = usuario
        self.senha = senha
        self.filtro = filtro
        self.callback_url = callback_url
        self.produtos_coletados = []

    def start_requests(self):
        url = "https://peapi.servimed.com.br/api/usuario/login"
        payload = {
            "usuario": self.usuario,
            "senha": self.senha
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0",
            "Origin": "https://pedidoeletronico.servimed.com.br",
            "Referer": "https://pedidoeletronico.servimed.com.br/"
        }

        yield scrapy.Request(
            url=url,
            method="POST",
            headers=headers,
            body=json.dumps(payload),
            callback=self.after_login,
            dont_filter=True
        )

    def after_login(self, response):
        try:
            login_data = json.loads(response.text)
        except Exception as e:
            self.logger.error(f"Erro ao decodificar JSON de login: {e}")
            return

        if "usuario" not in login_data:
            self.logger.error("Login falhou ou resposta inesperada.")
            self.logger.info(f"Resposta completa: {response.text}")
            return

        cookie_dict = extraia_access_token_dos_cookies(response.headers.getlist("Set-Cookie"))
        raw_token = cookie_dict.get("accesstoken")
        session_token = cookie_dict.get("sessiontoken")

        if not raw_token or not session_token:
            self.logger.warning("Tokens não encontrados. Verifique headers.")
            return

        access_token = decode_jwt_token(raw_token, self.logger)
        if not access_token:
            return

        self.logger.info(f"Accesstoken extraído e decodificado com sucesso")

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "accesstoken": access_token,
            "sessiontoken": session_token,
            "origin": "https://pedidoeletronico.servimed.com.br",
            "referer": "https://pedidoeletronico.servimed.com.br/",
            "user-agent": "Mozilla/5.0"
        }

        self.logger.info("-" * 30)
        self.logger.info(f"Filtro: {self.filtro}")
        self.logger.info("-" * 30)

        body = obtenha_body_carrinho(login_data=login_data, filtro=self.filtro)
        url = "https://peapi.servimed.com.br/api/carrinho/oculto?siteVersion=4.0.27"

        yield scrapy.Request(
            url=url,
            method="POST",
            headers=headers,
            cookies=cookie_dict,
            body=json.dumps(body),
            callback=self.parse_response
        )

    def parse_response(self, response):
        try:
            data = response.json()
        except Exception as e:
            self.logger.error(f"Erro ao decodificar JSON: {e}")
            return

        for item in data.get("lista", []):
            produto = {
                "descricao": str(item.get("descricao")),
                "gtin": str(item.get("codigoBarras")),
                "codigo": str(item.get("codigoExterno")),
                "preco_fabrica": item.get("valorComDesconto"),
                "estoque": item.get("quantidadeEstoque")
            }
            self.produtos_coletados.append(produto)
            yield produto

    def close(self, reason):
        if self.produtos_coletados:
            self.logger.info(f"Total de produtos coletados: {len(self.produtos_coletados)}")

            self.logger.info("-" * 50)
            self.logger.info(f"Produtos coletados: \n{self.produtos_coletados}")
            self.logger.info("-" * 50)

            self.logger.info("Enviando callback para API da Cotefácil...")
            if self.callback_url:
                cadastre_produto(self.callback_url, self.produtos_coletados, self.logger)
        else:
            self.logger.warning("Nenhum produto foi coletado.")
