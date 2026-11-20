import logging
import asyncio
from typing import Optional, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from backend.app.core.config import settings

logger = logging.getLogger("docnest.mongo")


class MongoManager:
    """
    Asynchronous MongoDB client manager with automatic health verification
    and transparent fallback flag for SQLite dual-layer persistence.
    """

    def __init__(self):
        self._client: Optional[AsyncIOMotorClient] = None
        self._db: Optional[AsyncIOMotorDatabase] = None
        self._is_online: bool = False

    async def connect(self) -> bool:
        """
        Attempt to establish connection to MongoDB. Returns True if alive, False otherwise.
        """
        if not settings.MONGO_ENABLED:
            logger.info("MongoDB disabled via configuration. Using SQLite as primary storage engine.")
            self._is_online = False
            return False

        try:
            logger.info(f"Connecting to MongoDB at {settings.MONGO_URI}...")
            self._client = AsyncIOMotorClient(
                settings.MONGO_URI,
                serverSelectionTimeoutMS=2000,
                connectTimeoutMS=2000,
            )
            # Ping database to verify active connection
            await self._client.admin.command("ping")
            self._db = self._client[settings.MONGO_DB_NAME]
            self._is_online = True
            logger.info(f"MongoDB connected successfully to database '{settings.MONGO_DB_NAME}'.")
            return True
        except Exception as exc:
            logger.warning(
                f"MongoDB connection failed ({exc}). Gracefully falling back to SQLite engine."
            )
            self._is_online = False
            self._client = None
            self._db = None
            return False

    async def disconnect(self) -> None:
        """Gracefully close MongoDB connection pool."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            self._is_online = False
            logger.info("MongoDB connection closed.")

    @property
    def is_online(self) -> bool:
        return self._is_online

    @property
    def db(self) -> Optional[AsyncIOMotorDatabase]:
        return self._db if self._is_online else None

    async def ping(self) -> bool:
        if not self._is_online or not self._client:
            return False
        try:
            await self._client.admin.command("ping")
            return True
        except Exception:
            self._is_online = False
            return False


mongo_manager = MongoManager()


def get_mongo_db() -> Optional[AsyncIOMotorDatabase]:
    return mongo_manager.db


def is_mongo_online() -> bool:
    return mongo_manager.is_online
