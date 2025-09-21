import aiohttp
import asyncio
from typing import Dict, List, Optional, Union
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class TelegramService:
    """Service for Telegram API operations"""

    def __init__(self, config: settings):
        self.token = config.telegram_bot_token
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.session: Optional[aiohttp.ClientSession] = None
        self._session_timeout = aiohttp.ClientTimeout(total=30)

    async def __aenter__(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=self._session_timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    async def _ensure_session(self):
        """Ensure session is available and not closed"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=self._session_timeout)

    async def close(self):
        """Explicitly close the session"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    async def _make_request(self, method: str, **kwargs) -> Dict:
        """Make API request to Telegram"""
        url = f"{self.base_url}/{method}"

        await self._ensure_session()

        try:
            async with self.session.post(url, json=kwargs) as response:
                result = await response.json()

                if not result.get('ok'):
                    logger.error(f"Telegram API error: {result}")
                    raise Exception(f"Telegram API error: {result.get('description', 'Unknown error')}")

                return result['result']
        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error for {method}: {e}")
            raise
        except asyncio.TimeoutError as e:
            logger.error(f"Timeout error for {method}: {e}")
            raise
        except Exception as e:
            logger.error(f"Request to {method} failed: {e}")
            raise

    async def send_message(
        self,
        chat_id: Union[int, str],
        text: str,
        reply_markup: Optional[Dict] = None,
        parse_mode: str = "HTML",
        disable_web_page_preview: bool = True
    ) -> Dict:
        """Send text message"""
        params = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview
        }

        if reply_markup:
            params["reply_markup"] = reply_markup

        return await self._make_request("sendMessage", **params)

    async def edit_message_text(
        self,
        chat_id: Union[int, str],
        message_id: int,
        text: str,
        reply_markup: Optional[Dict] = None,
        parse_mode: str = "HTML"
    ) -> Dict:
        """Edit message text"""
        params = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": parse_mode
        }

        if reply_markup:
            params["reply_markup"] = reply_markup

        return await self._make_request("editMessageText", **params)

    async def edit_message_reply_markup(
        self,
        chat_id: Union[int, str],
        message_id: int,
        reply_markup: Optional[Dict] = None
    ) -> Dict:
        """Edit message reply markup"""
        return await self._make_request(
            "editMessageReplyMarkup",
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=reply_markup
        )

    async def delete_message(self, chat_id: Union[int, str], message_id: int) -> bool:
        """Delete message"""
        try:
            await self._make_request("deleteMessage", chat_id=chat_id, message_id=message_id)
            return True
        except Exception as e:
            logger.warning(f"Failed to delete message {message_id}: {e}")
            return False

    async def send_photo(
        self,
        chat_id: Union[int, str],
        photo: str,
        caption: str = None,
        reply_markup: Optional[Dict] = None,
        parse_mode: str = "HTML"
    ) -> Dict:
        """Send photo"""
        params = {
            "chat_id": chat_id,
            "photo": photo,
            "parse_mode": parse_mode
        }

        if caption:
            params["caption"] = caption

        if reply_markup:
            params["reply_markup"] = reply_markup

        return await self._make_request("sendPhoto", **params)

    async def send_photo_from_file(
        self,
        chat_id: Union[int, str],
        file_path: str,
        caption: str = None,
        reply_markup: Optional[Dict] = None,
        parse_mode: str = "HTML"
    ) -> Dict:
        """Send photo from local file path"""
        import os
        import json

        if not os.path.exists(file_path):
            raise Exception(f"File not found: {file_path}")

        url = f"{self.base_url}/sendPhoto"
        await self._ensure_session()

        try:
            # Read file content synchronously
            with open(file_path, 'rb') as f:
                file_content = f.read()

            # Prepare form data
            data = aiohttp.FormData()
            data.add_field('chat_id', str(chat_id))
            data.add_field('photo', file_content, filename=os.path.basename(file_path))
            data.add_field('parse_mode', parse_mode)

            if caption:
                data.add_field('caption', caption)

            if reply_markup:
                data.add_field('reply_markup', json.dumps(reply_markup))

            async with self.session.post(url, data=data) as response:
                result = await response.json()

                if not result.get('ok'):
                    logger.error(f"Telegram API error: {result}")
                    raise Exception(f"Telegram API error: {result.get('description', 'Unknown error')}")

                return result['result']

        except Exception as e:
            logger.error(f"Error sending photo from file {file_path}: {e}")
            raise

    async def get_file(self, file_id: str) -> Dict:
        """Get file info"""
        return await self._make_request("getFile", file_id=file_id)

    async def download_file(self, file_path: str) -> bytes:
        """Download file from Telegram servers"""
        url = f"https://api.telegram.org/file/bot{self.token}/{file_path}"

        # Create separate session with longer timeout for file downloads (10 minutes)
        download_timeout = aiohttp.ClientTimeout(total=600)

        async with aiohttp.ClientSession(timeout=download_timeout) as download_session:
            try:
                logger.info(f"Starting download from URL: {url}")
                async with download_session.get(url) as response:
                    logger.info(f"Got response status: {response.status} for file: {file_path}")
                    if response.status == 200:
                        content_length = response.headers.get('content-length')
                        logger.info(f"Content length: {content_length} bytes for file: {file_path}")

                        content = await response.read()
                        logger.info(f"Successfully downloaded file: {file_path}, size: {len(content)} bytes")
                        return content
                    else:
                        logger.error(f"Failed to download file {file_path}: HTTP {response.status}")
                        raise Exception(f"Failed to download file: {response.status}")
            except aiohttp.ClientError as e:
                logger.error(f"HTTP client error downloading file {file_path}: {e}")
                raise
            except asyncio.TimeoutError as e:
                logger.error(f"Timeout error downloading file {file_path}: {e}")
                raise
            except Exception as e:
                logger.error(f"Error downloading file {file_path}: {e}")
                raise

    async def answer_callback_query(
        self,
        callback_query_id: str,
        text: str = None,
        show_alert: bool = False
    ) -> Dict:
        """Answer callback query"""
        params = {
            "callback_query_id": callback_query_id,
            "show_alert": show_alert
        }

        if text:
            params["text"] = text

        return await self._make_request("answerCallbackQuery", **params)

    async def set_webhook(self, webhook_url: str) -> Dict:
        """Set webhook URL"""
        return await self._make_request("setWebhook", url=webhook_url)

    async def delete_webhook(self) -> Dict:
        """Delete webhook"""
        return await self._make_request("deleteWebhook")

    async def get_webhook_info(self) -> Dict:
        """Get webhook info"""
        return await self._make_request("getWebhookInfo")

    # Keyboard builders
    def build_inline_keyboard(self, buttons: List[List[Dict]]) -> Dict:
        """Build inline keyboard markup"""
        return {
            "inline_keyboard": buttons
        }

    def build_reply_keyboard(self, buttons: List[List[str]], resize: bool = True, one_time: bool = False) -> Dict:
        """Build reply keyboard markup"""
        keyboard = []
        for row in buttons:
            keyboard_row = []
            for button in row:
                keyboard_row.append({"text": button})
            keyboard.append(keyboard_row)

        return {
            "keyboard": keyboard,
            "resize_keyboard": resize,
            "one_time_keyboard": one_time
        }

    def build_remove_keyboard(self) -> Dict:
        """Build remove keyboard markup"""
        return {
            "remove_keyboard": True
        }

    async def broadcast_message(
        self,
        user_ids: List[int],
        text: str,
        reply_markup: Optional[Dict] = None
    ) -> Dict:
        """Broadcast message to multiple users"""
        successful = 0
        failed = 0
        failed_users = []

        tasks = []
        for user_id in user_ids:
            task = self._send_to_user(user_id, text, reply_markup)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed += 1
                failed_users.append(user_ids[i])
                logger.warning(f"Failed to send message to user {user_ids[i]}: {result}")
            else:
                successful += 1

        return {
            "successful": successful,
            "failed": failed,
            "failed_users": failed_users
        }

    async def _send_to_user(
        self,
        user_id: int,
        text: str,
        reply_markup: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Send message to single user (helper for broadcast)"""
        try:
            return await self.send_message(user_id, text, reply_markup)
        except Exception as e:
            logger.warning(f"Failed to send message to user {user_id}: {e}")
            raise e