import logging
from asyncio.log import logger

from .base import *
from .logging_config import *

logger = logging.getLogger(__name__)

try:
    from .local_settings import *
except ImportError as e:
    logger.error(str(e))

Path(LOGS_ROOT).mkdir(parents=True, exist_ok=True)
