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

        # Carrega os headers de autenticação do arquivo JSON
        with open("auth_headers.json", "r") as file:
            headers = json.load(file)

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
