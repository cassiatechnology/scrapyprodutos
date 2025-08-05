import scrapy
import json
from servimed_scraper.utils.auth_accesstoken import extraia_access_token_dos_cookies, decode_jwt_token
from servimed_scraper.utils.payload_carrinho import obtenha_body_carrinho
from servimed_scraper.utils.rabbitmq_utils import enviar_para_fila

class ServimedNivel3Spider(scrapy.Spider):
    name = "servimed_nivel3"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # REMOVER ESSA PARTE DEPOIS DE TESTAR --------------------------
        from dotenv import load_dotenv
        import os
        load_dotenv()  # Carrega variáveis de ambiente do arquivo .env

        usuario = os.getenv("USUARIO_SERVIMED", "")
        senha = os.getenv("SENHA_SERVIMED", "")
        callback_url = "https://desafio.cotefacil.net"
        filtro = "277738"  # Nome do produto que deseja consultar

        self.usuario = usuario
        self.senha = senha
        self.filtro = filtro
        self.callback_url = callback_url
        self.produtos_coletados = []
        self.access_token = None
        self.sessiontoken = None
        self.cookie = None
        self.login_data = {}
        self.quantidade = 1  # Quantidade de produtos a serem comprados
        self.produto_encontrado = {}
        # ---------------------------------------------------------------

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

        self.logger.info("*" * 50)
        self.logger.info("[LOGIN] Iniciando processo de login...")
        self.logger.info(f"[LOGIN] URL: {url}")

        self.logger.info(f"[LOGIN] Payload: {payload}")
        self.logger.info(f"[LOGIN] Headers: {headers}")
        self.logger.info("*" * 50)

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
            self.login_data = response.json()
            self.logger.info("*" * 50)
            self.logger.info(f"[LOGIN] self.login_data: {self.login_data}")


            self.logger.info("*" * 50)
            self.logger.info("[LOGIN] Verificando resposta do login...")
            self.logger.info(f"[LOGIN] Status: {response.status}")
            self.logger.info("*" * 50)

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

        self.logger.info(f"Accesstoken extraído e decodificado com sucesso: {access_token}")
        self.access_token = access_token
        self.sessiontoken = session_token

        self.logger.info("*" * 50)
        # Montar cookie no formato "chave=valor; chave=valor; ..."
        cookie_str = "; ".join([f"{k}={v}" for k, v in cookie_dict.items()])
        self.logger.info(f"[LOGIN] COOOOOOOOOOOOOOOOOOOKIIIIIIIIIIIIIIIIIII: ({cookie_str.strip()})")
        self.logger.info("*" * 50)

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

        self.logger.info("[CARRINHO] Obtendo Produtos...")

        self.cookie = cookie_dict

        yield scrapy.Request(
            url=url,
            method="POST",
            headers=headers,
            cookies=cookie_dict,
            body=json.dumps(body),
            callback=self.after_produto
        )

    def after_produto(self, response):
        lista = response.json().get("lista", [])

        self.logger.info("*" * 50)
        self.logger.info(f"[PRODUTO] Status Produtos: {response.status}")
        self.logger.info("*" * 50)
        self.logger.info(f"[PRODUTO] Produtos encontrados: {response.text}")
        self.logger.info("*" * 50)

        if not lista:
            self.logger.error("[PRODUTO] Produto não encontrado!")
            return

        self.produto_encontrado = lista[0]

        self.logger.info("[PEDIDO] Transmitindo pedido...")
        self.logger.info("*" * 100)
        self.logger.info(f"Preenchendo access token ({self.access_token})\n session token ({self.sessiontoken})\ncookie ({self.cookie})")

        self.logger.info("*" * 100)
        url = "https://peapi.servimed.com.br/api/Pedido/TrasmitirPedido"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "accesstoken": self.access_token,
            "sessiontoken": self.sessiontoken
        }
        body = {
            "customerId": self.login_data["usuario"]["users"][1],
            "userCode": self.login_data["usuario"]["codigoUsuario"],
            "daysOfPlots": 28,
            "pieces": ["21", "28", "35"],
            "quantityPlots": 1,
            "sellId": 1,
            "observation": "Pedido via integração Cotefácil",
            "itens": [{
                "id": self.produto_encontrado["codigoExterno"],
                "selectedPromotionID": -1,
                "taxValue": 0,
                "quantityRequested": self.quantidade,
                "baseValue": 0,
                "totalStIvaValue": 0,
                "totalValue": 0,
                "discount": 0,
                "descontos": [],
                "discountValue": 0,
                "stIVA": 0
            }]
        }
        yield scrapy.Request(
            url=url,
            method="POST",
            headers=headers,
            cookies=self.cookie,
            body=json.dumps(body),
            callback=self.after_pedido
        )

    def after_pedido(self, response):
        self.logger.info("[PEDIDO] Obtendo último pedido...")
        url = "https://peapi.servimed.com.br/api/Pedido"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "accesstoken": self.access_token,
            "sessiontoken": self.sessiontoken
        }
        body = {
            "dataInicio": "",
            "dataFim": "",
            "filtro": "",
            "pagina": 1,
            "registrosPorPagina": 1,
            "codigoExterno": self.login_data["usuario"]["codigoExterno"],
            "codigoUsuario": self.login_data["usuario"]["codigoUsuario"],
            "kindSeller": 0,
            "kindSeller": 0,
            "users": self.login_data["usuario"]["users"]
        }

        
        self.logger.info("*" * 100)
        self.logger.info(body)
        self.logger.info("*" * 100)

        yield scrapy.Request(
            url=url,
            method="POST",
            headers=headers,
            cookies=self.cookie,
            body=json.dumps(body),
            callback=self.after_ultimo_pedido
        )

    def after_ultimo_pedido(self, response):
        self.logger.info("*" * 100)
        self.logger.info(f"[PEDIDO] PEDIDOS encontrados: {response.text}")

        lista = response.json().get("lista", [])
        if not lista:
            self.logger.error("[PEDIDO] Nenhum pedido encontrado.")
            return

        id_pedido = lista[0]["id"]

        self.logger.info(f"[PEDIDO] ID do último pedido: {id_pedido}")
        self.logger.info("*" * 100)

        mensagem = {
            "usuario": self.usuario,
            "senha": self.senha,
            "id_pedido": str(id_pedido),
            "produtos": [{
                "gtin": str(self.produto_encontrado["codigoBarras"]),
                "codigo": str(self.produto_encontrado["codigoExterno"]),
                "quantidade": self.quantidade
            }],
            "callback_url": self.callback_url
        }
        enviar_para_fila("orders_queue_nivel3", mensagem)
        self.logger.info(f"[FILA] Pedido {id_pedido} enviado para fila.")
