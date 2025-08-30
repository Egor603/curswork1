import logging

LOGGER_NAME = "coursework_logger"

logger = logging.getLogger(LOGGER_NAME)
logger.setLevel(logging.INFO)

_handler = logging.StreamHandler()
_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
_handler.setFormatter(_formatter)
logger.addHandler(_handler)
