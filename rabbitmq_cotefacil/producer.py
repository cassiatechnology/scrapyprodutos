import aioamqp
import json

async def send(produtos, logger=None):
    try:
        logger.info("Iniciando envio de produtos para RabbitMQ...")
        logger.info(f"Produtos: {len(produtos)} itens")

        logger.info("Declarando fila RabbitMQ.")
        transport, protocol = await aioamqp.connect()
        channel = await protocol.channel()
        
        await channel.queue_declare(queue_name='producer')
        logger.info("Fila 'producer' declarada com sucesso.")

        for produto in produtos:
            payload = json.dumps(produto)
            
            logger.info(f"Enviando produto: {payload}")

            await channel.basic_publish(
                payload=payload.encode('utf-8'),
                exchange_name='',
                routing_key='producer'
            )

        await protocol.close()
        transport.close()
    except Exception as e:
        logger.error(f"Erro ao enviar produtos para RabbitMQ: {e}")