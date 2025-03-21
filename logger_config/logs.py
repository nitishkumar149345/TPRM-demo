# logger_config.py
from loguru import logger



logger.remove()  
logger.add(
    "app.log",
    format="{time} | {level} | {message}",
    level="INFO",
    rotation="1 MB",
    retention="1 week",
    enqueue=True
)


__all__ = ["logger"]
