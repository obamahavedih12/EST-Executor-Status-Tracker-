import logging
import sys
from pathlib import Path

Path("logs").mkdir(exist_ok=True)

logging.basicConfig(
    level    = logging.INFO,
    format   = "[%(asctime)s] [%(levelname)-8s] [%(name)s] %(message)s",
    datefmt  = "%Y-%m-%d %H:%M:%S",
    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/bot.log", encoding="utf-8")
    ]
)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
