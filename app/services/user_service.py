from typing import Optional, Dict, List
import json
import logging
from app.repositories.database import DatabaseRepository
from app.services.telegram_service import TelegramService

logger = logging.getLogger(__name__)


class UserService:
    """Service for user-related business logic"""

    def __init__(self, db_repository: DatabaseRepository, telegram_service: TelegramService):
        self.db = db_repository
        self.telegram = telegram_service

    async def get_or_create_user(self, telegram_id: int, first_name: str = None, username: str = None) -> Dict:
        """Get existing user or create new one"""
        user = await self.db.get_user(telegram_id)

        if not user:
            # Create new user with default language
            await self.db.create_user(
                telegram_id=telegram_id,
                first_name=first_name,
                username=username,
                language='ru'
            )
            user = await self.db.get_user(telegram_id)
            logger.info(f"Created new user: {telegram_id}")

        return user

    async def update_user_language(self, telegram_id: int, language: str) -> bool:
        """Update user's preferred language"""
        try:
            affected_rows = await self.db.update_user_language(telegram_id, language)
            return affected_rows > 0
        except Exception as e:
            logger.error(f"Failed to update user language: {e}")
            return False

    async def get_user_state(self, telegram_id: int) -> tuple[str, Dict]:
        """Get user's current state and state data"""
        user = await self.db.get_user(telegram_id)
        if not user:
            return 'start', {}

        state = user.get('state', 'start')
        state_data = user.get('state_data', '{}')

        try:
            if isinstance(state_data, str):
                state_data = json.loads(state_data) if state_data else {}
            elif state_data is None:
                state_data = {}
        except json.JSONDecodeError:
            logger.warning(f"Invalid state_data for user {telegram_id}: {state_data}")
            state_data = {}

        return state, state_data

    async def set_user_state(self, telegram_id: int, state: str, data: Dict = None) -> bool:
        """Set user's state and state data"""
        try:
            if data is None:
                data = {}

            affected_rows = await self.db.update_user_state(telegram_id, state, data)
            return affected_rows > 0
        except Exception as e:
            logger.error(f"Failed to update user state: {e}")
            return False

    async def clear_user_state(self, telegram_id: int) -> bool:
        """Clear user's state (set to start)"""
        return await self.set_user_state(telegram_id, 'start', {})

    async def get_user_language(self, telegram_id: int) -> str:
        """Get user's preferred language"""
        user = await self.db.get_user(telegram_id)
        return user.get('language_code', 'ru') if user else 'ru'

    async def get_user_favorites(self, telegram_id: int) -> List[Dict]:
        """Get user's favorite advertisements"""
        user = await self.db.get_user(telegram_id)
        if not user:
            return []

        return await self.db.get_user_favorites(user['id'])

    async def add_to_favorites(self, telegram_id: int, ad_id: int) -> bool:
        """Add advertisement to user's favorites"""
        try:
            user = await self.db.get_user(telegram_id)
            if not user:
                return False

            affected_rows = await self.db.add_to_favorites(user['id'], ad_id)
            return affected_rows > 0
        except Exception as e:
            logger.error(f"Failed to add to favorites: {e}")
            return False

    async def remove_from_favorites(self, telegram_id: int, ad_id: int) -> bool:
        """Remove advertisement from user's favorites"""
        try:
            user = await self.db.get_user(telegram_id)
            if not user:
                return False

            affected_rows = await self.db.remove_from_favorites(user['id'], ad_id)
            return affected_rows > 0
        except Exception as e:
            logger.error(f"Failed to remove from favorites: {e}")
            return False

    async def is_favorite(self, telegram_id: int, ad_id: int) -> bool:
        """Check if advertisement is in user's favorites"""
        try:
            user = await self.db.get_user(telegram_id)
            if not user:
                return False

            return await self.db.is_favorite(user['id'], ad_id)
        except Exception as e:
            logger.error(f"Failed to check favorite status: {e}")
            return False

    async def get_user_advertisements(self, telegram_id: int, status: str = None) -> List[Dict]:
        """Get user's advertisements"""
        try:
            user = await self.db.get_user(telegram_id)
            if not user:
                return []

            return await self.db.get_user_advertisements(user['id'], status)
        except Exception as e:
            logger.error(f"Failed to get user advertisements: {e}")
            return []

    async def update_state_data(self, telegram_id: int, key: str, value) -> bool:
        """Update specific key in user's state data"""
        try:
            current_state, state_data = await self.get_user_state(telegram_id)
            state_data[key] = value
            return await self.set_user_state(telegram_id, current_state, state_data)
        except Exception as e:
            logger.error(f"Failed to update state data: {e}")
            return False

    async def get_state_data_value(self, telegram_id: int, key: str, default=None):
        """Get specific value from user's state data"""
        try:
            _, state_data = await self.get_user_state(telegram_id)
            return state_data.get(key, default)
        except Exception as e:
            logger.error(f"Failed to get state data value: {e}")
            return default

    async def validate_user_action(self, telegram_id: int, required_state: str = None) -> bool:
        """Validate if user can perform an action based on their state"""
        try:
            current_state, _ = await self.get_user_state(telegram_id)

            if required_state and current_state != required_state:
                logger.warning(f"User {telegram_id} tried action from wrong state: {current_state}, required: {required_state}")
                return False

            return True
        except Exception as e:
            logger.error(f"Failed to validate user action: {e}")
            return False

    async def reset_user_workflow(self, telegram_id: int) -> bool:
        """Reset user's workflow to initial state"""
        try:
            return await self.clear_user_state(telegram_id)
        except Exception as e:
            logger.error(f"Failed to reset user workflow: {e}")
            return False