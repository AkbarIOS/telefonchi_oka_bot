import aiomysql
import json
import os
import logging
from typing import Optional, Dict, List, Any
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.pool = None
        self.config = {
            'host': os.getenv('DB_HOST', 'mysql'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'db': os.getenv('DB_NAME', 'telegram_bot'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', 'root'),
            'charset': 'utf8mb4',
            'autocommit': True,
            'maxsize': 10,
            'minsize': 1,
        }

    async def init_pool(self):
        """Initialize connection pool"""
        try:
            self.pool = await aiomysql.create_pool(**self.config)
            logger.info("Database connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise

    async def close_pool(self):
        """Close connection pool"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            logger.info("Database connection pool closed")

    @asynccontextmanager
    async def get_connection(self):
        """Get database connection from pool"""
        if not self.pool:
            await self.init_pool()

        async with self.pool.acquire() as conn:
            yield conn

    async def execute(self, query: str, params: tuple = None) -> int:
        """Execute query and return affected rows"""
        async with self.get_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, params)
                return cursor.rowcount

    async def fetchone(self, query: str, params: tuple = None) -> Optional[Dict]:
        """Fetch one row"""
        async with self.get_connection() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, params)
                return await cursor.fetchone()

    async def fetchall(self, query: str, params: tuple = None) -> List[Dict]:
        """Fetch all rows"""
        async with self.get_connection() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, params)
                return await cursor.fetchall()

    # User operations
    async def get_user(self, telegram_id: int) -> Optional[Dict]:
        """Get user by telegram_id"""
        return await self.fetchone(
            "SELECT * FROM users WHERE telegram_id = %s",
            (telegram_id,)
        )

    async def create_user(self, user_data: Dict) -> int:
        """Create new user and return user ID"""
        async with self.get_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO users (telegram_id, first_name, username, language_code)
                    VALUES (%s, %s, %s, %s)
                """, (
                    user_data['telegram_id'],
                    user_data.get('first_name'),
                    user_data.get('username'),
                    user_data.get('language_code', 'ru')
                ))
                return cursor.lastrowid

    async def update_user(self, telegram_id: int, data: Dict) -> bool:
        """Update user data"""
        if not data:
            return False

        set_clauses = []
        values = []

        for key, value in data.items():
            set_clauses.append(f"{key} = %s")
            values.append(value)

        values.append(telegram_id)

        query = f"UPDATE users SET {', '.join(set_clauses)} WHERE telegram_id = %s"
        rows_affected = await self.execute(query, tuple(values))
        return rows_affected > 0

    async def get_all_users(self) -> List[Dict]:
        """Get all users"""
        return await self.fetchall("SELECT * FROM users ORDER BY created_at DESC")

    # Category operations
    async def get_categories(self) -> List[Dict]:
        """Get all active categories"""
        return await self.fetchall(
            "SELECT * FROM categories WHERE is_active = 1 ORDER BY id"
        )

    async def get_category(self, category_id: int) -> Optional[Dict]:
        """Get category by ID"""
        return await self.fetchone(
            "SELECT * FROM categories WHERE id = %s",
            (category_id,)
        )

    # Brand operations
    async def get_brands(self, category_id: int) -> List[Dict]:
        """Get brands by category"""
        return await self.fetchall(
            "SELECT * FROM brands WHERE category_id = %s AND is_active = 1 ORDER BY name",
            (category_id,)
        )

    async def get_brand(self, brand_id: int) -> Optional[Dict]:
        """Get brand by ID"""
        return await self.fetchone(
            "SELECT * FROM brands WHERE id = %s",
            (brand_id,)
        )

    # Temporary data operations
    async def get_temp_data(self, user_id: int) -> Dict:
        """Get temporary data for user"""
        result = await self.fetchone(
            "SELECT data FROM user_temp_data WHERE user_id = %s",
            (user_id,)
        )
        if result and result['data']:
            return json.loads(result['data'])
        return {}

    async def set_temp_data(self, user_id: int, data: Dict) -> bool:
        """Set temporary data for user"""
        rows_affected = await self.execute("""
            INSERT INTO user_temp_data (user_id, data)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE data = VALUES(data), updated_at = CURRENT_TIMESTAMP
        """, (user_id, json.dumps(data)))
        return rows_affected > 0

    async def clear_temp_data(self, user_id: int) -> bool:
        """Clear temporary data for user"""
        rows_affected = await self.execute(
            "DELETE FROM user_temp_data WHERE user_id = %s",
            (user_id,)
        )
        return rows_affected > 0

    # Advertisement operations
    async def create_advertisement(self, ad_data: Dict) -> Optional[int]:
        """Create new advertisement and return advertisement ID"""
        try:
            async with self.get_connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                        INSERT INTO advertisements
                        (user_id, category_id, brand_id, model, price, city, contact_phone, photo_path, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        ad_data['user_id'],
                        ad_data['category_id'],
                        ad_data['brand_id'],
                        ad_data['model'],
                        ad_data['price'],
                        ad_data['city'],
                        ad_data['contact_phone'],
                        ad_data.get('photo_path'),
                        ad_data.get('status', 'pending')
                    ))
                    return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error creating advertisement: {e}")
            return None

    async def get_advertisements(self, category_id: int = None, brand_id: int = None,
                                status: str = 'approved', limit: int = 10, offset: int = 0) -> List[Dict]:
        """Get advertisements with filters"""
        query = """
            SELECT a.*, u.first_name, u.username,
                   c.name_ru as category_name_ru, c.name_uz as category_name_uz,
                   c.icon as category_icon, b.name as brand_name
            FROM advertisements a
            JOIN users u ON a.user_id = u.id
            JOIN categories c ON a.category_id = c.id
            JOIN brands b ON a.brand_id = b.id
            WHERE a.status = %s
        """

        params = [status]

        if category_id:
            query += " AND a.category_id = %s"
            params.append(category_id)

        if brand_id:
            query += " AND a.brand_id = %s"
            params.append(brand_id)

        query += " ORDER BY a.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        return await self.fetchall(query, tuple(params))

    async def get_user_advertisements(self, user_id: int) -> List[Dict]:
        """Get advertisements by user"""
        return await self.fetchall("""
            SELECT a.*, c.name_ru as category_name_ru, c.name_uz as category_name_uz,
                   c.icon as category_icon, b.name as brand_name
            FROM advertisements a
            JOIN categories c ON a.category_id = c.id
            JOIN brands b ON a.brand_id = b.id
            WHERE a.user_id = %s
            ORDER BY a.created_at DESC
        """, (user_id,))

    async def update_advertisement_status(self, ad_id: int, status: str, rejection_reason: str = None) -> bool:
        """Update advertisement status"""
        if rejection_reason:
            rows_affected = await self.execute(
                "UPDATE advertisements SET status = %s, rejection_reason = %s WHERE id = %s",
                (status, rejection_reason, ad_id)
            )
        else:
            rows_affected = await self.execute(
                "UPDATE advertisements SET status = %s WHERE id = %s",
                (status, ad_id)
            )
        return rows_affected > 0

    # Favorites operations
    async def add_to_favorites(self, user_id: int, advertisement_id: int) -> bool:
        """Add advertisement to favorites"""
        try:
            await self.execute("""
                INSERT IGNORE INTO favorites (user_id, advertisement_id)
                VALUES (%s, %s)
            """, (user_id, advertisement_id))
            return True
        except Exception as e:
            logger.error(f"Error adding to favorites: {e}")
            return False

    async def remove_from_favorites(self, user_id: int, advertisement_id: int) -> bool:
        """Remove advertisement from favorites"""
        rows_affected = await self.execute("""
            DELETE FROM favorites WHERE user_id = %s AND advertisement_id = %s
        """, (user_id, advertisement_id))
        return rows_affected > 0

    async def get_user_favorites(self, user_id: int) -> List[Dict]:
        """Get user's favorite advertisements"""
        return await self.fetchall("""
            SELECT a.*, c.name_ru as category_name_ru, c.name_uz as category_name_uz,
                   c.icon as category_icon, b.name as brand_name
            FROM favorites f
            JOIN advertisements a ON f.advertisement_id = a.id
            JOIN categories c ON a.category_id = c.id
            JOIN brands b ON a.brand_id = b.id
            WHERE f.user_id = %s AND a.status = 'approved'
            ORDER BY f.created_at DESC
        """, (user_id,))

    async def is_favorite(self, user_id: int, advertisement_id: int) -> bool:
        """Check if advertisement is in user's favorites"""
        result = await self.fetchone(
            "SELECT 1 FROM favorites WHERE user_id = %s AND advertisement_id = %s",
            (user_id, advertisement_id)
        )
        return result is not None

    # Statistics
    async def get_stats(self) -> Dict[str, int]:
        """Get bot statistics"""
        stats = {}

        # Total users
        result = await self.fetchone("SELECT COUNT(*) as count FROM users")
        stats['total_users'] = result['count'] if result else 0

        # Total advertisements
        result = await self.fetchone("SELECT COUNT(*) as count FROM advertisements")
        stats['total_ads'] = result['count'] if result else 0

        # Pending advertisements
        result = await self.fetchone("SELECT COUNT(*) as count FROM advertisements WHERE status = 'pending'")
        stats['pending_ads'] = result['count'] if result else 0

        # Approved advertisements
        result = await self.fetchone("SELECT COUNT(*) as count FROM advertisements WHERE status = 'approved'")
        stats['approved_ads'] = result['count'] if result else 0

        # Total categories
        result = await self.fetchone("SELECT COUNT(*) as count FROM categories WHERE is_active = 1")
        stats['total_categories'] = result['count'] if result else 0

        # Total brands
        result = await self.fetchone("SELECT COUNT(*) as count FROM brands WHERE is_active = 1")
        stats['total_brands'] = result['count'] if result else 0

        return stats