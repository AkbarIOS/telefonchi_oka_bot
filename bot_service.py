import aiohttp
import asyncio
import json
import os
import logging
from typing import Dict, List, Any, Optional
from models import TelegramUpdate, Message, CallbackQuery
from database import Database

logger = logging.getLogger(__name__)

class BotService:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.db = Database()

        # User states
        self.STATES = {
            'IDLE': 'idle',
            'WAITING_CATEGORY': 'waiting_category',
            'WAITING_BRAND': 'waiting_brand',
            'WAITING_MODEL': 'waiting_model',
            'WAITING_PRICE': 'waiting_price',
            'WAITING_CITY': 'waiting_city',
            'WAITING_PHONE': 'waiting_phone',
            'WAITING_PHOTO': 'waiting_photo',
            'WAITING_PAYMENT_RECEIPT': 'waiting_payment_receipt',
            'AD_SUBMITTED': 'ad_submitted'
        }

        # Messages in both languages
        self.messages = {
            'ru': {
                'welcome': '👋 Добро пожаловать в телефончи.UZ!\n\nВыберите действие:',
                'sell': '📱 Продать',
                'buy': '🛒 Купить',
                'my_ads': '📋 Мои объявления',
                'favorites': '❤️ Избранное',
                'language': '🌐 Язык',
                'help': '❓ Помощь',
                'home': '🏠 Главная',
                'back': '⬅️ Назад',
                'done': '✅ Готово',
                'cancel': '❌ Отмена',
                'choose_category': 'Выберите категорию:',
                'choose_brand': 'Выберите бренд:',
                'enter_model': 'Введите модель устройства:',
                'enter_price': 'Введите цену в сумах:',
                'enter_city': 'Введите город:',
                'enter_phone': 'Отправьте ваш номер телефона:',
                'share_phone': '📞 Поделиться номером',
                'send_photo': 'Отправьте фото устройства:',
                'payment_info': '💳 Оплата размещения объявления\n\nСтоимость: 30,000 сум\n\nПереведите на карту: 1234 5678 9012 3456\n\nПосле оплаты отправьте скриншот чека.',
                'send_receipt': 'Отправьте скриншот чека об оплате:',
                'ad_submitted': '✅ Ваше объявление отправлено на модерацию!\n\nВ течение 24 часов администратор проверит объявление.',
                'invalid_price': '❌ Неверная цена. Введите число.',
                'phone_received': '✅ Номер телефона получен',
                'photo_received': '✅ Фото получено',
                'receipt_received': '✅ Чек получен',
                'no_ads': 'У вас пока нет объявлений',
                'no_favorites': 'У вас пока нет избранных объявлений',
                'language_changed': '✅ Язык изменен на русский',
                'ad_approved': '✅ Ваше объявление одобрено!',
                'ad_rejected': '❌ Ваше объявление отклонено.\n\nПричина: {reason}',
                'add_to_favorites': '❤️ В избранное',
                'remove_from_favorites': '💔 Удалить из избранного',
                'added_to_favorites': '✅ Добавлено в избранное',
                'removed_from_favorites': '✅ Удалено из избранного',
                'contact_seller': '📞 Связаться с продавцом',
                'view_details': '👁️ Подробнее',
                'smartphones': '📱 Смартфоны',
                'laptops': '💻 Ноутбуки'
            },
            'uz': {
                'welcome': '👋 Telefonchi.UZ ga xush kelibsiz!\n\nAmalni tanlang:',
                'sell': '📱 Sotish',
                'buy': '🛒 Sotib olish',
                'my_ads': '📋 Mening e\'lonlarim',
                'favorites': '❤️ Sevimlilar',
                'language': '🌐 Til',
                'help': '❓ Yordam',
                'home': '🏠 Bosh sahifa',
                'back': '⬅️ Orqaga',
                'done': '✅ Tayyor',
                'cancel': '❌ Bekor qilish',
                'choose_category': 'Kategoriyani tanlang:',
                'choose_brand': 'Brendni tanlang:',
                'enter_model': 'Qurilma modelini kiriting:',
                'enter_price': 'Narxini so\'mda kiriting:',
                'enter_city': 'Shaharni kiriting:',
                'enter_phone': 'Telefon raqamingizni yuboring:',
                'share_phone': '📞 Raqamni ulashish',
                'send_photo': 'Qurilma rasmini yuboring:',
                'payment_info': '💳 E\'lon joylash to\'lovi\n\nNarxi: 30,000 so\'m\n\nKartaga o\'tkazing: 1234 5678 9012 3456\n\nTo\'lovdan keyin chek skrinishotini yuboring.',
                'send_receipt': 'To\'lov cheki skrinishotini yuboring:',
                'ad_submitted': '✅ Sizning e\'loningiz moderatsiyaga yuborildi!\n\n24 soat ichida administrator e\'lonni tekshiradi.',
                'invalid_price': '❌ Noto\'g\'ri narx. Raqam kiriting.',
                'phone_received': '✅ Telefon raqami qabul qilindi',
                'photo_received': '✅ Rasm qabul qilindi',
                'receipt_received': '✅ Chek qabul qilindi',
                'no_ads': 'Sizda hali e\'lonlar yo\'q',
                'no_favorites': 'Sizda hali sevimli e\'lonlar yo\'q',
                'language_changed': '✅ Til o\'zbekchaga o\'zgartirildi',
                'ad_approved': '✅ Sizning e\'loningiz tasdiqlandi!',
                'ad_rejected': '❌ Sizning e\'loningiz rad etildi.\n\nSabab: {reason}',
                'add_to_favorites': '❤️ Sevimlilarga',
                'remove_from_favorites': '💔 Sevimlilardan o\'chirish',
                'added_to_favorites': '✅ Sevimlilarga qo\'shildi',
                'removed_from_favorites': '✅ Sevimlilardan o\'chirildi',
                'contact_seller': '📞 Sotuvchi bilan bog\'lanish',
                'view_details': '👁️ Batafsil',
                'smartphones': '📱 Smartfonlar',
                'laptops': '💻 Noutbuklar'
            }
        }

    async def api_request(self, method: str, data: Dict = None) -> Optional[Dict]:
        """Make API request to Telegram Bot API"""
        url = f"{self.base_url}/{method}"

        async with aiohttp.ClientSession() as session:
            try:
                if data:
                    async with session.post(url, json=data) as response:
                        return await response.json()
                else:
                    async with session.get(url) as response:
                        return await response.json()
            except Exception as e:
                logger.error(f"API request error: {e}")
                return None

    async def send_message(self, chat_id: int, text: str, reply_markup: Dict = None) -> bool:
        """Send message to user"""
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML'
        }

        if reply_markup:
            data['reply_markup'] = reply_markup

        result = await self.api_request('sendMessage', data)
        return result and result.get('ok', False)

    async def edit_message(self, chat_id: int, message_id: int, text: str, reply_markup: Dict = None) -> bool:
        """Edit message"""
        data = {
            'chat_id': chat_id,
            'message_id': message_id,
            'text': text,
            'parse_mode': 'HTML'
        }

        if reply_markup:
            data['reply_markup'] = reply_markup

        result = await self.api_request('editMessageText', data)
        return result and result.get('ok', False)

    async def answer_callback_query(self, callback_query_id: str, text: str = None, show_alert: bool = False) -> bool:
        """Answer callback query"""
        data = {
            'callback_query_id': callback_query_id
        }

        if text:
            data['text'] = text
            data['show_alert'] = show_alert

        result = await self.api_request('answerCallbackQuery', data)
        return result and result.get('ok', False)

    async def get_me(self) -> Optional[Dict]:
        """Get bot information"""
        return await self.api_request('getMe')

    async def set_webhook(self, url: str) -> bool:
        """Set webhook URL"""
        data = {'url': url}
        result = await self.api_request('setWebhook', data)
        return result and result.get('ok', False)

    async def delete_webhook(self) -> bool:
        """Delete webhook"""
        result = await self.api_request('deleteWebhook')
        return result and result.get('ok', False)

    def get_message(self, key: str, lang: str = 'ru', **kwargs) -> str:
        """Get localized message"""
        message = self.messages.get(lang, self.messages['ru']).get(key, key)
        if kwargs:
            return message.format(**kwargs)
        return message

    def get_main_keyboard(self, lang: str = 'ru') -> Dict:
        """Get main menu keyboard"""
        return {
            'inline_keyboard': [
                [
                    {'text': self.get_message('sell', lang), 'callback_data': 'sell'},
                    {'text': self.get_message('buy', lang), 'callback_data': 'buy'}
                ],
                [
                    {'text': self.get_message('my_ads', lang), 'callback_data': 'my_ads'},
                    {'text': self.get_message('favorites', lang), 'callback_data': 'favorites'}
                ],
                [
                    {'text': self.get_message('language', lang), 'callback_data': 'language'},
                    {'text': self.get_message('help', lang), 'callback_data': 'help'}
                ]
            ]
        }

    def get_language_keyboard(self) -> Dict:
        """Get language selection keyboard"""
        return {
            'inline_keyboard': [
                [
                    {'text': '🇷🇺 Русский', 'callback_data': 'lang_ru'},
                    {'text': '🇺🇿 O\'zbekcha', 'callback_data': 'lang_uz'}
                ],
                [
                    {'text': self.get_message('back', 'ru') + ' / ' + self.get_message('back', 'uz'), 'callback_data': 'home'}
                ]
            ]
        }

    def get_categories_keyboard(self, lang: str = 'ru') -> Dict:
        """Get categories keyboard"""
        return {
            'inline_keyboard': [
                [
                    {'text': self.get_message('smartphones', lang), 'callback_data': 'category_1'}
                ],
                [
                    {'text': self.get_message('laptops', lang), 'callback_data': 'category_2'}
                ],
                [
                    {'text': self.get_message('back', lang), 'callback_data': 'home'}
                ]
            ]
        }

    def get_phone_keyboard(self, lang: str = 'ru') -> Dict:
        """Get phone sharing keyboard"""
        return {
            'keyboard': [
                [
                    {'text': self.get_message('share_phone', lang), 'request_contact': True}
                ]
            ],
            'one_time_keyboard': True,
            'resize_keyboard': True
        }

    def get_navigation_keyboard(self, lang: str = 'ru') -> Dict:
        """Get navigation keyboard"""
        return {
            'inline_keyboard': [
                [
                    {'text': self.get_message('back', lang), 'callback_data': 'back'},
                    {'text': self.get_message('home', lang), 'callback_data': 'home'}
                ]
            ]
        }

    async def get_user_language(self, telegram_id: int) -> str:
        """Get user's language preference"""
        user = await self.db.get_user(telegram_id)
        return user.get('language_code', 'ru') if user else 'ru'

    async def get_user_state(self, telegram_id: int) -> str:
        """Get user's current state"""
        user = await self.db.get_user(telegram_id)
        return user.get('state', self.STATES['IDLE']) if user else self.STATES['IDLE']

    async def set_user_state(self, telegram_id: int, state: str) -> bool:
        """Set user's state"""
        return await self.db.update_user(telegram_id, {'state': state})

    async def process_update(self, update: TelegramUpdate):
        """Process incoming update"""
        try:
            if update.message:
                await self.handle_message(update.message)
            elif update.callback_query:
                await self.handle_callback_query(update.callback_query)
        except Exception as e:
            logger.error(f"Error processing update: {e}")

    async def handle_message(self, message: Message):
        """Handle incoming message"""
        try:
            telegram_id = message.from_.id
            chat_id = message.chat.id

            # Register user if not exists
            user = await self.db.get_user(telegram_id)
            if not user:
                user_data = {
                    'telegram_id': telegram_id,
                    'first_name': message.from_.first_name,
                    'username': message.from_.username,
                    'language_code': message.from_.language_code or 'ru'
                }
                await self.db.create_user(user_data)
                user = await self.db.get_user(telegram_id)

            lang = user.get('language_code', 'ru')
            state = user.get('state', self.STATES['IDLE'])

            # Handle /start command
            if message.text and message.text.startswith('/start'):
                await self.send_welcome(chat_id, lang)
                return

            # Handle contact sharing
            if message.contact:
                await self.handle_contact(message, user)
                return

            # Handle photo upload
            if message.photo:
                await self.handle_photo(message, user)
                return

            # Handle text messages based on state
            if message.text:
                await self.handle_text_message(message, user)

        except Exception as e:
            logger.error(f"Error handling message: {e}")

    async def handle_callback_query(self, callback_query: CallbackQuery):
        """Handle callback query"""
        try:
            telegram_id = callback_query.from_.id
            chat_id = callback_query.message.chat.id
            message_id = callback_query.message.message_id
            data = callback_query.data

            await self.answer_callback_query(callback_query.id)

            user = await self.db.get_user(telegram_id)
            if not user:
                return

            lang = user.get('language_code', 'ru')

            if data == 'home':
                await self.send_welcome(chat_id, lang, message_id)
            elif data == 'sell':
                await self.start_selling_process(chat_id, lang, message_id)
            elif data == 'buy':
                await self.show_categories_for_buying(chat_id, lang, message_id)
            elif data == 'my_ads':
                await self.show_user_ads(chat_id, telegram_id, lang, message_id)
            elif data == 'favorites':
                await self.show_user_favorites(chat_id, telegram_id, lang, message_id)
            elif data == 'language':
                await self.show_language_menu(chat_id, message_id)
            elif data.startswith('lang_'):
                new_lang = data.split('_')[1]
                await self.change_language(chat_id, telegram_id, new_lang, message_id)
            elif data.startswith('category_'):
                await self.handle_category_selection(callback_query, user)
            elif data.startswith('brand_'):
                await self.handle_brand_selection(callback_query, user)

        except Exception as e:
            logger.error(f"Error handling callback query: {e}")

    async def send_welcome(self, chat_id: int, lang: str = 'ru', message_id: int = None):
        """Send welcome message"""
        text = self.get_message('welcome', lang)
        keyboard = self.get_main_keyboard(lang)

        if message_id:
            await self.edit_message(chat_id, message_id, text, keyboard)
        else:
            await self.send_message(chat_id, text, keyboard)

    async def start_selling_process(self, chat_id: int, lang: str, message_id: int = None):
        """Start the selling process"""
        text = self.get_message('choose_category', lang)
        keyboard = self.get_categories_keyboard(lang)

        if message_id:
            await self.edit_message(chat_id, message_id, text, keyboard)
        else:
            await self.send_message(chat_id, text, keyboard)

    async def show_categories_for_buying(self, chat_id: int, lang: str, message_id: int = None):
        """Show categories for buying"""
        text = self.get_message('choose_category', lang)
        keyboard = self.get_categories_keyboard(lang)

        if message_id:
            await self.edit_message(chat_id, message_id, text, keyboard)
        else:
            await self.send_message(chat_id, text, keyboard)

    async def show_language_menu(self, chat_id: int, message_id: int = None):
        """Show language selection menu"""
        text = "🌐 Language / Til:"
        keyboard = self.get_language_keyboard()

        if message_id:
            await self.edit_message(chat_id, message_id, text, keyboard)
        else:
            await self.send_message(chat_id, text, keyboard)

    async def change_language(self, chat_id: int, telegram_id: int, new_lang: str, message_id: int = None):
        """Change user language"""
        await self.db.update_user(telegram_id, {'language_code': new_lang})
        text = self.get_message('language_changed', new_lang)
        keyboard = self.get_main_keyboard(new_lang)

        if message_id:
            await self.edit_message(chat_id, message_id, text, keyboard)
        else:
            await self.send_message(chat_id, text, keyboard)

    async def handle_category_selection(self, callback_query: CallbackQuery, user: Dict):
        """Handle category selection"""
        category_id = int(callback_query.data.split('_')[1])
        telegram_id = user['telegram_id']
        chat_id = callback_query.message.chat.id
        message_id = callback_query.message.message_id
        lang = user.get('language_code', 'ru')

        # Store selected category in temp data
        temp_data = await self.db.get_temp_data(user['id'])
        temp_data['category_id'] = category_id
        await self.db.set_temp_data(user['id'], temp_data)

        # Get brands for this category
        brands = await self.db.get_brands(category_id)

        if not brands:
            await self.send_message(chat_id, "No brands available for this category")
            return

        # Create brands keyboard
        keyboard_rows = []
        for brand in brands:
            keyboard_rows.append([{'text': brand['name'], 'callback_data': f'brand_{brand["id"]}'}])

        keyboard_rows.append([{'text': self.get_message('back', lang), 'callback_data': 'sell'}])

        keyboard = {'inline_keyboard': keyboard_rows}
        text = self.get_message('choose_brand', lang)

        await self.edit_message(chat_id, message_id, text, keyboard)

    async def handle_brand_selection(self, callback_query: CallbackQuery, user: Dict):
        """Handle brand selection"""
        brand_id = int(callback_query.data.split('_')[1])
        telegram_id = user['telegram_id']
        chat_id = callback_query.message.chat.id
        message_id = callback_query.message.message_id
        lang = user.get('language_code', 'ru')

        # Store selected brand in temp data
        temp_data = await self.db.get_temp_data(user['id'])
        temp_data['brand_id'] = brand_id
        await self.db.set_temp_data(user['id'], temp_data)

        # Set state to waiting for model
        await self.set_user_state(telegram_id, self.STATES['WAITING_MODEL'])

        # Ask for model
        text = self.get_message('enter_model', lang)
        keyboard = self.get_navigation_keyboard(lang)

        await self.edit_message(chat_id, message_id, text, keyboard)

    async def handle_text_message(self, message: Message, user: Dict):
        """Handle text message based on user state"""
        telegram_id = user['telegram_id']
        chat_id = message.chat.id
        text = message.text
        lang = user.get('language_code', 'ru')
        state = user.get('state', self.STATES['IDLE'])

        if state == self.STATES['WAITING_MODEL']:
            await self.handle_model_input(chat_id, telegram_id, text, lang)
        elif state == self.STATES['WAITING_PRICE']:
            await self.handle_price_input(chat_id, telegram_id, text, lang)
        elif state == self.STATES['WAITING_CITY']:
            await self.handle_city_input(chat_id, telegram_id, text, lang)

    async def handle_model_input(self, chat_id: int, telegram_id: int, model: str, lang: str):
        """Handle model input"""
        user = await self.db.get_user(telegram_id)
        temp_data = await self.db.get_temp_data(user['id'])
        temp_data['model'] = model
        await self.db.set_temp_data(user['id'], temp_data)

        # Set state to waiting for price
        await self.set_user_state(telegram_id, self.STATES['WAITING_PRICE'])

        # Ask for price
        text = self.get_message('enter_price', lang)
        keyboard = self.get_navigation_keyboard(lang)

        await self.send_message(chat_id, text, keyboard)

    async def handle_price_input(self, chat_id: int, telegram_id: int, price: str, lang: str):
        """Handle price input"""
        try:
            # Validate price is numeric
            int(price.replace(' ', ''))

            user = await self.db.get_user(telegram_id)
            temp_data = await self.db.get_temp_data(user['id'])
            temp_data['price'] = price
            await self.db.set_temp_data(user['id'], temp_data)

            # Set state to waiting for city
            await self.set_user_state(telegram_id, self.STATES['WAITING_CITY'])

            # Ask for city
            text = self.get_message('enter_city', lang)
            keyboard = self.get_navigation_keyboard(lang)

            await self.send_message(chat_id, text, keyboard)

        except ValueError:
            text = self.get_message('invalid_price', lang)
            await self.send_message(chat_id, text)

    async def handle_city_input(self, chat_id: int, telegram_id: int, city: str, lang: str):
        """Handle city input"""
        user = await self.db.get_user(telegram_id)
        temp_data = await self.db.get_temp_data(user['id'])
        temp_data['city'] = city
        await self.db.set_temp_data(user['id'], temp_data)

        # Set state to waiting for phone
        await self.set_user_state(telegram_id, self.STATES['WAITING_PHONE'])

        # Ask for phone
        text = self.get_message('enter_phone', lang)
        keyboard = self.get_phone_keyboard(lang)

        await self.send_message(chat_id, text, keyboard)

    async def handle_contact(self, message: Message, user: Dict):
        """Handle contact sharing"""
        telegram_id = user['telegram_id']
        chat_id = message.chat.id
        lang = user.get('language_code', 'ru')
        state = user.get('state', self.STATES['IDLE'])

        if state == self.STATES['WAITING_PHONE']:
            phone = message.contact.phone_number
            temp_data = await self.db.get_temp_data(user['id'])
            temp_data['contact_phone'] = phone
            await self.db.set_temp_data(user['id'], temp_data)

            # Set state to waiting for photo
            await self.set_user_state(telegram_id, self.STATES['WAITING_PHOTO'])

            # Ask for photo
            text = self.get_message('send_photo', lang)
            await self.send_message(chat_id, text)

    async def handle_photo(self, message: Message, user: Dict):
        """Handle photo upload"""
        telegram_id = user['telegram_id']
        chat_id = message.chat.id
        lang = user.get('language_code', 'ru')
        state = user.get('state', self.STATES['IDLE'])

        if state == self.STATES['WAITING_PHOTO']:
            # Get largest photo
            photo = max(message.photo, key=lambda x: x.file_size or 0)
            temp_data = await self.db.get_temp_data(user['id'])
            temp_data['photo_path'] = photo.file_id
            await self.db.set_temp_data(user['id'], temp_data)

            # Set state to waiting for payment receipt
            await self.set_user_state(telegram_id, self.STATES['WAITING_PAYMENT_RECEIPT'])

            # Show payment info
            text = self.get_message('payment_info', lang)
            await self.send_message(chat_id, text)

        elif state == self.STATES['WAITING_PAYMENT_RECEIPT']:
            # Handle payment receipt
            await self.handle_payment_receipt(message, user)

    async def handle_payment_receipt(self, message: Message, user: Dict):
        """Handle payment receipt"""
        telegram_id = user['telegram_id']
        chat_id = message.chat.id
        lang = user.get('language_code', 'ru')

        # Create advertisement
        temp_data = await self.db.get_temp_data(user['id'])

        ad_data = {
            'user_id': user['id'],
            'category_id': temp_data['category_id'],
            'brand_id': temp_data['brand_id'],
            'model': temp_data['model'],
            'price': temp_data['price'],
            'city': temp_data['city'],
            'contact_phone': temp_data['contact_phone'],
            'photo_path': temp_data['photo_path'],
            'status': 'pending'
        }

        ad_id = await self.db.create_advertisement(ad_data)

        if ad_id:
            # Clear temp data
            await self.db.clear_temp_data(user['id'])

            # Set state to idle
            await self.set_user_state(telegram_id, self.STATES['IDLE'])

            # Send confirmation
            text = self.get_message('ad_submitted', lang)
            keyboard = self.get_main_keyboard(lang)

            await self.send_message(chat_id, text, keyboard)

    async def show_user_ads(self, chat_id: int, telegram_id: int, lang: str, message_id: int = None):
        """Show user's advertisements"""
        user = await self.db.get_user(telegram_id)
        ads = await self.db.get_user_advertisements(user['id'])

        if not ads:
            text = self.get_message('no_ads', lang)
            keyboard = self.get_main_keyboard(lang)
        else:
            text = "📋 Ваши объявления:\n\n" if lang == 'ru' else "📋 Sizning e'lonlaringiz:\n\n"
            for ad in ads[:5]:  # Show first 5 ads
                status_emoji = "⏳" if ad['status'] == 'pending' else "✅" if ad['status'] == 'approved' else "❌"
                text += f"{status_emoji} {ad['brand_name']} {ad['model']} - {ad['price']} сум\n"
            keyboard = self.get_main_keyboard(lang)

        if message_id:
            await self.edit_message(chat_id, message_id, text, keyboard)
        else:
            await self.send_message(chat_id, text, keyboard)

    async def show_user_favorites(self, chat_id: int, telegram_id: int, lang: str, message_id: int = None):
        """Show user's favorites"""
        user = await self.db.get_user(telegram_id)
        favorites = await self.db.get_user_favorites(user['id'])

        if not favorites:
            text = self.get_message('no_favorites', lang)
            keyboard = self.get_main_keyboard(lang)
        else:
            text = "❤️ Избранные объявления:\n\n" if lang == 'ru' else "❤️ Sevimli e'lonlar:\n\n"
            for fav in favorites[:5]:  # Show first 5 favorites
                text += f"📱 {fav['brand_name']} {fav['model']} - {fav['price']} сум\n"
            keyboard = self.get_main_keyboard(lang)

        if message_id:
            await self.edit_message(chat_id, message_id, text, keyboard)
        else:
            await self.send_message(chat_id, text, keyboard)