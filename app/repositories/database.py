from typing import Optional, Dict, List, Any
from abc import ABC, abstractmethod
import aiomysql
from aiomysql import Pool
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class BaseRepository(ABC):
    """Abstract base repository"""

    def __init__(self, settings):
        self.settings = settings
        self.pool: Optional[Pool] = None

    async def init_pool(self):
        """Initialize database connection pool"""
        try:
            self.pool = await aiomysql.create_pool(
                host=self.settings.db_host,
                port=self.settings.db_port,
                user=self.settings.db_user,
                password=self.settings.db_password,
                db=self.settings.db_name,
                charset='utf8mb4',
                autocommit=True,
                minsize=5,
                maxsize=20
            )
            logger.info("Database pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise

    async def close_pool(self):
        """Close database connection pool"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            logger.info("Database pool closed")

    async def execute(self, query: str, params: tuple = None) -> int:
        """Execute query and return affected rows"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, params)
                return cursor.rowcount

    async def fetchone(self, query: str, params: tuple = None) -> Optional[Dict]:
        """Fetch one row"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, params)
                return await cursor.fetchone()

    async def fetchall(self, query: str, params: tuple = None) -> List[Dict]:
        """Fetch all rows"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, params)
                return await cursor.fetchall()

    async def insert(self, query: str, params: tuple = None) -> int:
        """Insert and return last insert id"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, params)
                return cursor.lastrowid


class DatabaseRepository(BaseRepository):
    """Main database repository with all CRUD operations"""

    async def get_user(self, telegram_id: int) -> Optional[Dict]:
        """Get user by telegram ID"""
        return await self.fetchone(
            "SELECT * FROM users WHERE telegram_id = %s",
            (telegram_id,)
        )

    async def create_user(self, telegram_id: int, first_name: str = None, username: str = None, language: str = 'ru') -> int:
        """Create new user"""
        return await self.insert(
            "INSERT INTO users (telegram_id, first_name, username, language_code) VALUES (%s, %s, %s, %s)",
            (telegram_id, first_name, username, language)
        )

    async def update_user_state(self, telegram_id: int, state: str, data: Dict = None) -> int:
        """Update user state and data"""
        import json
        data_json = json.dumps(data) if data else None
        return await self.execute(
            "UPDATE users SET state = %s, state_data = %s WHERE telegram_id = %s",
            (state, data_json, telegram_id)
        )

    async def update_user_language(self, telegram_id: int, language: str) -> int:
        """Update user language"""
        return await self.execute(
            "UPDATE users SET language_code = %s WHERE telegram_id = %s",
            (language, telegram_id)
        )

    async def get_categories(self, type_filter: str = None) -> List[Dict]:
        """Get all categories, optionally filtered by type"""
        if type_filter:
            return await self.fetchall(
                "SELECT * FROM categories WHERE type = %s ORDER BY name_ru",
                (type_filter,)
            )
        return await self.fetchall("SELECT * FROM categories ORDER BY name_ru")

    async def get_brands(self, category_id: int = None) -> List[Dict]:
        """Get all brands, optionally filtered by category"""
        if category_id:
            return await self.fetchall(
                """SELECT * FROM brands
                   WHERE category_id = %s ORDER BY name""",
                (category_id,)
            )
        return await self.fetchall("SELECT * FROM brands ORDER BY name")

    async def create_advertisement(self, user_id: int, category_id: int, brand_id: int,
                                 model: str, price: int, description: str,
                                 phone: str, city: str, contact_phone: str, photo_path: str = None) -> int:
        """Create new advertisement"""
        return await self.insert(
            """INSERT INTO advertisements
               (user_id, category_id, brand_id, model, price, description, phone, city, contact_phone, photo_path, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())""",
            (user_id, category_id, brand_id, model, price, description, phone, city, contact_phone, photo_path)
        )

    async def get_advertisement(self, ad_id: int) -> Optional[Dict]:
        """Get advertisement by ID with related data"""
        return await self.fetchone(
            """SELECT a.*, c.name_ru as category_name, c.name_uz as category_name_uz,
                      b.name as brand_name, u.username
               FROM advertisements a
               JOIN categories c ON a.category_id = c.id
               JOIN brands b ON a.brand_id = b.id
               JOIN users u ON a.user_id = u.id
               WHERE a.id = %s""",
            (ad_id,)
        )

    async def get_user_advertisements(self, user_id: int, status: str = None) -> List[Dict]:
        """Get user advertisements with optional status filter"""
        if status:
            return await self.fetchall(
                """SELECT a.*, c.name_ru as category_name, b.name as brand_name
                   FROM advertisements a
                   JOIN categories c ON a.category_id = c.id
                   JOIN brands b ON a.brand_id = b.id
                   WHERE a.user_id = %s AND a.status = %s
                   ORDER BY a.created_at DESC""",
                (user_id, status)
            )
        return await self.fetchall(
            """SELECT a.*, c.name_ru as category_name, b.name as brand_name
               FROM advertisements a
               JOIN categories c ON a.category_id = c.id
               JOIN brands b ON a.brand_id = b.id
               WHERE a.user_id = %s
               ORDER BY a.created_at DESC""",
            (user_id,)
        )

    async def search_advertisements(self, category_id: int = None, brand_id: int = None,
                                  search_term: str = None, status: str = 'approved') -> List[Dict]:
        """Search advertisements with filters"""
        conditions = ["a.status = %s"]
        params = [status]

        if category_id:
            conditions.append("a.category_id = %s")
            params.append(category_id)

        if brand_id:
            conditions.append("a.brand_id = %s")
            params.append(brand_id)

        if search_term:
            conditions.append("(a.model LIKE %s OR a.description LIKE %s)")
            params.extend([f"%{search_term}%", f"%{search_term}%"])

        query = f"""
            SELECT a.*, c.name_ru as category_name, c.name_uz as category_name_uz,
                   b.name as brand_name, u.username
            FROM advertisements a
            JOIN categories c ON a.category_id = c.id
            JOIN brands b ON a.brand_id = b.id
            JOIN users u ON a.user_id = u.id
            WHERE {' AND '.join(conditions)}
            ORDER BY a.created_at DESC
            LIMIT 50
        """

        return await self.fetchall(query, tuple(params))

    async def update_advertisement_status(self, ad_id: int, status: str, rejection_reason: str = None) -> int:
        """Update advertisement status"""
        return await self.execute(
            "UPDATE advertisements SET status = %s, rejection_reason = %s, moderated_at = NOW() WHERE id = %s",
            (status, rejection_reason, ad_id)
        )

    async def add_to_favorites(self, user_id: int, ad_id: int) -> int:
        """Add advertisement to user favorites"""
        try:
            return await self.insert(
                "INSERT INTO favorites (user_id, advertisement_id, created_at) VALUES (%s, %s, NOW())",
                (user_id, ad_id)
            )
        except aiomysql.IntegrityError:
            return 0

    async def remove_from_favorites(self, user_id: int, ad_id: int) -> int:
        """Remove advertisement from user favorites"""
        return await self.execute(
            "DELETE FROM favorites WHERE user_id = %s AND advertisement_id = %s",
            (user_id, ad_id)
        )

    async def get_user_favorites(self, user_id: int) -> List[Dict]:
        """Get user favorite advertisements"""
        return await self.fetchall(
            """SELECT a.*, c.name_ru as category_name, c.name_uz as category_name_uz,
                      b.name as brand_name, u.username
               FROM favorites f
               JOIN advertisements a ON f.advertisement_id = a.id
               JOIN categories c ON a.category_id = c.id
               JOIN brands b ON a.brand_id = b.id
               JOIN users u ON a.user_id = u.id
               WHERE f.user_id = %s AND a.status = 'approved'
               ORDER BY f.created_at DESC""",
            (user_id,)
        )

    async def is_favorite(self, user_id: int, ad_id: int) -> bool:
        """Check if advertisement is in user favorites"""
        result = await self.fetchone(
            "SELECT 1 FROM favorites WHERE user_id = %s AND advertisement_id = %s",
            (user_id, ad_id)
        )
        return result is not None

    async def get_pending_advertisements(self) -> List[Dict]:
        """Get all pending advertisements for moderation"""
        return await self.fetchall(
            """SELECT a.*, c.name_ru as category_name, b.name as brand_name, u.username
               FROM advertisements a
               JOIN categories c ON a.category_id = c.id
               JOIN brands b ON a.brand_id = b.id
               JOIN users u ON a.user_id = u.id
               WHERE a.status = 'pending'
               ORDER BY a.created_at ASC"""
        )

    async def create_payment(self, user_id: int, ad_id: int, amount: int) -> int:
        """Create payment record"""
        return await self.insert(
            "INSERT INTO payments (user_id, advertisement_id, amount, status, created_at) VALUES (%s, %s, %s, 'pending', NOW())",
            (user_id, ad_id, amount)
        )

    async def update_payment_receipt(self, payment_id: int, receipt_path: str) -> int:
        """Update payment with receipt"""
        return await self.execute(
            "UPDATE payments SET receipt_path = %s, status = 'submitted' WHERE id = %s",
            (receipt_path, payment_id)
        )

    async def get_payment(self, payment_id: int) -> Optional[Dict]:
        """Get payment by ID"""
        return await self.fetchone(
            "SELECT * FROM payments WHERE id = %s",
            (payment_id,)
        )