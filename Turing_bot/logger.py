# logger.py
import logging
import os


def setup_logger(name, log_file, level=logging.INFO):
    """Configura y retorna un logger."""
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    # Evitar que los logs se propaguen a otros loggers
    logger.propagate = False

    return logger


# Configuración de loggers específicos
bot_logger = setup_logger("bot_logger", "bot.log")
data_logger = setup_logger("data_logger", "data.log")
ai_logger = setup_logger("ai_logger", "ai.log")
