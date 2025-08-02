import scrapy
import json
from get_token import get_auth_headers
from dotenv import load_dotenv
import os


class ServimedSpider(scrapy.Spider):
    name = "servimed_oculto"

    def start_requests(self):
        # Carrega as variáveis do .env
        load_dotenv()
        
        username = os.getenv("USERNAME_SERVIMED")
        password = os.getenv("PASSWORD_SERVIMED")

        # Captura os headers via Selenium
        # headers = get_auth_headers(username, password)
        
        with open("auth_headers.json", "r") as file:
            headers = json.load(file)

        # Converte cookies de string para dicionário
        cookie_str = headers.pop("cookie", "")
        cookies = dict(pair.split("=", 1) for pair in cookie_str.split("; ") if "=" in pair)

        url = "https://peapi.servimed.com.br/api/carrinho/oculto?siteVersion=4.0.27"
        body = {
            "filtro": "dipirona",
            "pagina": 1,
            "registrosPorPagina": 20,
            "ordenarDecrescente": False,
            "colunaOrdenacao": "nenhuma",
            "clienteId": 267511,
            "tipoVendaId": 1,
            "fabricanteIdFiltro": 0,
            "pIIdFiltro": 0,
            "cestaPPFiltro": False,
            "codigoExterno": 0,
            "codigoUsuario": 22850,
            "promocaoSelecionada": "",
            "indicadorTipoUsuario": "CLI",
            "kindUser": 0,
            "xlsx": [],
            "principioAtivo": "",
            "master": False,
            "kindSeller": 0,
            "grupoEconomico": "",
            "users": [518565, 267511],
            "list": True
        }

        yield scrapy.Request(
            url=url,
            method="POST",
            headers=headers,
            cookies=cookies,
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
            yield {
                "descricao": item.get("descricao"),
                "gtin": item.get("codigoBarras"),
                "codigo": item.get("codigoExterno"),
                "preco_fabrica": item.get("valorComDesconto"),
                "estoque": item.get("quantidadeEstoque")
                }
