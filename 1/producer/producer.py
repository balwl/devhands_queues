import os
import asyncio
import socket
from nats.aio.client import Client as NATS

container_id = socket.gethostname()

async def main():
    nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
    nats = NATS()

    while True:
        try:
            await nats.connect(nats_url)
            print("Producer connected to NATS!")
            break
        except Exception as e:
            print(f"Connection failed: {e}, retrying...")
            await asyncio.sleep(1)

    # Send messages every 2 seconds
    counter = 0
    while True:
        counter += 1
        message = f"Hello from producer {container_id}! ({counter})"
        await nats.publish("test.subject", message.encode())
        print(f"Published: {message}")
        await asyncio.sleep(2)

if __name__ == '__main__':
    asyncio.run(main())