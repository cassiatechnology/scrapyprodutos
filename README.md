Este projeto implementa um processo de scraping autenticado no site da **Servimed**, integração com a API de callback da **Cotefácil**, e processamento assíncrono usando **RabbitMQ**.

---

## 📋 Pré-requisitos

Antes de rodar o projeto, garanta que você tem:

1. **Python 3.10+** instalado
2. **Pip** atualizado
3. **Virtualenv** para ambiente virtual
4. **RabbitMQ** instalado e rodando localmente
5. **Git** instalado
6. Conta na **API de Callback Cotefácil** com usuário criado via `/oauth/signup`

---

## ⚙️ Instalação e Configuração

### 1. Clone o repositório

```bash
git clone https://github.com/cassiatechnology/scrapyprodutos.git
cd servimed_scraper

```

### 2. Crie e ative o ambiente virtual

```bash
python -m venv venv

# Windows
venv\\Scripts\\activate

# Linux/Mac
source venv/bin/activate

```

### 3. Instale as dependências

```bash
pip install -r requirements.txt

```

### 4. Configure variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto com:

```
USERNAME_COTEFACIL=seu_usuario
PASSWORD_COTEFACIL=sua_senha

```

### 5. Suba o RabbitMQ

Se estiver usando Docker:

```bash
cd .\servimed_scraper
docker compose up
```

Interface de administração: [http://localhost:15672](http://localhost:15672/)

Usuário/senha padrão: `guest / guest`

---

## 🚀 Testes por Níve

### 📌 **Nível 1 – Scraping Autenticado**

Rodar diretamente a spider para buscar produtos:

```bash
scrapy crawl servimed_produtos -a usuario="usuario@dominio.com" -a senha="sua_senha" -a filtro="dipirona" -a callback_url="https://desafio.cotefacil.net"

```

Isso irá:

- Logar no sistema da Servimed
- Buscar produtos pelo filtro
- Salvar em `produtos.json`
- Enviar para a API de callback (se configurado)

---

### 📌 **Nível 2 – Consulta de Produtos com Fila**

### 1. Inicie o **consumer**:

```bash
python -m servimed_scraper.rabbitmq.produto_consumer

```

### 2. Envie a tarefa com o **producer**:

Edite o arquivo `parametros.json` na raiz:

```json
{
    "usuario": "usuario@dominio.com",
    "senha": "sua_senha",
    "callback_url": "<https://desafio.cotefacil.net>",
    "filtro": "dipirona"
}

```

E rode:

```bash
python -m servimed_scraper.rabbitmq.produto_producer

```

### 3. Resultado:

- O consumer executa a spider
- Busca produtos pelo filtro
- Salva localmente e envia para a API de callback

---

### 📌 **Nível 3 – Pedido de Produto Específico com Fila**

### 1. Inicie o **consumer de pedidos**:

```bash
python -m servimed_scraper.rabbitmq.order_consumer

```

### 2. Gere e envie o pedido com o **producer**:

```bash
python -m servimed_scraper.rabbitmq.producer_order

```

Este script:

1. Executa a spider `servimed_pedidos`
2. Faz login e busca o produto pelo código
3. Realiza o pedido (`TrasmitirPedido`)
4. Obtém o ID do pedido mais recente
5. Enfileira no RabbitMQ

### 3. Resultado:

- O consumer de pedidos pega o ID
- Faz PATCH para `/pedido/:id` na API da Cotefácil com:

```json
{
    "codigo_confirmacao": "ID_DO_PEDIDO",
    "status": "pedido_realizado"
}

```

### 4. Fazer PATCH para /pedido/:id com os dados extraídos

Não foi possível executar essa etapa, pois o endpoint da API está com problemas:

```powershell
curl -X 'POST' \
  'https://desafio.cotefacil.net/pedido' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciO...KcrXLlF2KO0wO' \
  -d ''
```

**Error: response status is 500**

```json
{
  "message": "Unhandled server error"
}
```

---

## 🗂 Estrutura de Pastas

```
servimed_scraper/
│
├── callback/              # Integração com API Cotefácil
├── rabbitmq/              # Consumers e Producers para filas
├── spiders/               # Spiders Scrapy
├── utils/                 # Funções auxiliares
├── produtos.json          # Saída do scraping de produtos
├── produtos_nivel3.json     # ID do último pedido gerado
├── parametros.json        # Parâmetros do producer de produtos
└── .env                   # Credenciais

```

---

## 📌 Observações Importantes

- Somente a spider de produtos salva `produtos.json`.
- Sempre iniciar o **consumer** antes do **producer**.
- Use o **RabbitMQ Management** para monitorar filas: [http://localhost:15672](http://localhost:15672/)
- Certifique-se de que a API da Cotefácil está acessível antes de enviar callbacks.

---

## 🧪 Evidencias de Teste no Postman

### Cadastro de Produtos na API da Cotefacil:

imagens/produtos.png

---

### Cadastro de Pedidos na API da Servimed:

imagens/pedido.png