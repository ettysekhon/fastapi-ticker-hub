import asyncio
import logging

from app.polling import poll_loop

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")

if __name__ == "__main__":
    logging.info("Starting standalone polling worker")
    asyncio.run(poll_loop())
