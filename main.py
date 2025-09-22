from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn
import logging
import sys
import os
from typing import Dict
from app.core.config import settings
from app.api.webhook import router as webhook_router
from app.api.miniapp import router as miniapp_router
from app.core.dependencies import get_database, get_bot_handler
from app.handlers.bot_handler import BotHandler

# Configure logging with proper levels
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan with SOLID architecture"""
    logger.info("Starting SOLID FastAPI Bot Service...")

    try:
        # Database will be initialized per request via dependency injection
        logger.info(f"Bot service initialized with SOLID architecture")
        logger.info(f"App: {settings.app_name} v{settings.app_version}")
        logger.info(f"Debug mode: {settings.debug}")

        # Set webhook if URL is provided
        if settings.webhook_url:
            logger.info(f"Webhook URL configured: {settings.webhook_url}")

        yield
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise
    finally:
        logger.info("Shutting down SOLID FastAPI Bot Service...")


# Create FastAPI app with SOLID architecture
app = FastAPI(
    title=settings.app_name,
    description="SOLID FastAPI Telegram Bot for Electronics Marketplace",
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan
)

# CORS middleware - allow specific origins for production security
allowed_origins = ["*"] if settings.debug else [
    "https://telefonchiokaminiapp-production.up.railway.app",
    "http://localhost:3000",  # For local development
    "https://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Custom static file handler with CORS headers
from fastapi.responses import FileResponse
from fastapi import Request
import os

@app.options("/static/uploads/{filename}")
async def serve_upload_options(filename: str):
    """Handle OPTIONS requests for CORS preflight"""
    response = JSONResponse(content={})
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@app.get("/static/uploads/{filename}")
async def serve_upload(filename: str, request: Request):
    """Serve uploaded files with proper CORS headers"""
    file_path = f"/app/uploads/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    response = FileResponse(file_path)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@app.options("/api/proxy/image/{filename}")
async def proxy_image_options(filename: str):
    """Handle OPTIONS requests for image proxy CORS preflight"""
    response = JSONResponse(content={})
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@app.get("/api/proxy/image/{filename}")
async def proxy_image(filename: str):
    """Proxy images through the API domain to avoid CORS issues in Telegram WebApp"""
    file_path = f"/app/uploads/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    response = FileResponse(file_path)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response

# Include API routers with proper versioning
app.include_router(webhook_router, prefix="/api/v1", tags=["webhook"])
app.include_router(miniapp_router, prefix="/api", tags=["miniapp"])


@app.get("/")
async def root() -> Dict:
    """Root endpoint with SOLID architecture info"""
    return {
        "message": f"{settings.app_name} is running",
        "version": settings.app_version,
        "architecture": "SOLID FastAPI",
        "status": "active",
        "debug": settings.debug
    }


@app.get("/health")
async def health_check(
    db=Depends(get_database),
    bot_handler: BotHandler = Depends(get_bot_handler)
) -> Dict:
    """Health check endpoint with dependency injection"""
    try:
        # Check database connection via dependency
        db_status = "connected" if db.pool else "disconnected"

        # Check Telegram service
        try:
            await bot_handler.telegram_service.get_webhook_info()
            telegram_status = "connected"
        except Exception:
            telegram_status = "error"

        return {
            "status": "healthy",
            "database": db_status,
            "telegram": telegram_status,
            "architecture": "SOLID FastAPI",
            "version": settings.app_version,
            "components": {
                "repository_layer": "✅ Active",
                "service_layer": "✅ Active",
                "handler_layer": "✅ Active",
                "dependency_injection": "✅ Active"
            }
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "architecture": "SOLID FastAPI"
        }


# Legacy webhook endpoint for backward compatibility
@app.post("/webhook")
async def webhook_legacy(
    request: Request,
    bot_handler: BotHandler = Depends(get_bot_handler)
) -> JSONResponse:
    """Legacy webhook endpoint for backward compatibility"""
    logger.warning("Using legacy webhook endpoint. Please use /api/v1/webhook")

    try:
        json_data = await request.json()
        await bot_handler.process_update(json_data)
        return JSONResponse(content={"status": "ok"})
    except Exception as e:
        logger.error(f"Legacy webhook error: {e}")
        return JSONResponse(content={"status": "error"}, status_code=200)


@app.post("/broadcast")
async def broadcast_message(
    request: Request,
    bot_handler: BotHandler = Depends(get_bot_handler)
) -> Dict:
    """Broadcast message to all users with SOLID architecture"""
    try:
        data = await request.json()
        message = data.get("message")

        if not message:
            raise HTTPException(status_code=400, detail="Message is required")

        # Get all users via service layer
        users = await bot_handler.user_service.db.fetchall("SELECT telegram_id FROM users")
        user_ids = [user['telegram_id'] for user in users]

        # Broadcast via telegram service
        result = await bot_handler.telegram_service.broadcast_message(user_ids, message)

        return {
            "status": "success",
            "message": "Broadcast completed",
            "sent_to": result['successful'],
            "failed": result['failed'],
            "architecture": "SOLID FastAPI"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Broadcast error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_statistics(
    bot_handler: BotHandler = Depends(get_bot_handler)
) -> Dict:
    """Get bot statistics with SOLID architecture"""
    try:
        # Get stats via service layer
        total_users = await bot_handler.user_service.db.fetchone("SELECT COUNT(*) as count FROM users")
        total_ads = await bot_handler.advertisement_service.db.fetchone("SELECT COUNT(*) as count FROM advertisements")
        pending_ads = await bot_handler.advertisement_service.db.fetchone(
            "SELECT COUNT(*) as count FROM advertisements WHERE status = 'pending'"
        )

        # Get category statistics
        category_stats = await bot_handler.advertisement_service.get_category_statistics()

        return {
            "status": "success",
            "architecture": "SOLID FastAPI",
            "statistics": {
                "total_users": total_users['count'] if total_users else 0,
                "total_advertisements": total_ads['count'] if total_ads else 0,
                "pending_advertisements": pending_ads['count'] if pending_ads else 0,
                "category_breakdown": category_stats
            }
        }

    except Exception as e:
        logger.error(f"Get statistics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/bot-info")
async def get_bot_info(
    bot_handler: BotHandler = Depends(get_bot_handler)
) -> Dict:
    """Get bot information via SOLID architecture"""
    try:
        # Get webhook info via telegram service
        webhook_info = await bot_handler.telegram_service.get_webhook_info()

        return {
            "status": "success",
            "architecture": "SOLID FastAPI",
            "webhook_info": webhook_info,
            "app_config": {
                "name": settings.app_name,
                "version": settings.app_version,
                "debug": settings.debug,
                "ad_price": settings.advertisement_price
            }
        }

    except Exception as e:
        logger.error(f"Get bot info error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # Production-ready server configuration
    # Use Railway's PORT environment variable if available, fallback to 8000
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True
    )