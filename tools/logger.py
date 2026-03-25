import logging


def get_logger(name: str) -> logging.Logger:
    """Создает и настраивает логгер с указанным именем."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)

        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s")
        handler.setFormatter(formatter)

        logger.addHandler(handler)
        logger.propagate = False

    return logger
