import logging

LOGGER_NAME = "coursework_logger"

logger = logging.getLogger(LOGGER_NAME)
logger.setLevel(logging.INFO)

_handler = logging.StreamHandler()
_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(_handler)
