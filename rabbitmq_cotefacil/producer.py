import asyncio
import aioamqp
import json
import os

async def send(produtos, logger=None):
    try:
        if logger:
            logger.info("Iniciando envio de produtos para RabbitMQ...")
            logger.info(f"Produtos: {len(produtos)} itens")
        else:
            print("Iniciando envio de produtos para RabbitMQ...")
            print(f"Produtos: {len(produtos)} itens")

        logger.info("Declarando fila RabbitMQ.")
        transport, protocol = await aioamqp.connect()
        channel = await protocol.channel()
        
        await channel.queue_declare(queue_name='producer')
        if logger:
            logger.info("Fila 'producer' declarada com sucesso.")
        else:
            print("Fila 'producer' declarada com sucesso.")

        for produto in produtos:
            payload = json.dumps(produto)
            if logger:
                logger.info(f"Enviando produto: {payload}")
            else:
                print(f"Enviando produto: {payload}")
            await channel.basic_publish(
                payload=payload.encode('utf-8'),
                exchange_name='',
                routing_key='producer'
            )
            # await asyncio.sleep(1)

        await protocol.close()
        transport.close()
    except Exception as e:
        if logger:
            logger.error(f"Erro ao enviar produtos para RabbitMQ: {e}")
        else:
            print(f"Erro ao enviar produtos para RabbitMQ: {e}")