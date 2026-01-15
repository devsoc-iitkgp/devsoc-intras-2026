"""
MetaKGP FastAPI Application
Main application with all service routers
"""

from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging
import os
from dotenv import load_dotenv

from src.services.query_service.router import router as query_router, set_query_service
from src.services.query_service.service import QueryService

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info("Starting MetaKGP API...")
    
    # Get configuration from environment
    modal_url = os.getenv("MODAL_URL")
    if not modal_url:
        raise RuntimeError("MODAL_URL environment variable not set")
    
    chroma_dir = os.getenv("CHROMA_DIR", "./chroma_data")
    
    # Initialize query service
    logger.info("Initializing Query Service...")
    query_service = QueryService(
        modal_url=modal_url,
        chroma_dir=chroma_dir,
        collection_name="metakgp_wiki"
    )
    set_query_service(query_service)
    
    logger.info("All services initialized successfully")
    logger.info(f"Total documents: {query_service.get_document_count()}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down MetaKGP API...")


# Create FastAPI app
app = FastAPI(
    title="MetaKGP Chatbot API",
    description="API for MetaKGP WIKI Chatbot",
    version="2.0.0",
    lifespan=lifespan
)


# Include routers
app.include_router(query_router)


@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "name": "MetaKGP Chatbot API",
        "version": "2.0.0",
        "services": {
            "query": {
                "description": "API for MetaKGP WIKI Chatbot",
                "endpoints": {
                    "search": "/query/search (POST)",
                    "health": "/query/health (GET)"
                }
            }
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }


@app.get("/health")
async def health():
    """Overall API health check"""
    return {
        "status": "ok",
        "services": ["query"]
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "src.app.main:app",
        host=host,
        port=port,
        log_level="info",
        reload=False
    )
