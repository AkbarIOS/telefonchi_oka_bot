from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import List, Optional, Dict, Any
import logging
import uuid
import os
from pathlib import Path

from app.core.dependencies import get_bot_handler
from app.handlers.bot_handler import BotHandler
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# File upload configuration - use uploads directory
UPLOAD_DIR = Path("/app/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.get("/advertisements")
async def get_advertisements(
    page: int = 1,
    limit: int = 10,
    category: Optional[str] = None,
    brand: Optional[str] = None,
    city: Optional[str] = None,
    status: Optional[str] = None,
    bot_handler: BotHandler = Depends(get_bot_handler)
) -> Dict[str, Any]:
    """Get all advertisements with pagination and filters"""
    try:
        # Calculate offset
        offset = (page - 1) * limit

        # Build query with filters
        where_conditions = []
        params = []

        if category:
            where_conditions.append("c.name_en = %s")
            params.append(category)

        if brand:
            where_conditions.append("b.name = %s")
            params.append(brand)

        if city:
            where_conditions.append("a.city = %s")
            params.append(city)

        if status:
            where_conditions.append("a.status = %s")
            params.append(status)

        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

        # Get advertisements with joins
        query = f"""
        SELECT
            a.id, a.model, a.price, a.description, a.city, a.phone, a.contact_phone,
            a.photo_path, a.status, a.created_at, a.user_id,
            c.name_ru as category_name, b.name as brand_name,
            u.username
        FROM advertisements a
        LEFT JOIN categories c ON a.category_id = c.id
        LEFT JOIN brands b ON a.brand_id = b.id
        LEFT JOIN users u ON a.user_id = u.telegram_id
        {where_clause}
        ORDER BY a.created_at DESC
        LIMIT %s OFFSET %s
        """

        params.extend([limit, offset])
        ads = await bot_handler.advertisement_service.db.fetchall(query, params)

        # Get total count
        count_query = f"""
        SELECT COUNT(*) as total
        FROM advertisements a
        LEFT JOIN categories c ON a.category_id = c.id
        LEFT JOIN brands b ON a.brand_id = b.id
        {where_clause}
        """

        total_result = await bot_handler.advertisement_service.db.fetchone(count_query, params[:-2])
        total = total_result['total'] if total_result else 0

        # Calculate total pages
        total_pages = (total + limit - 1) // limit

        return {
            "advertisements": ads,
            "total": total,
            "page": page,
            "totalPages": total_pages
        }

    except Exception as e:
        logger.error(f"Error getting advertisements: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch advertisements")


@router.get("/users/{user_id}/advertisements")
async def get_user_advertisements(
    user_id: int,
    status: Optional[str] = None,
    bot_handler: BotHandler = Depends(get_bot_handler)
) -> Dict[str, Any]:
    """Get advertisements for a specific user"""
    try:
        # Get internal user ID from telegram ID
        user = await bot_handler.advertisement_service.db.get_user(user_id)
        if not user:
            return {"advertisements": []}

        internal_user_id = user['id']

        where_clause = "WHERE a.user_id = %s"
        params = [internal_user_id]

        if status:
            where_clause += " AND a.status = %s"
            params.append(status)

        query = f"""
        SELECT
            a.id, a.model, a.price, a.description, a.city, a.phone, a.contact_phone,
            a.photo_path, a.status, a.created_at, a.user_id,
            c.name_ru as category_name, b.name as brand_name,
            u.username
        FROM advertisements a
        LEFT JOIN categories c ON a.category_id = c.id
        LEFT JOIN brands b ON a.brand_id = b.id
        LEFT JOIN users u ON a.user_id = u.telegram_id
        {where_clause}
        ORDER BY a.created_at DESC
        """

        ads = await bot_handler.advertisement_service.db.fetchall(query, params)

        # Convert photo paths to proxied URLs to avoid CORS issues in Telegram WebApp
        base_url = "https://telefonchi-backend-working.loca.lt"
        for ad in ads:
            if ad.get('photo_path'):
                # If already a full URL, leave it
                if ad['photo_path'].startswith('http'):
                    continue
                # Extract filename for proxy endpoint
                if ad['photo_path'].startswith('/static/uploads/'):
                    filename = ad['photo_path'].split('/')[-1]
                elif ad['photo_path'].startswith('/app/uploads/'):
                    filename = ad['photo_path'].split('/')[-1]
                else:
                    filename = ad['photo_path']

                # Use proxy endpoint to serve images through same domain
                ad['photo_path'] = f"{base_url}/api/proxy/image/{filename}"

        return {
            "advertisements": ads
        }

    except Exception as e:
        logger.error(f"Error getting user advertisements: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch user advertisements")


@router.post("/advertisements")
async def create_advertisement(
    user_id: int = Form(...),
    category_id: int = Form(...),
    brand_id: int = Form(...),
    model: str = Form(...),
    price: int = Form(...),
    description: str = Form(...),
    city: str = Form(...),
    contact_phone: str = Form(...),
    photo: UploadFile = File(...),
    bot_handler: BotHandler = Depends(get_bot_handler)
) -> Dict[str, Any]:
    """Create a new advertisement"""
    try:
        logger.info(f"Creating advertisement for user {user_id}: {model}")
        logger.info(f"Form data: category_id={category_id}, brand_id={brand_id}, price={price}, city={city}")
        logger.info(f"Photo filename: {photo.filename}, content_type: {photo.content_type}")
        # Get or create user in database using telegram_id
        logger.info(f"Looking up user with telegram_id: {user_id}")
        user = await bot_handler.advertisement_service.db.get_user(user_id)
        if not user:
            logger.info(f"User not found, creating new user with telegram_id: {user_id}")
            # Create user if doesn't exist
            await bot_handler.advertisement_service.db.create_user(
                telegram_id=user_id,
                username=f"user_{user_id}",  # Default username
                first_name="Unknown",  # Default first name
                language="ru"  # Default language
            )
            user = await bot_handler.advertisement_service.db.get_user(user_id)
            logger.info(f"Created user successfully: {user}")

        # Use the internal user ID from database
        internal_user_id = user['id']
        logger.info(f"Using internal user ID: {internal_user_id}")

        # Save uploaded file
        file_extension = photo.filename.split('.')[-1] if '.' in photo.filename else 'jpg'
        filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = UPLOAD_DIR / filename

        # Create the URL that will be accessible
        photo_url = f"/static/uploads/{filename}"

        with open(file_path, "wb") as buffer:
            content = await photo.read()
            buffer.write(content)

        # Create advertisement record using internal user ID
        logger.info(f"Inserting advertisement into database")
        query = """
        INSERT INTO advertisements (
            user_id, category_id, brand_id, model, price, description,
            phone, city, contact_phone, photo_path, status, created_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending', NOW())
        """

        query_params = [
            internal_user_id, category_id, brand_id, model, price, description,
            contact_phone, city, contact_phone, photo_url
        ]
        logger.info(f"Query params: {query_params}")

        await bot_handler.advertisement_service.db.execute(query, query_params)
        logger.info(f"Advertisement inserted successfully")

        # Get the created advertisement
        ad_query = """
        SELECT
            a.id, a.model, a.price, a.description, a.city, a.phone, a.contact_phone,
            a.photo_path, a.status, a.created_at, a.user_id,
            c.name_ru as category_name, b.name as brand_name
        FROM advertisements a
        LEFT JOIN categories c ON a.category_id = c.id
        LEFT JOIN brands b ON a.brand_id = b.id
        WHERE a.user_id = %s AND a.model = %s AND a.price = %s
        ORDER BY a.created_at DESC
        LIMIT 1
        """

        ad = await bot_handler.advertisement_service.db.fetchone(ad_query, [internal_user_id, model, price])

        # Convert photo path to proxied URL to avoid CORS issues in Telegram WebApp
        if ad and ad.get('photo_path'):
            base_url = "https://telefonchi-backend-working.loca.lt"
            # If already a full URL, leave it
            if ad['photo_path'].startswith('http'):
                pass
            else:
                # Extract filename for proxy endpoint
                if ad['photo_path'].startswith('/static/uploads/'):
                    filename = ad['photo_path'].split('/')[-1]
                elif ad['photo_path'].startswith('/app/uploads/'):
                    filename = ad['photo_path'].split('/')[-1]
                else:
                    filename = ad['photo_path']

                # Use proxy endpoint to serve images through same domain
                ad['photo_path'] = f"{base_url}/api/proxy/image/{filename}"

        return {
            "advertisement": ad
        }

    except Exception as e:
        logger.error(f"Error creating advertisement: {e}")
        raise HTTPException(status_code=500, detail="Failed to create advertisement")


@router.post("/advertisements/{ad_id}/sold")
async def mark_advertisement_sold(
    ad_id: int,
    bot_handler: BotHandler = Depends(get_bot_handler)
) -> Dict[str, Any]:
    """Mark an advertisement as sold"""
    try:
        query = "UPDATE advertisements SET status = 'sold' WHERE id = %s"
        await bot_handler.advertisement_service.db.execute(query, [ad_id])

        return {
            "status": "success",
            "message": "Advertisement marked as sold"
        }

    except Exception as e:
        logger.error(f"Error marking advertisement as sold: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark advertisement as sold")


@router.get("/categories")
async def get_categories(
    bot_handler: BotHandler = Depends(get_bot_handler)
) -> Dict[str, Any]:
    """Get all categories"""
    try:
        query = "SELECT id, name_ru, name_uz FROM categories ORDER BY name_ru"
        categories = await bot_handler.advertisement_service.db.fetchall(query)

        return {
            "categories": categories
        }

    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch categories")


@router.get("/brands")
async def get_brands(
    category_id: Optional[int] = None,
    bot_handler: BotHandler = Depends(get_bot_handler)
) -> Dict[str, Any]:
    """Get all brands or brands filtered by category"""
    try:
        if category_id:
            query = "SELECT id, name FROM brands WHERE category_id = %s ORDER BY name"
            brands = await bot_handler.advertisement_service.db.fetchall(query, [category_id])
        else:
            query = "SELECT id, name FROM brands ORDER BY name"
            brands = await bot_handler.advertisement_service.db.fetchall(query)

        return {
            "brands": brands
        }

    except Exception as e:
        logger.error(f"Error getting brands: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch brands")


@router.post("/auth/validate")
async def validate_telegram_data(
    data: Dict[str, Any],
    bot_handler: BotHandler = Depends(get_bot_handler)
) -> Dict[str, Any]:
    """Validate Telegram Web App data"""
    try:
        # For now, return a simple validation
        # In production, you should validate the initData parameter
        return {
            "valid": True,
            "user": {
                "id": 162099531,  # Placeholder
                "username": "test_user"
            }
        }

    except Exception as e:
        logger.error(f"Error validating Telegram data: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate Telegram data")