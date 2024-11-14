import logging
import colorlog
from config import DEBUG_MODE, SQL_LOGGING

log_format = (
    "%(log_color)s%(levelname)s: %(asctime)s - %(name)s - %(message)s"
)

log_colors = {
    'DEBUG': 'yellow',
    'INFO': 'green',
    'WARNING': 'red',
    'ERROR': 'bold_red',
    'CRITICAL': 'bold_red',
}

handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    log_format, log_colors=log_colors
))

logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.WARNING,
    handlers=[handler],
)

sqlalchemy_log_level = logging.INFO if SQL_LOGGING else logging.WARNING

logging.getLogger("sqlalchemy.engine").setLevel(sqlalchemy_log_level)
logging.getLogger("sqlalchemy.pool").setLevel(sqlalchemy_log_level)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("openai._base_client").setLevel(logging.WARNING)
logging.getLogger("httpcore.http11").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore.connection").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
