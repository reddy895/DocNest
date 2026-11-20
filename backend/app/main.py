import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from backend.app.api.health import router as health_router
from backend.app.api.system import router as system_router
from backend.app.api.auth import router as auth_router
from backend.app.api.settings import router as settings_router
from backend.app.api.documents import router as documents_router
from backend.app.api.chat import router as chat_router
from backend.app.api.eval import router as eval_router
from backend.app.api.research import router as research_router
from backend.app.api.workspaces import router as workspaces_router
from backend.app.api.conversations import router as conversations_router
from backend.app.api.models import router as models_router

# Configure standard structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("docnest")


from backend.app.core.db_init import initialize_all_databases
from backend.app.core.mongo import mongo_manager
from backend.app.core.middleware import register_error_handlers, CorrelationIdMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting DocNest API service...")
    await initialize_all_databases()
    yield
    logger.info("Shutting down DocNest API service...")
    await mongo_manager.disconnect()


app = FastAPI(
    title="DocNest API",
    description="Enterprise Document Intelligence & RAG Platform powered by ChromaDB and local Llama 3.2",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(CorrelationIdMiddleware)

app.include_router(health_router)
app.include_router(system_router)
app.include_router(auth_router)
app.include_router(settings_router)
app.include_router(documents_router)
app.include_router(chat_router)
app.include_router(eval_router)
app.include_router(research_router)
app.include_router(workspaces_router)
app.include_router(conversations_router)
app.include_router(models_router)

# Register centralized error handlers
register_error_handlers(app)


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": "DocNest API",
        "version": "1.0.0",
        "tagline": "Your documents. Your questions. Clear answers.",
        "status": "operational",
        "docs": "/docs",
    }
