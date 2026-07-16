"""
ToxicUB - Configuration
========================
All credentials MUST come from environment variables.
"""

import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("ToxicUB")


class Config:
    API_ID: int = int(os.getenv("API_ID", "0"))
    API_HASH: str = os.getenv("API_HASH", "")
    STRING_SESSION: str = os.getenv("STRING_SESSION", "")

    PREFIX: str = os.getenv("BOT_PREFIX", ".")
    LOG_GROUP: int = int(os.getenv("LOG_GROUP", "0"))

    BOT_NAME: str = "ToxicUB"
    BOT_VERSION: str = "2.1.0"
    BOT_REPO: str = "https://github.com/SegsyToxic95/ToxicUB"
    OWNER_USERNAME: str = os.getenv("OWNER_USERNAME", "@SegsyToxic95")
    SUDO_USERS: list = [
        int(x) for x in os.getenv("SUDO_USERS", "").split() if x.strip().isdigit()
    ]

    PORT: int = int(os.getenv("PORT", "8080"))

    SPAM_LIMIT: int = 50
    FLOOD_LIMIT: int = 100
    SPAM_DELAY: float = 0.3

    MAX_RESTART_ATTEMPTS: int = 15
    RESTART_BACKOFF_BASE: int = 5
    RESTART_BACKOFF_MAX: int = 300
    RECONNECT_DELAY_BASE: int = 3
    RECONNECT_DELAY_MAX: int = 120

    @classmethod
    def validate(cls) -> bool:
        return cls.API_ID != 0 and bool(cls.API_HASH) and bool(cls.STRING_SESSION)

    @classmethod
    def missing_vars(cls) -> list:
        m = []
        if cls.API_ID == 0:
            m.append("API_ID")
        if not cls.API_HASH:
            m.append("API_HASH")
        if not cls.STRING_SESSION:
            m.append("STRING_SESSION")
        return m
