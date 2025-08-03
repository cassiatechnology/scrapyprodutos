import asyncio
import aioamqp

async def callback_consumer(channel, body, envelope, properties):
    print(f"Recebido produto: {body.decode('utf-8')}")

async def receiver():
    transport, protocol = await aioamqp.connect()
    channel = await protocol.channel()

    await channel.queue_declare(queue_name='producer')
    
    print("Aguardando produtos...")
    await channel.basic_consume(
        queue_name='producer',
        callback=callback_consumer
    )

    await asyncio.Event().wait()  # Keep the consumer running

if __name__ == "__main__":
    asyncio.run(receiver())