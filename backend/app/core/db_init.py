import logging
import asyncio
from backend.app.core.mongo import mongo_manager
from backend.app.core.database import db_manager, get_db_connection

logger = logging.getLogger("docnest.db_init")


async def init_mongo_indexes() -> None:
    """
    Ensure performance indexes exist on MongoDB collections.
    """
    if not mongo_manager.is_online or not mongo_manager.db:
        return

    try:
        db = mongo_manager.db
        logger.info("Initializing MongoDB collection indexes...")

        # Users indexes
        await db["users"].create_index("email", unique=True)
        await db["users"].create_index("username", unique=True)

        # Workspaces indexes
        await db["workspaces"].create_index([("user_id", 1), ("created_at", -1)])

        # Documents indexes
        await db["documents"].create_index([("user_id", 1), ("workspace_id", 1), ("status", 1)])
        await db["documents"].create_index([("user_id", 1), ("file_hash", 1)])

        # Conversations indexes
        await db["conversations"].create_index([("user_id", 1), ("is_pinned", -1), ("updated_at", -1)])

        # Messages indexes
        await db["messages"].create_index([("conversation_id", 1), ("created_at", 1)])

        # Notes indexes
        await db["research_notes"].create_index([("user_id", 1), ("updated_at", -1)])
        await db["research_notes"].create_index([("title", "text"), ("content", "text")])

        logger.info("MongoDB collection indexes initialized successfully.")
    except Exception as exc:
        logger.warning(f"MongoDB index initialization warning: {exc}")


async def init_sqlite_indexes() -> None:
    """
    Ensure performance indexes exist on SQLite database tables.
    """
    try:
        async with get_db_connection() as conn:
            # Documents indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_docs_user_ws ON documents(user_id, workspace_id);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_docs_hash ON documents(file_hash);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_docs_status ON documents(status);")

            # Chat sessions indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_sess_user_pin ON chat_sessions(user_id, is_pinned, updated_at);")

            # Chat messages indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_msg_sess_created ON chat_messages(session_id, created_at);")

            # Research notes indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_notes_user_upd ON research_notes(user_id, updated_at);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_notes_sess ON research_notes(session_id);")

            # Collections indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_collections_user ON document_collections(user_id, workspace_id);")

            await conn.commit()
            logger.info("SQLite performance indexes verified.")
    except Exception as exc:
        logger.warning(f"SQLite index initialization warning: {exc}")


async def initialize_all_databases() -> None:
    """
    Unified database initializer: checks MongoDB, runs SQLite schema migrations, and sets indexes.
    """
    # 1. Initialize SQLite tables first
    await db_manager.init_db()
    await init_sqlite_indexes()

    # 2. Check and initialize MongoDB if enabled
    is_mongo_up = await mongo_manager.connect()
    if is_mongo_up:
        await init_mongo_indexes()
