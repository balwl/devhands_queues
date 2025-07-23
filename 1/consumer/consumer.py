import os
import asyncio
from nats.aio.client import Client as NATS

async def run():
    nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
    nats = NATS()

    while True:
        try:
            await nats.connect(nats_url)
            print("Consumer connected to NATS!")
            break
        except Exception as e:
            print(f"Connection failed: {e}, retrying...")
            await asyncio.sleep(1)

    async def message_handler(msg):
        subject = msg.subject
        data = msg.data.decode()
        print(f"Received on [{subject}]: {data}")

    await nats.subscribe("test.subject", cb=message_handler)
    print("Listening for messages...")

    while True:
        await asyncio.sleep(1)

if __name__ == '__main__':
    asyncio.run(run())