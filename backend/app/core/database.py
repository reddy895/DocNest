import aiosqlite
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from backend.app.core.config import settings

logger = logging.getLogger("docnest.db")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    username TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    workspace_name TEXT NOT NULL DEFAULT 'Default Workspace',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    page_count INTEGER NOT NULL DEFAULT 0,
    total_chunks INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'ready',
    progress_pct INTEGER NOT NULL DEFAULT 100,
    error_msg TEXT,
    is_scanned BOOLEAN NOT NULL DEFAULT 0,
    tags TEXT NOT NULL DEFAULT '[]',
    file_path TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    sender TEXT NOT NULL,
    text TEXT NOT NULL,
    citations TEXT NOT NULL DEFAULT '[]',
    retrieval_trace TEXT NOT NULL DEFAULT '{}',
    feedback_rating INTEGER,
    feedback_comment TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_settings (
    user_id TEXT PRIMARY KEY,
    chunk_size INTEGER NOT NULL DEFAULT 512,
    chunk_overlap INTEGER NOT NULL DEFAULT 64,
    top_k INTEGER NOT NULL DEFAULT 5,
    min_relevance_score REAL NOT NULL DEFAULT 0.30,
    temperature REAL NOT NULL DEFAULT 0.1,
    hybrid_enabled BOOLEAN NOT NULL DEFAULT 1,
    reranker_enabled BOOLEAN NOT NULL DEFAULT 1,
    preset_name TEXT NOT NULL DEFAULT 'balanced',
    updated_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS eval_runs (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    faithfulness_score REAL NOT NULL,
    relevancy_score REAL NOT NULL,
    precision_score REAL NOT NULL,
    avg_retrieval_ms REAL NOT NULL,
    avg_ttft_ms REAL NOT NULL,
    total_questions INTEGER NOT NULL,
    results_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_docs_user ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_docs_hash ON documents(file_hash);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_session ON chat_messages(session_id);
"""


class DatabaseManager:
    """Manages asynchronous SQLite connections and database initialization."""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    async def init_db(self) -> None:
        """Initialize SQLite tables and indexes."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initializing SQLite database schema at {self.db_path}...")
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript(SCHEMA_SQL)
            await db.execute("""
            INSERT OR IGNORE INTO users (id, email, username, password_hash, workspace_name, created_at)
            VALUES ('user_default_local', 'local@docnest.ai', 'Local User', 'local_dev_only', 'Default Workspace', datetime('now'))
            """)
            await db.commit()
        logger.info("Database schema initialized successfully.")

    async def get_db(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        """Dependency for FastAPI async routes."""
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            await conn.execute("PRAGMA foreign_keys = ON;")
            yield conn


db_manager = DatabaseManager(settings.DB_PATH)


async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    async for conn in db_manager.get_db():
        yield conn


@asynccontextmanager
async def get_db_connection() -> AsyncGenerator[aiosqlite.Connection, None]:
    """Helper async context manager for background workers and services."""
    async with aiosqlite.connect(settings.DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA foreign_keys = ON;")
        yield conn

