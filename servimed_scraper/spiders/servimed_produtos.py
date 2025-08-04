import scrapy
import json
from dotenv import load_dotenv
import os
import sys
import asyncio
import nest_asyncio


# Adiciona o caminho do projeto ao sys.path para importar corretamente
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# Importa o produtor de RabbitMQ
from rabbitmq_cotefacil.producer import send as producer_send

# Aplica o nest_asyncio para permitir múltiplos loops de eventos
nest_asyncio.apply()


class ServimedProdutosSpider(scrapy.Spider):
    name = "servimed_produtos"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.produtos_coletados = []

    # Garantindo compatibilidade com o Scrapy anterior a 2.13
    def start_requests(self):
        return super().start_requests()

    async def start(self):
        load_dotenv()

        
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Content-Type": "application/json",
            "contenttype": "application/json",
            "cookie": "_gid=GA1.3.1988582023.1754168219; _gat=1; _gat_gtag_UA_149227611_1=1; _ga=GA1.1.1452426544.1754168219; sessiontoken=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJjb2RpZ29Vc3VhcmlvIjoyMjg1MCwidG9rZW4iOiI0MDQ2YjM4MC02ZmUzLTExZjAtYmNiZC1kNTUzOWQ3OTNmODIiLCJpYXQiOjE3NTQxNjgyMjcsImV4cCI6MTc1NDIxMTQyNywiYXVkIjoiaHR0cDovL3NlcnZpbWVkLmNvbS5iciIsImlzcyI6IlNlcnZpbWVkIiwic3ViIjoic2VydmltZWRAU2VydmltZWQuY29tLmJyIn0.OOuWTPwE-q0fQjN7BFnfwGHuuAG0SCFTz7Ap1vQ-LmQuqJggoWQlta-GolSWhBwbqjOnlk_iEi_sEB8B359jzQ; accesstoken=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJjb2RpZ29Vc3VhcmlvIjoyMjg1MCwidG9rZW4iOiI0MDQ2YjM4MC02ZmUzLTExZjAtYmNiZC1kNTUzOWQ3OTNmODIiLCJpYXQiOjE3NTQxNjgyMjcsImV4cCI6MTc1NDIxMTQyNywiYXVkIjoiaHR0cDovL3NlcnZpbWVkLmNvbS5iciIsImlzcyI6IlNlcnZpbWVkIiwic3ViIjoic2VydmltZWRAU2VydmltZWQuY29tLmJyIn0.OOuWTPwE-q0fQjN7BFnfwGHuuAG0SCFTz7Ap1vQ-LmQuqJggoWQlta-GolSWhBwbqjOnlk_iEi_sEB8B359jzQ; _ga_0684EZD6WN=GS2.1.s1754168218$o1$g0$t1754168227$j51$l0$h0",
            "loggeduser": "22850",
            "origin": "https://pedidoeletronico.servimed.com.br",
            "referer": "https://pedidoeletronico.servimed.com.br/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
            "x-cart": "",
            "x-peperone": ""
        }

        headers["accesstoken"] = os.getenv("ACCESS_TOKEN_SERVIMED", headers.get("accesstoken", ""))

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
            produto = {
                "descricao": item.get("descricao"),
                "gtin": item.get("codigoBarras"),
                "codigo": item.get("codigoExterno"),
                "preco_fabrica": item.get("valorComDesconto"),
                "estoque": item.get("quantidadeEstoque")
                }
            
            self.produtos_coletados.append(produto)
            yield produto
            
    def close(self, reason):
        if self.produtos_coletados:
            self.logger.info(f"Total de produtos coletados: {len(self.produtos_coletados)}")
            import nest_asyncio
            nest_asyncio.apply()
            loop = asyncio.get_event_loop()
            self.logger.info("Iniciando envio de produtos para RabbitMQ...")
            loop.run_until_complete(producer_send(self.produtos_coletados, self.logger))
        else:
            self.logger.warning("Nenhum produto foi coletado.")
