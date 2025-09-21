from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse
import logging
from typing import Dict
from app.handlers.bot_handler import BotHandler
from app.core.dependencies import get_bot_handler
from app.schemas.telegram import TelegramUpdate

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/webhook")
async def webhook(
    request: Request,
    bot_handler: BotHandler = Depends(get_bot_handler)
) -> JSONResponse:
    """Handle incoming Telegram webhook updates"""
    try:
        # Get raw request data
        json_data = await request.json()
        logger.info(f"Received webhook update: {json_data.get('update_id', 'unknown')}")
        logger.debug(f"Full webhook data: {json_data}")

        # Validate and parse update
        try:
            update = TelegramUpdate(**json_data)
        except Exception as validation_error:
            logger.error(f"Invalid update format: {validation_error}")
            logger.debug(f"Raw update data: {json_data}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid update format"
            )

        # Process the update using raw JSON data to preserve field names
        logger.info(f"About to call bot_handler.process_update with data: {json_data.get('update_id', 'unknown')}")
        await bot_handler.process_update(json_data)
        logger.info(f"Successfully processed update {json_data.get('update_id', 'unknown')}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "ok"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        logger.exception("Full webhook error traceback:")

        # Don't expose internal errors to Telegram
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "error"}
        )


@router.get("/webhook/status")
async def webhook_status() -> Dict:
    """Get webhook status"""
    return {
        "status": "active",
        "version": "2.0.0",
        "architecture": "SOLID FastAPI"
    }


@router.post("/webhook/set")
async def set_webhook(
    request: Request,
    bot_handler: BotHandler = Depends(get_bot_handler)
) -> Dict:
    """Set webhook URL programmatically"""
    try:
        data = await request.json()
        webhook_url = data.get("webhook_url")

        if not webhook_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="webhook_url is required"
            )

        # Set webhook via Telegram service
        result = await bot_handler.telegram_service.set_webhook(webhook_url)
        logger.info(f"Webhook set to: {webhook_url}")

        return {
            "status": "success",
            "webhook_url": webhook_url,
            "telegram_response": result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Set webhook error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set webhook"
        )


@router.delete("/webhook")
async def delete_webhook(
    bot_handler: BotHandler = Depends(get_bot_handler)
) -> Dict:
    """Delete webhook"""
    try:
        result = await bot_handler.telegram_service.delete_webhook()
        logger.info("Webhook deleted")

        return {
            "status": "success",
            "message": "Webhook deleted",
            "telegram_response": result
        }

    except Exception as e:
        logger.error(f"Delete webhook error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete webhook"
        )


@router.get("/webhook/info")
async def webhook_info(
    bot_handler: BotHandler = Depends(get_bot_handler)
) -> Dict:
    """Get webhook information"""
    try:
        result = await bot_handler.telegram_service.get_webhook_info()
        return {
            "status": "success",
            "webhook_info": result
        }

    except Exception as e:
        logger.error(f"Get webhook info error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get webhook info"
        )