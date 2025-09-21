import os
import logging
import asyncio
from typing import Dict, Optional, Any
from app.services.user_service import UserService
from app.services.advertisement_service import AdvertisementService
from app.services.telegram_service import TelegramService
from app.utils.localization import LocalizationManager
from app.utils.keyboards import KeyboardBuilder

logger = logging.getLogger(__name__)


class BotHandler:
    """Main bot handler with proper separation of concerns"""

    def __init__(
        self,
        user_service: UserService,
        advertisement_service: AdvertisementService,
        telegram_service: TelegramService
    ):
        self.user_service = user_service
        self.advertisement_service = advertisement_service
        self.telegram_service = telegram_service
        self.localization = LocalizationManager()
        self.keyboards = KeyboardBuilder(self.localization)

    async def process_update(self, update: Dict) -> None:
        """Process incoming Telegram update"""
        try:
            logger.info(f"Bot handler processing update: {update.get('update_id', 'unknown')}")
            if 'message' in update:
                logger.info(f"Processing message: {update['message'].get('text', 'no text')}")
                await self._handle_message(update['message'])
            elif 'callback_query' in update:
                logger.info(f"Processing callback query: {update['callback_query'].get('data', 'no data')}")
                await self._handle_callback_query(update['callback_query'])
            else:
                logger.warning(f"Unknown update type: {update}")
        except Exception as e:
            logger.error(f"Error processing update: {e}")
            logger.exception("Full traceback:")

    async def _handle_message(self, message: Dict) -> None:
        """Handle text message"""
        try:
            chat_id = message['chat']['id']
            # Handle Pydantic conversion of 'from' to 'from_' (Python keyword)
            from_field = message.get('from_') or message.get('from')
            if not from_field:
                logger.warning(f"Message without 'from' field: {message}")
                return
            user_id = from_field['id']
            first_name = from_field.get('first_name')
            username = from_field.get('username')
            text = message.get('text', '')
        except KeyError as e:
            logger.error(f"Missing required field in message: {e}, message: {message}")
            return

        # Get or create user
        await self.user_service.get_or_create_user(user_id, first_name, username)

        # Get user state and language
        try:
            state, state_data = await self.user_service.get_user_state(user_id)
            # Ensure state_data is never None
            if state_data is None:
                state_data = {}
        except Exception as e:
            logger.error(f"Error getting user state: {e}")
            state, state_data = 'start', {}

        language = await self.user_service.get_user_language(user_id)

        # Handle commands
        if text.startswith('/'):
            await self._handle_command(chat_id, user_id, text, language)
            return

        # Handle photo uploads
        if 'photo' in message:
            await self._handle_photo(chat_id, user_id, message['photo'], state, state_data, language)
            return

        # Handle contact sharing
        if 'contact' in message:
            await self._handle_contact(chat_id, user_id, message['contact'], state, state_data, language)
            return

        # Handle text input based on current state
        await self._handle_text_input(chat_id, user_id, text, state, state_data, language)

    async def _handle_callback_query(self, callback_query: Dict) -> None:
        """Handle inline button callback"""
        try:
            query_id = callback_query['id']
            chat_id = callback_query['message']['chat']['id']
            # Handle Pydantic conversion of 'from' to 'from_' (Python keyword)
            from_field = callback_query.get('from_') or callback_query.get('from')
            if not from_field:
                logger.error(f"Callback query without 'from' field: {callback_query}")
                return
            user_id = from_field['id']
            data = callback_query['data']

            logger.info(f"Processing callback query from user {user_id} with data: {data}")
        except KeyError as e:
            logger.error(f"Missing required field in callback query: {e}, query: {callback_query}")
            return

        # Get user state and language
        try:
            state, state_data = await self.user_service.get_user_state(user_id)
            # Ensure state_data is never None
            if state_data is None:
                state_data = {}
        except Exception as e:
            logger.error(f"Error getting user state: {e}")
            state, state_data = 'start', {}

        language = await self.user_service.get_user_language(user_id)

        # Answer callback query early to prevent timeout
        try:
            await self.telegram_service.answer_callback_query(query_id)
        except Exception as e:
            logger.warning(f"Failed to answer callback query {query_id}: {e}")
            # Continue processing even if callback answer fails

        # Handle callback data
        if data == 'home':
            await self._show_main_menu(chat_id, user_id, language)
        elif data == 'back':
            await self._handle_back_button(chat_id, user_id, state, state_data, language)
        elif data.startswith('lang_'):
            await self._handle_language_change(chat_id, user_id, data, language)
        elif data == 'sell':
            await self._start_sell_workflow(chat_id, user_id, language)
        elif data == 'buy':
            await self._start_buy_workflow(chat_id, user_id, language)
        elif data.startswith('sell_category_'):
            await self._handle_sell_category_selection(chat_id, user_id, data, language)
        elif data.startswith('buy_category_'):
            await self._handle_buy_category_selection(chat_id, user_id, data, language)
        elif data.startswith('sell_brand_'):
            await self._handle_sell_brand_selection(chat_id, user_id, data, state_data, language)
        elif data.startswith('buy_brand_'):
            await self._handle_buy_brand_selection(chat_id, user_id, data, state_data, language)
        elif data.startswith('view_ad_'):
            await self._handle_view_advertisement(chat_id, user_id, data, language)
        elif data.startswith('favorite_'):
            await self._handle_favorite_toggle(chat_id, user_id, data, language)
        elif data == 'my_favorites':
            await self._show_favorites(chat_id, user_id, language)
        elif data == 'my_ads':
            await self._show_my_advertisements(chat_id, user_id, language)
        elif data == 'language':
            await self._show_language_menu(chat_id, user_id, language)
        elif data == 'help':
            await self._show_help(chat_id, user_id, language)
        elif data.startswith('my_ads_page_'):
            page = int(data.split('_')[-1])
            await self._handle_my_ads_pagination(chat_id, user_id, page, language)
        elif data.startswith('mark_sold_'):
            ad_id = int(data.split('_')[-1])
            await self._handle_mark_sold(chat_id, user_id, ad_id, language)
        elif data == 'payment_confirmed':
            await self._handle_payment_confirmed(chat_id, user_id, state_data, language)
        elif data.startswith('approve_'):
            await self._handle_approve_advertisement(chat_id, user_id, data, language)
        elif data.startswith('reject_'):
            await self._handle_reject_advertisement(chat_id, user_id, data, language)
        elif data == 'show_pending_ads':
            await self._show_pending_advertisements(chat_id, user_id, language)
        else:
            logger.warning(f"Unknown callback data: {data}")

    async def _handle_command(self, chat_id: int, user_id: int, command: str, language: str) -> None:
        """Handle bot commands"""
        if command == '/start':
            await self._show_main_menu(chat_id, user_id, language)
        elif command == '/language':
            await self._show_language_menu(chat_id, user_id, language)
        elif command == '/help':
            await self._show_help(chat_id, user_id, language)
        elif command == '/admin' or command == '/moderate':
            await self._handle_admin_command(chat_id, user_id, language)
        else:
            await self.telegram_service.send_message(
                chat_id,
                self.localization.get_text('unknown_command', language),
                self.keyboards.get_main_menu(language)
            )

    async def _show_main_menu(self, chat_id: int, user_id: int, language: str) -> None:
        """Show main menu"""
        await self.user_service.clear_user_state(user_id)

        text = self.localization.get_text('main_menu', language)
        keyboard = self.keyboards.get_main_menu(language)

        await self.telegram_service.send_message(chat_id, text, keyboard)

    async def _start_sell_workflow(self, chat_id: int, user_id: int, language: str) -> None:
        """Start selling workflow"""
        categories = await self.advertisement_service.get_categories()

        if not categories:
            await self.telegram_service.send_message(
                chat_id,
                self.localization.get_text('no_categories', language)
            )
            return

        await self.user_service.set_user_state(user_id, 'sell_select_category', {})

        text = self.localization.get_text('select_category_sell', language)
        keyboard = self.keyboards.get_categories_keyboard(categories, 'sell', language)

        await self.telegram_service.send_message(chat_id, text, keyboard)

    async def _start_buy_workflow(self, chat_id: int, user_id: int, language: str) -> None:
        """Start buying workflow"""
        categories = await self.advertisement_service.get_categories()

        if not categories:
            await self.telegram_service.send_message(
                chat_id,
                self.localization.get_text('no_categories', language)
            )
            return

        await self.user_service.set_user_state(user_id, 'buy_select_category', {})

        text = self.localization.get_text('select_category_buy', language)
        keyboard = self.keyboards.get_categories_keyboard(categories, 'buy', language)

        await self.telegram_service.send_message(chat_id, text, keyboard)

    async def _handle_sell_category_selection(self, chat_id: int, user_id: int, data: str, language: str) -> None:
        """Handle category selection for selling"""
        category_id = int(data.split('_')[2])
        brands = await self.advertisement_service.get_brands(category_id)

        if not brands:
            await self.telegram_service.send_message(
                chat_id,
                self.localization.get_text('no_brands', language)
            )
            return

        await self.user_service.set_user_state(user_id, 'sell_select_brand', {'category_id': category_id})

        text = self.localization.get_text('select_brand', language)
        keyboard = self.keyboards.get_brands_keyboard(brands, 'sell', language)

        await self.telegram_service.send_message(chat_id, text, keyboard)

    async def _handle_buy_category_selection(self, chat_id: int, user_id: int, data: str, language: str) -> None:
        """Handle category selection for buying"""
        category_id = int(data.split('_')[2])

        # Search advertisements in this category
        advertisements = await self.advertisement_service.search_buy_advertisements(category_id=category_id)

        if not advertisements:
            text = self.localization.get_text('no_ads_found', language)
            keyboard = self.keyboards.get_back_home_keyboard(language)
            await self.telegram_service.send_message(chat_id, text, keyboard)
            return

        await self.user_service.set_user_state(user_id, 'buy_viewing', {'category_id': category_id})
        await self._show_advertisements_list(chat_id, user_id, advertisements, language)

    async def _handle_sell_brand_selection(self, chat_id: int, user_id: int, data: str, state_data: Dict, language: str) -> None:
        """Handle brand selection for selling"""
        brand_id = int(data.split('_')[2])
        category_id = state_data.get('category_id')

        await self.user_service.set_user_state(
            user_id,
            'sell_enter_model',
            {'category_id': category_id, 'brand_id': brand_id}
        )

        text = self.localization.get_text('enter_model', language)
        keyboard = self.keyboards.get_back_home_keyboard(language)

        await self.telegram_service.send_message(chat_id, text, keyboard)

    async def _handle_buy_brand_selection(self, chat_id: int, user_id: int, data: str, state_data: Dict, language: str) -> None:
        """Handle brand selection for buying"""
        brand_id = int(data.split('_')[2])
        category_id = state_data.get('category_id')

        # Search advertisements with both category and brand
        advertisements = await self.advertisement_service.search_buy_advertisements(
            category_id=category_id,
            brand_id=brand_id
        )

        if not advertisements:
            text = self.localization.get_text('no_ads_found', language)
            keyboard = self.keyboards.get_back_home_keyboard(language)
            await self.telegram_service.send_message(chat_id, text, keyboard)
            return

        await self.user_service.set_user_state(
            user_id,
            'buy_viewing',
            {'category_id': category_id, 'brand_id': brand_id}
        )
        await self._show_advertisements_list(chat_id, user_id, advertisements, language)

    async def _handle_text_input(self, chat_id: int, user_id: int, text: str, state: str, state_data: Dict, language: str) -> None:
        """Handle text input based on current state"""
        if state == 'sell_enter_model':
            await self._process_model_input(chat_id, user_id, text, state_data, language)
        elif state == 'sell_enter_price':
            await self._process_price_input(chat_id, user_id, text, state_data, language)
        elif state == 'sell_enter_description':
            await self._process_description_input(chat_id, user_id, text, state_data, language)
        elif state == 'sell_enter_city':
            await self._process_city_input(chat_id, user_id, text, state_data, language)
        elif state == 'sell_waiting_photo':
            text = self.localization.get_text('waiting_for_photo', language)
            await self.telegram_service.send_message(chat_id, text)
        elif state == 'sell_waiting_phone':
            await self._process_phone_input(chat_id, user_id, text, state_data, language)
        else:
            # Default: show main menu for unhandled states
            await self._show_main_menu(chat_id, user_id, language)

    async def _process_model_input(self, chat_id: int, user_id: int, model: str, state_data: Dict, language: str) -> None:
        """Process model input"""
        state_data['model'] = model
        await self.user_service.set_user_state(user_id, 'sell_enter_price', state_data)

        text = self.localization.get_text('enter_price', language)
        keyboard = self.keyboards.get_back_home_keyboard(language)

        await self.telegram_service.send_message(chat_id, text, keyboard)

    async def _process_price_input(self, chat_id: int, user_id: int, price_text: str, state_data: Dict, language: str) -> None:
        """Process price input"""
        try:
            price = int(price_text.replace(' ', '').replace(',', ''))
            if price <= 0:
                raise ValueError("Price must be positive")

            state_data['price'] = price
            await self.user_service.set_user_state(user_id, 'sell_enter_description', state_data)

            text = self.localization.get_text('enter_description', language)
            keyboard = self.keyboards.get_back_home_keyboard(language)

            await self.telegram_service.send_message(chat_id, text, keyboard)

        except ValueError:
            text = self.localization.get_text('invalid_price', language)
            await self.telegram_service.send_message(chat_id, text)

    async def _process_description_input(self, chat_id: int, user_id: int, description: str, state_data: Dict, language: str) -> None:
        """Process description input"""
        if len(description) < 10:
            text = self.localization.get_text('description_too_short', language)
            await self.telegram_service.send_message(chat_id, text)
            return

        state_data['description'] = description
        await self.user_service.set_user_state(user_id, 'sell_enter_city', state_data)

        text = self.localization.get_text('enter_city', language)
        await self.telegram_service.send_message(chat_id, text)

    async def _process_city_input(self, chat_id: int, user_id: int, city: str, state_data: Dict, language: str) -> None:
        """Process city input"""
        if len(city.strip()) < 2:
            text = self.localization.get_text('city_too_short', language)
            await self.telegram_service.send_message(chat_id, text)
            return

        state_data['city'] = city.strip()
        await self.user_service.set_user_state(user_id, 'sell_waiting_photo', state_data)

        text = self.localization.get_text('send_photo', language)
        keyboard = self.keyboards.get_back_home_keyboard(language)
        await self.telegram_service.send_message(chat_id, text, keyboard)

    async def _handle_photo(self, chat_id: int, user_id: int, photos: list, state: str, state_data: Dict, language: str) -> None:
        """Handle photo upload"""
        if state == 'sell_waiting_photo':
            await self._handle_advertisement_photo(chat_id, user_id, photos, state_data, language)
        elif state == 'waiting_receipt':
            await self._handle_receipt_photo(chat_id, user_id, photos, state_data, language)
        else:
            logger.warning(f"Photo received for user {user_id} but state is {state}, not expected photo state")
            return

    async def _handle_advertisement_photo(self, chat_id: int, user_id: int, photos: list, state_data: Dict, language: str) -> None:
        """Handle advertisement photo upload"""

        try:
            logger.info(f"Processing photo upload for user {user_id}")

            # Get the highest quality photo
            photo = photos[-1]
            logger.info(f"Photo file_id: {photo['file_id']}")

            # Get file info with error handling
            try:
                file_info = await self.telegram_service.get_file(photo['file_id'])
                logger.info(f"Got file info: {file_info.get('file_path', 'no path')}")
            except Exception as e:
                logger.error(f"Failed to get file info for {photo['file_id']}: {e}")
                raise Exception(f"Failed to get file info: {e}")

            # Download file with error handling
            try:
                file_content = await self.telegram_service.download_file(file_info['file_path'])
                logger.info(f"Downloaded file, size: {len(file_content)} bytes")
            except Exception as e:
                logger.error(f"Failed to download file {file_info['file_path']}: {e}")
                raise Exception(f"Failed to download file: {e}")

            # Save photo
            try:
                success, photo_path = await self.advertisement_service.save_uploaded_photo(
                    file_content,
                    '.jpg'
                )
                logger.info(f"Save photo result: success={success}, path={photo_path}")
            except Exception as e:
                logger.error(f"Failed to save photo: {e}")
                raise Exception(f"Failed to save photo: {e}")

            if success:
                state_data['photo_path'] = photo_path
                await self.user_service.set_user_state(user_id, 'sell_waiting_phone', state_data)

                text = self.localization.get_text('send_phone', language)
                keyboard = self.keyboards.get_contact_keyboard(language)

                await self.telegram_service.send_message(chat_id, text, keyboard)
                logger.info(f"Successfully processed photo upload for user {user_id}")
            else:
                text = self.localization.get_text('photo_upload_error', language)
                await self.telegram_service.send_message(chat_id, text)
                logger.error(f"Photo save failed for user {user_id}: {photo_path}")

        except asyncio.TimeoutError as e:
            logger.error(f"Timeout error handling photo for user {user_id}: {e}")
            text = self.localization.get_text('photo_upload_timeout', language)
            await self.telegram_service.send_message(chat_id, text)
        except Exception as e:
            logger.error(f"Error handling photo for user {user_id}: {e}")
            logger.exception("Full photo handling error traceback:")

            # Check if the error is due to timeout
            if "TimeoutError" in str(e) or "timeout" in str(e).lower():
                text = self.localization.get_text('photo_upload_timeout', language)
                await self.telegram_service.send_message(chat_id, text)
            else:
                text = self.localization.get_text('photo_upload_error', language)
                await self.telegram_service.send_message(chat_id, text)

    async def _handle_receipt_photo(self, chat_id: int, user_id: int, photos: list, state_data: Dict, language: str) -> None:
        """Handle receipt photo upload"""
        try:
            logger.info(f"Processing receipt upload for user {user_id}")

            # Get the highest quality photo
            photo = photos[-1]
            logger.info(f"Receipt photo file_id: {photo['file_id']}")

            # Get file info with error handling
            try:
                file_info = await self.telegram_service.get_file(photo['file_id'])
                logger.info(f"Got receipt file info: {file_info.get('file_path', 'no path')}")
            except Exception as e:
                logger.error(f"Failed to get receipt file info for {photo['file_id']}: {e}")
                raise Exception(f"Failed to get receipt file info: {e}")

            # Download file with error handling
            try:
                file_content = await self.telegram_service.download_file(file_info['file_path'])
                logger.info(f"Downloaded receipt file, size: {len(file_content)} bytes")
            except Exception as e:
                logger.error(f"Failed to download receipt file {file_info['file_path']}: {e}")
                raise Exception(f"Failed to download receipt file: {e}")

            # Save receipt
            try:
                success, receipt_path = await self.advertisement_service.save_uploaded_photo(
                    file_content,
                    '.jpg'
                )
                logger.info(f"Save receipt result: success={success}, path={receipt_path}")
            except Exception as e:
                logger.error(f"Failed to save receipt: {e}")
                raise Exception(f"Failed to save receipt: {e}")

            if success:
                # Now create the advertisement with all the data
                await self._create_advertisement_with_receipt(chat_id, user_id, state_data, receipt_path, language)
            else:
                text = self.localization.get_text('photo_upload_error', language)
                await self.telegram_service.send_message(chat_id, text)
                logger.error(f"Receipt save failed for user {user_id}: {receipt_path}")

        except Exception as e:
            logger.error(f"Error handling receipt for user {user_id}: {e}")
            logger.exception("Full receipt handling error traceback:")
            text = self.localization.get_text('photo_upload_error', language)
            await self.telegram_service.send_message(chat_id, text)

    async def _create_advertisement_with_receipt(self, chat_id: int, user_id: int, state_data: Dict, receipt_path: str, language: str) -> None:
        """Create advertisement after receipt is uploaded"""
        try:
            # Get user data
            user = await self.user_service.db.get_user(user_id)
            if not user:
                return

            # Create advertisement
            success, ad_id, message = await self.advertisement_service.create_sell_advertisement(
                user_id=user['id'],
                category_id=state_data['category_id'],
                brand_id=state_data['brand_id'],
                model=state_data['model'],
                price=state_data['price'],
                description=state_data['description'],
                phone=state_data['phone'],
                city=state_data['city'],
                contact_phone=state_data['contact_phone'],
                photo_path=state_data.get('photo_path')
            )

            if success:
                # Clear user state
                await self.user_service.clear_user_state(user_id)

                # Show success message
                text = self.localization.get_text('ad_created_success', language)
                keyboard = self.keyboards.get_main_menu(language)
                await self.telegram_service.send_message(chat_id, text, keyboard)

                logger.info(f"Successfully created advertisement {ad_id} for user {user_id} with receipt {receipt_path}")
            else:
                text = self.localization.get_text('ad_creation_error', language)
                await self.telegram_service.send_message(chat_id, text)

        except Exception as e:
            logger.error(f"Error creating advertisement with receipt: {e}")
            text = self.localization.get_text('ad_creation_error', language)
            await self.telegram_service.send_message(chat_id, text)

    async def _handle_contact(self, chat_id: int, user_id: int, contact: Dict, state: str, state_data: Dict, language: str) -> None:
        """Handle contact sharing"""
        if state != 'sell_waiting_phone':
            return

        phone = contact['phone_number']
        await self._finalize_advertisement(chat_id, user_id, phone, state_data, language)

    async def _process_phone_input(self, chat_id: int, user_id: int, phone: str, state_data: Dict, language: str) -> None:
        """Process manual phone input"""
        await self._finalize_advertisement(chat_id, user_id, phone, state_data, language)

    async def _finalize_advertisement(self, chat_id: int, user_id: int, phone: str, state_data: Dict, language: str) -> None:
        """Show payment instructions before creating advertisement"""
        try:
            # Get user data
            user = await self.user_service.db.get_user(user_id)
            if not user:
                return

            # Save advertisement data and set state for payment
            state_data['phone'] = phone
            state_data['contact_phone'] = phone
            await self.user_service.set_user_state(user_id, 'waiting_payment', state_data)

            # Remove reply keyboard
            await self.telegram_service.send_message(
                chat_id,
                self.localization.get_text('phone_received', language),
                self.keyboards.get_remove_keyboard()
            )

            # Show payment instructions with "Оплачено" button
            text = self.localization.get_text('payment_instructions', language).format(
                price=self.advertisement_service.config.advertisement_price,
                card_number=self.advertisement_service.config.payment_card_number
            )
            keyboard = self.keyboards.get_payment_confirm_keyboard(language)

            await self.telegram_service.send_message(chat_id, text, keyboard)

        except Exception as e:
            logger.error(f"Error showing payment instructions: {e}")
            text = self.localization.get_text('ad_creation_error', language)
            await self.telegram_service.send_message(chat_id, text)

    async def _handle_payment_confirmed(self, chat_id: int, user_id: int, state_data: Dict, language: str) -> None:
        """Handle payment confirmation - ask for receipt"""
        try:
            # Set state to waiting for receipt
            await self.user_service.set_user_state(user_id, 'waiting_receipt', state_data)

            # Ask for receipt screenshot
            text = self.localization.get_text('send_receipt', language)
            await self.telegram_service.send_message(chat_id, text)

        except Exception as e:
            logger.error(f"Error handling payment confirmation: {e}")
            text = self.localization.get_text('ad_creation_error', language)
            await self.telegram_service.send_message(chat_id, text)

    async def _show_advertisements_list(self, chat_id: int, user_id: int, advertisements: list, language: str) -> None:
        """Show list of advertisements"""
        if not advertisements:
            text = self.localization.get_text('no_ads_found', language)
            keyboard = self.keyboards.get_back_home_keyboard(language)
            await self.telegram_service.send_message(chat_id, text, keyboard)
            return

        text = self.localization.get_text('found_ads', language).format(count=len(advertisements))

        for ad in advertisements[:10]:  # Show first 10 ads
            ad_text = await self.advertisement_service.format_advertisement_text(ad, language)
            keyboard = self.keyboards.get_advertisement_keyboard(ad['id'], user_id, language)

            photo_path = ad.get('photo_path')
            if photo_path:
                try:
                    # Convert photo path to URL for Telegram
                    if photo_path.startswith('/static/'):
                        # New format: already a URL path, make it a full URL
                        photo_url = f"https://telefonchi-backend-working.loca.lt{photo_path}"
                        await self.telegram_service.send_photo(
                            chat_id, photo_url, ad_text, keyboard
                        )
                    elif photo_path.startswith('/app/uploads/'):
                        # Old format: convert to new format
                        filename = photo_path.split('/')[-1]
                        photo_url = f"https://telefonchi-backend-working.loca.lt/static/uploads/{filename}"
                        await self.telegram_service.send_photo(
                            chat_id, photo_url, ad_text, keyboard
                        )
                    elif os.path.exists(photo_path):
                        # Fallback: try as file path
                        await self.telegram_service.send_photo_from_file(
                            chat_id, photo_path, ad_text, keyboard
                        )
                    else:
                        # No photo, send text only
                        await self.telegram_service.send_message(chat_id, ad_text, keyboard)
                except Exception as e:
                    logger.error(f"Error sending photo {photo_path}: {e}")
                    # Fallback to text message
                    await self.telegram_service.send_message(chat_id, ad_text, keyboard)
            else:
                await self.telegram_service.send_message(chat_id, ad_text, keyboard)

    async def _handle_language_change(self, chat_id: int, user_id: int, data: str, current_language: str) -> None:
        """Handle language change"""
        new_language = data.split('_')[1]
        success = await self.user_service.update_user_language(user_id, new_language)

        if success:
            text = self.localization.get_text('language_changed', new_language)
            await self.telegram_service.send_message(chat_id, text)
            await self._show_main_menu(chat_id, user_id, new_language)
        else:
            text = self.localization.get_text('language_change_error', current_language)
            await self.telegram_service.send_message(chat_id, text)

    async def _show_language_menu(self, chat_id: int, user_id: int, language: str) -> None:
        """Show language selection menu"""
        text = self.localization.get_text('select_language', language)
        keyboard = self.keyboards.get_language_keyboard()

        await self.telegram_service.send_message(chat_id, text, keyboard)

    async def _show_help(self, chat_id: int, user_id: int, language: str) -> None:
        """Show help message"""
        text = self.localization.get_text('help_message', language)
        keyboard = self.keyboards.get_main_menu(language)

        await self.telegram_service.send_message(chat_id, text, keyboard)

    async def _handle_back_button(self, chat_id: int, user_id: int, state: str, state_data: Dict, language: str) -> None:
        """Handle back button navigation"""
        if state.startswith('sell_'):
            if state == 'sell_select_category':
                await self._show_main_menu(chat_id, user_id, language)
            elif state == 'sell_select_brand':
                await self._start_sell_workflow(chat_id, user_id, language)
            elif state in ['sell_enter_model', 'sell_enter_price', 'sell_enter_description', 'sell_enter_city', 'sell_waiting_photo', 'sell_waiting_phone']:
                await self._handle_sell_category_selection(
                    chat_id, user_id,
                    f"sell_category_{state_data.get('category_id', 0)}",
                    language
                )
        elif state.startswith('buy_'):
            if state == 'buy_select_category':
                await self._show_main_menu(chat_id, user_id, language)
            elif state == 'buy_viewing':
                await self._start_buy_workflow(chat_id, user_id, language)
        else:
            await self._show_main_menu(chat_id, user_id, language)

    async def _show_my_advertisements(self, chat_id: int, user_id: int, language: str) -> None:
        """Show user's advertisements with immediate display"""
        logger.info(f"_show_my_advertisements called for user {user_id}")
        try:
            # Get all user advertisements immediately using user service (handles telegram_id -> user_id conversion)
            all_ads = []

            # Get each status separately and ensure they're lists
            for status in ['pending', 'approved', 'rejected']:
                try:
                    ads = await self.user_service.get_user_advertisements(user_id, status)
                    if ads:
                        # Convert to list if it's not already
                        if not isinstance(ads, list):
                            ads = list(ads) if ads else []
                        all_ads.extend(ads)
                except Exception as e:
                    logger.error(f"Error getting {status} ads for user {user_id}: {e}")
                    continue

            logger.info(f"Total ads found: {len(all_ads)} for user {user_id}")

            if all_ads:
                # Show ads one by one as cards with pagination
                await self._show_ad_cards(chat_id, user_id, all_ads, 0, language, is_my_ads=True)
            else:
                no_ads_text = self.localization.get_text('no_ads_found', language)
                keyboard = self.keyboards.get_back_home_keyboard(language)
                await self.telegram_service.send_message(chat_id, no_ads_text, keyboard)

        except Exception as e:
            logger.error(f"Error showing user advertisements: {e}")
            text = "❌ Ошибка получения объявлений / Xatolik yuz berdi"
            keyboard = self.keyboards.get_back_home_keyboard(language)
            await self.telegram_service.send_message(chat_id, text, keyboard)

    async def _show_ad_cards(self, chat_id: int, user_id: int, ads: list, page: int, language: str, is_my_ads: bool = False) -> None:
        """Show advertisements as individual cards with pagination"""
        try:
            logger.info(f"_show_ad_cards called: page={page}, total_ads={len(ads)}, is_my_ads={is_my_ads}")

            if not ads or page < 0 or page >= len(ads):
                logger.warning(f"Invalid page or no ads: ads_count={len(ads) if ads else 0}, page={page}")
                no_ads_text = self.localization.get_text('no_ads_found', language)
                keyboard = self.keyboards.get_back_home_keyboard(language)
                await self.telegram_service.send_message(chat_id, no_ads_text, keyboard)
                return

            ad = ads[page]
            logger.info(f"Processing ad: id={ad.get('id')}, model={ad.get('model')}, status={ad.get('status')}")

            # Format advertisement text
            try:
                ad_text = await self.advertisement_service.format_advertisement_text(ad, language)
                logger.info(f"Advertisement text formatted successfully")

                # Add status information for My Ads
                if is_my_ads:
                    status_emoji = "⏳" if ad.get('status') == 'pending' else "✅" if ad.get('status') == 'approved' else "❌"
                    status_text = {
                        'pending': 'На модерации' if language == 'ru' else 'Moderatsiyada',
                        'approved': 'Одобрено' if language == 'ru' else 'Tasdiqlangan',
                        'rejected': 'Отклонено' if language == 'ru' else 'Rad etilgan'
                    }.get(ad.get('status'), str(ad.get('status', 'Unknown')))

                    ad_text += f"\n\n{status_emoji} <b>Статус:</b> {status_text}"

            except Exception as e:
                logger.error(f"Error formatting advertisement: {e}")
                logger.exception("Full ad formatting error traceback:")
                ad_text = "❌ Ошибка отображения объявления / E'lonni ko'rsatishda xatolik"

            # Create pagination keyboard
            try:
                keyboard = self._get_my_ads_card_keyboard(page, len(ads), ad.get('id'), ad.get('status'), language)
                logger.info(f"Keyboard created successfully: {keyboard}")
            except Exception as e:
                logger.error(f"Error creating keyboard: {e}")
                logger.exception("Full keyboard creation error traceback:")
                keyboard = self.keyboards.get_back_home_keyboard(language)

            # Send with photo if available
            photo_path = ad.get('photo_path')
            logger.info(f"Photo path: {photo_path}")

            if photo_path:
                try:
                    # Convert photo path to URL for Telegram
                    if photo_path.startswith('/static/'):
                        # New format: already a URL path, make it a full URL
                        photo_url = f"https://telefonchi-backend-working.loca.lt{photo_path}"
                        logger.info(f"Using photo URL: {photo_url}")
                        await self.telegram_service.send_photo(
                            chat_id=chat_id,
                            photo=photo_url,
                            caption=ad_text,
                            reply_markup=keyboard
                        )
                    elif photo_path.startswith('/app/uploads/'):
                        # Old format: convert to new format
                        filename = photo_path.split('/')[-1]
                        photo_url = f"https://telefonchi-backend-working.loca.lt/static/uploads/{filename}"
                        logger.info(f"Converted old path to URL: {photo_url}")
                        await self.telegram_service.send_photo(
                            chat_id=chat_id,
                            photo=photo_url,
                            caption=ad_text,
                            reply_markup=keyboard
                        )
                    else:
                        # Fallback: try as file path
                        logger.info(f"Using file path for photo")
                        await self.telegram_service.send_photo_from_file(
                            chat_id=chat_id,
                            file_path=photo_path,
                            caption=ad_text,
                            reply_markup=keyboard
                        )
                    logger.info(f"Photo message sent successfully")
                except Exception as e:
                    logger.error(f"Error sending photo {photo_path}: {e}")
                    logger.exception("Full photo sending error traceback:")
                    # Fallback to text message
                    await self.telegram_service.send_message(chat_id, ad_text, keyboard)
            else:
                logger.info(f"Sending text message (no photo)")
                await self.telegram_service.send_message(chat_id, ad_text, keyboard)
                logger.info(f"Text message sent successfully")

        except Exception as e:
            logger.error(f"Error in _show_ad_cards: {e}")
            logger.exception("Full _show_ad_cards error traceback:")
            text = "❌ Ошибка загрузки объявления / E'lonni yuklashda xatolik"
            keyboard = self.keyboards.get_back_home_keyboard(language)
            await self.telegram_service.send_message(chat_id, text, keyboard)

    def _get_my_ads_card_keyboard(self, current_page: int, total_ads: int, ad_id: int, ad_status: str, language: str) -> dict:
        """Get keyboard for My Ads card with pagination and actions"""
        keyboard = []

        # Add Sold button for approved ads
        if ad_status == 'approved':
            sold_text = "🔴 Продано" if language == 'ru' else "🔴 Sotildi"
            keyboard.append([{"text": sold_text, "callback_data": f"mark_sold_{ad_id}"}])

        # Pagination row
        nav_row = []
        if current_page > 0:
            nav_row.append({"text": "⬅️", "callback_data": f"my_ads_page_{current_page - 1}"})

        nav_row.append({"text": f"{current_page + 1}/{total_ads}", "callback_data": "noop"})

        if current_page < total_ads - 1:
            nav_row.append({"text": "➡️", "callback_data": f"my_ads_page_{current_page + 1}"})

        if nav_row:
            keyboard.append(nav_row)

        # Back and home buttons
        back_text = self.localization.get_text('back_button', language)
        home_text = self.localization.get_text('home_button', language)
        keyboard.append([
            {"text": back_text, "callback_data": "back"},
            {"text": home_text, "callback_data": "home"}
        ])

        return {"inline_keyboard": keyboard}

    async def _show_favorites(self, chat_id: int, user_id: int, language: str) -> None:
        """Show user's favorite advertisements"""
        text = self.localization.get_text('my_favorites', language)
        keyboard = self.keyboards.get_back_home_keyboard(language)
        await self.telegram_service.send_message(chat_id, text, keyboard)

    async def _handle_my_ads_filter(self, chat_id: int, user_id: int, data: str, language: str) -> None:
        """Handle My Ads filter selection"""
        filter_type = data.split('_')[2]  # Extract filter from my_ads_all, my_ads_pending, etc.

        if filter_type == 'all':
            status_filter = None
            message_key = 'my_ads'
        elif filter_type == 'pending':
            status_filter = 'pending'
            message_key = 'my_ads'
        elif filter_type == 'approved':
            status_filter = 'approved'
            message_key = 'my_ads'
        elif filter_type == 'rejected':
            status_filter = 'rejected'
            message_key = 'my_ads'
        else:
            logger.warning(f"Unknown my_ads filter: {filter_type}")
            return

        # Get user's advertisements with status filter
        try:
            if status_filter:
                ads = await self.advertisement_service.search_user_advertisements_by_status(user_id, status_filter)
            else:
                # Get all advertisements (combine all statuses)
                pending_ads = await self.advertisement_service.search_user_advertisements_by_status(user_id, 'pending')
                approved_ads = await self.advertisement_service.search_user_advertisements_by_status(user_id, 'approved')
                rejected_ads = await self.advertisement_service.search_user_advertisements_by_status(user_id, 'rejected')
                ads = pending_ads + approved_ads + rejected_ads

            if ads:
                ads_text = f"📋 {self.localization.get_text(message_key, language)}\n\n"
                for i, ad in enumerate(ads[:10], 1):  # Show first 10 ads
                    status_emoji = "⏳" if ad['status'] == 'pending' else "✅" if ad['status'] == 'approved' else "❌"
                    ads_text += f"{i}. {status_emoji} {ad['model']} - {ad['price']:,} сум\n"

                if len(ads) > 10:
                    ads_text += f"\n... и еще {len(ads) - 10} объявлений"
            else:
                ads_text = f"📋 {self.localization.get_text('no_ads_found', language)}"

            keyboard = self.keyboards.get_back_home_keyboard(language)
            await self.telegram_service.send_message(chat_id, ads_text, keyboard)

        except Exception as e:
            logger.error(f"Error getting user advertisements: {e}")
            text = "❌ Ошибка получения объявлений / Xatolik yuz berdi"
            keyboard = self.keyboards.get_back_home_keyboard(language)
            await self.telegram_service.send_message(chat_id, text, keyboard)

    async def _handle_my_ads_pagination(self, chat_id: int, user_id: int, page: int, language: str) -> None:
        """Handle pagination for My Ads cards"""
        try:
            # Get all user advertisements
            all_ads = []

            # Get each status separately and ensure they're lists
            for status in ['pending', 'approved', 'rejected']:
                try:
                    ads = await self.user_service.get_user_advertisements(user_id, status)
                    if ads:
                        # Convert to list if it's not already
                        if not isinstance(ads, list):
                            ads = list(ads) if ads else []
                        all_ads.extend(ads)
                except Exception as e:
                    logger.error(f"Error getting {status} ads for user {user_id}: {e}")
                    continue

            if all_ads:
                # Show ads card with the requested page
                await self._show_ad_cards(chat_id, user_id, all_ads, page, language, is_my_ads=True)
            else:
                no_ads_text = self.localization.get_text('no_ads_found', language)
                keyboard = self.keyboards.get_back_home_keyboard(language)
                await self.telegram_service.send_message(chat_id, no_ads_text, keyboard)

        except Exception as e:
            logger.error(f"Error handling my ads pagination: {e}")
            text = "❌ Ошибка загрузки объявлений / Xatolik yuz berdi"
            keyboard = self.keyboards.get_back_home_keyboard(language)
            await self.telegram_service.send_message(chat_id, text, keyboard)

    async def _handle_mark_sold(self, chat_id: int, user_id: int, ad_id: int, language: str) -> None:
        """Handle marking advertisement as sold"""
        try:
            # Update advertisement status to sold
            success, message = await self.advertisement_service.mark_advertisement_sold(ad_id, user_id)

            if success:
                # Show success message
                if language == 'uz':
                    text = "✅ E'lon sotilgan deb belgilandi!"
                else:
                    text = "✅ Объявление помечено как проданное!"

                # Refresh My Ads display
                await self._show_my_advertisements(chat_id, user_id, language)
            else:
                # Show error message
                if language == 'uz':
                    text = f"❌ Xatolik: {message}"
                else:
                    text = f"❌ Ошибка: {message}"

                keyboard = self.keyboards.get_back_home_keyboard(language)
                await self.telegram_service.send_message(chat_id, text, keyboard)

        except Exception as e:
            logger.error(f"Error marking ad {ad_id} as sold: {e}")
            if language == 'uz':
                text = "❌ E'lonni sotilgan deb belgilashda xatolik yuz berdi"
            else:
                text = "❌ Ошибка при отметке объявления как проданного"

            keyboard = self.keyboards.get_back_home_keyboard(language)
            await self.telegram_service.send_message(chat_id, text, keyboard)

    async def _is_moderator(self, user_id: int) -> bool:
        """Check if user is a moderator"""
        try:
            user = await self.user_service.db.get_user(user_id)
            if user and user.get('role') == 'moderator':
                return True
            return False
        except Exception as e:
            logger.error(f"Error checking moderator status for user {user_id}: {e}")
            return False

    async def _handle_admin_command(self, chat_id: int, user_id: int, language: str) -> None:
        """Handle admin commands (/admin, /moderate)"""
        if not await self._is_moderator(user_id):
            text = "❌ Доступ запрещен / Ruxsat berilmagan" if language == 'ru' else "❌ Access denied"
            await self.telegram_service.send_message(chat_id, text)
            return

        text = "🔧 Панель модератора / Moderator paneli\n\n" \
               "Выберите действие:"
        keyboard = {
            "inline_keyboard": [
                [{"text": "📋 Объявления на модерации", "callback_data": "show_pending_ads"}],
                [{"text": "🏠 Главное меню", "callback_data": "home"}]
            ]
        }
        await self.telegram_service.send_message(chat_id, text, keyboard)

    async def _show_pending_advertisements(self, chat_id: int, user_id: int, language: str) -> None:
        """Show pending advertisements for moderation"""
        if not await self._is_moderator(user_id):
            text = "❌ Доступ запрещен / Ruxsat berilmagan"
            await self.telegram_service.send_message(chat_id, text)
            return

        try:
            pending_ads = await self.advertisement_service.get_pending_advertisements()

            if not pending_ads:
                text = "✅ Нет объявлений на модерации / Moderatsiyada e'lonlar yo'q"
                keyboard = {"inline_keyboard": [[{"text": "🏠 Главное меню", "callback_data": "home"}]]}
                await self.telegram_service.send_message(chat_id, text, keyboard)
                return

            text = f"📋 Объявления на модерации ({len(pending_ads)})\n\n"

            for ad in pending_ads[:5]:  # Show first 5 ads
                ad_text = await self.advertisement_service.format_advertisement_text(ad, language)
                keyboard = self.keyboards.get_admin_keyboard(ad['id'], language)

                photo_path = ad.get('photo_path')
                if photo_path:
                    try:
                        if photo_path.startswith('/static/'):
                            photo_url = f"https://telefonchi-backend-working.loca.lt{photo_path}"
                            await self.telegram_service.send_photo(
                                chat_id, photo_url, ad_text, keyboard
                            )
                        elif photo_path.startswith('/app/uploads/'):
                            filename = photo_path.split('/')[-1]
                            photo_url = f"https://telefonchi-backend-working.loca.lt/static/uploads/{filename}"
                            await self.telegram_service.send_photo(
                                chat_id, photo_url, ad_text, keyboard
                            )
                        else:
                            await self.telegram_service.send_message(chat_id, ad_text, keyboard)
                    except Exception as e:
                        logger.error(f"Error sending photo {photo_path}: {e}")
                        await self.telegram_service.send_message(chat_id, ad_text, keyboard)
                else:
                    await self.telegram_service.send_message(chat_id, ad_text, keyboard)

        except Exception as e:
            logger.error(f"Error showing pending advertisements: {e}")
            text = "❌ Ошибка загрузки объявлений / Xatolik yuz berdi"
            await self.telegram_service.send_message(chat_id, text)

    async def _handle_approve_advertisement(self, chat_id: int, user_id: int, data: str, language: str) -> None:
        """Handle advertisement approval"""
        if not await self._is_moderator(user_id):
            text = "❌ Доступ запрещен / Ruxsat berilmagan"
            await self.telegram_service.send_message(chat_id, text)
            return

        try:
            ad_id = int(data.split('_')[1])
            success, message = await self.advertisement_service.approve_advertisement(ad_id)

            if success:
                text = f"✅ Объявление #{ad_id} одобрено / E'lon tasdiqlandi"
            else:
                text = f"❌ Ошибка: {message}"

            await self.telegram_service.send_message(chat_id, text)

        except Exception as e:
            logger.error(f"Error approving advertisement: {e}")
            text = "❌ Ошибка одобрения объявления / Xatolik yuz berdi"
            await self.telegram_service.send_message(chat_id, text)

    async def _handle_reject_advertisement(self, chat_id: int, user_id: int, data: str, language: str) -> None:
        """Handle advertisement rejection"""
        if not await self._is_moderator(user_id):
            text = "❌ Доступ запрещен / Ruxsat berilmagan"
            await self.telegram_service.send_message(chat_id, text)
            return

        try:
            ad_id = int(data.split('_')[1])
            success, message = await self.advertisement_service.reject_advertisement(ad_id, "Отклонено модератором")

            if success:
                text = f"❌ Объявление #{ad_id} отклонено / E'lon rad etildi"
            else:
                text = f"❌ Ошибка: {message}"

            await self.telegram_service.send_message(chat_id, text)

        except Exception as e:
            logger.error(f"Error rejecting advertisement: {e}")
            text = "❌ Ошибка отклонения объявления / Xatolik yuz berdi"
            await self.telegram_service.send_message(chat_id, text)