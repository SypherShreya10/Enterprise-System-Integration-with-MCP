import logging
import os

LOG_DIR = "logs"
LOG_FILE = "logs/security_audit.log"

os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger("security_audit")
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter(
    "%(asctime)s | user=%(user)s | role=%(role)s | tool=%(tool)s | status=%(status)s"
)

file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def log_audit(user, role, tool, status):
    logger.info(
        "tool_usage",
        extra={
            "user": user,
            "role": role,
            "tool": tool,
            "status": status
        }
    )