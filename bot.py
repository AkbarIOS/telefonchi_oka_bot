#!/usr/bin/env python3

import os
import logging
import json
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.constants import ParseMode
from database import Database
from messages import get_message

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.db = Database()

    def get_language_keyboard(self):
        keyboard = [
            [
                InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
                InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    def get_main_menu_keyboard(self, lang='ru'):
        keyboard = [
            [get_message('buy', lang), get_message('sell', lang)],
            [get_message('favorites', lang), get_message('my_ads', lang)],
            [get_message('help', lang), get_message('settings', lang)]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

    def get_category_keyboard(self, lang='ru'):
        categories = self.db.get_categories()
        keyboard = []

        row = []
        for category in categories:
            name = category['name_ru'] if lang == 'ru' else category['name_uz']
            row.append(InlineKeyboardButton(f"{category['icon']} {name}", callback_data=f"category_{category['id']}"))
        keyboard.append(row)

        keyboard.append([
            InlineKeyboardButton(get_message('back', lang), callback_data="back"),
            InlineKeyboardButton(get_message('home', lang), callback_data="home")
        ])

        return InlineKeyboardMarkup(keyboard)

    def get_brand_keyboard(self, category_id, lang='ru'):
        brands = self.db.get_brands(category_id)
        keyboard = []

        # Create rows of 2 brands each
        for i in range(0, len(brands), 2):
            row = []
            row.append(InlineKeyboardButton(brands[i]['name'], callback_data=f"brand_{brands[i]['id']}"))
            if i + 1 < len(brands):
                row.append(InlineKeyboardButton(brands[i + 1]['name'], callback_data=f"brand_{brands[i + 1]['id']}"))
            keyboard.append(row)

        keyboard.append([
            InlineKeyboardButton(get_message('back', lang), callback_data="back"),
            InlineKeyboardButton(get_message('home', lang), callback_data="home")
        ])

        return InlineKeyboardMarkup(keyboard)

    def get_contact_keyboard(self, lang='ru'):
        keyboard = [[KeyboardButton(get_message('send_contact', lang), request_contact=True)]]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    def get_done_keyboard(self, lang='ru'):
        keyboard = [
            [InlineKeyboardButton(get_message('done', lang), callback_data="done")],
            [
                InlineKeyboardButton(get_message('back', lang), callback_data="back"),
                InlineKeyboardButton(get_message('home', lang), callback_data="home")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        chat_id = update.effective_chat.id

        logger.info(f"Start command from user {user.id}")

        # Check if user exists
        db_user = self.db.get_user(user.id)

        if not db_user:
            # New user - create and show language selection
            self.db.create_user({
                'telegram_id': user.id,
                'first_name': user.first_name,
                'username': user.username,
                'language_code': user.language_code or 'ru'
            })

            await update.message.reply_text(
                get_message('welcome', 'ru'),
                reply_markup=self.get_language_keyboard(),
                parse_mode=ParseMode.HTML
            )
        else:
            # Existing user - show main menu
            lang = db_user.get('language_code', 'ru')
            await update.message.reply_text(
                get_message('home_menu', lang),
                reply_markup=self.get_main_menu_keyboard(lang),
                parse_mode=ParseMode.HTML
            )

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = query.from_user.id
        data = query.data

        logger.info(f"Button callback from user {user_id}: {data}")

        await query.answer()

        user = self.db.get_user(user_id)
        lang = user.get('language_code', 'ru')

        if data.startswith('lang_'):
            # Language selection
            new_lang = data.split('_')[1]
            self.db.update_user(user_id, {'language_code': new_lang})

            await query.edit_message_text(
                get_message('home_menu', new_lang),
                reply_markup=self.get_main_menu_keyboard(new_lang),
                parse_mode=ParseMode.HTML
            )

        elif data.startswith('category_'):
            # Category selection for selling
            category_id = int(data.split('_')[1])

            # Store category in temp data
            temp_data = self.db.get_temp_data(user['id']) or {}
            temp_data['category_id'] = category_id
            self.db.set_temp_data(user['id'], temp_data)

            await query.edit_message_text(
                get_message('choose_brand', lang),
                reply_markup=self.get_brand_keyboard(category_id, lang),
                parse_mode=ParseMode.HTML
            )

        elif data.startswith('brand_'):
            # Brand selection
            brand_id = int(data.split('_')[1])

            # Store brand in temp data
            temp_data = self.db.get_temp_data(user['id']) or {}
            temp_data['brand_id'] = brand_id
            self.db.set_temp_data(user['id'], temp_data)
            self.db.update_user(user_id, {'state': 'awaiting_photo'})

            await query.edit_message_text(
                get_message('photo_required', lang),
                parse_mode=ParseMode.HTML
            )

        elif data == 'done':
            # Complete the advertisement
            await self.complete_advertisement(query, context, user, lang)

        elif data == 'home':
            await query.edit_message_text(
                get_message('home_menu', lang),
                reply_markup=self.get_main_menu_keyboard(lang),
                parse_mode=ParseMode.HTML
            )

        elif data == 'back':
            # Handle back button based on current state
            state = user.get('state', 'idle')
            temp_data = self.db.get_temp_data(user['id']) or {}

            if 'brand_id' in temp_data:
                # Go back to category selection
                del temp_data['brand_id']
                self.db.set_temp_data(user['id'], temp_data)

                await query.edit_message_text(
                    get_message('what_sell', lang),
                    reply_markup=self.get_category_keyboard(lang),
                    parse_mode=ParseMode.HTML
                )
            else:
                await query.edit_message_text(
                    get_message('home_menu', lang),
                    reply_markup=self.get_main_menu_keyboard(lang),
                    parse_mode=ParseMode.HTML
                )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        message = update.message
        text = message.text

        logger.info(f"Message from user {user.id}: {text}")

        db_user = self.db.get_user(user.id)
        if not db_user:
            return

        lang = db_user.get('language_code', 'ru')
        state = db_user.get('state', 'idle')

        # Handle menu buttons
        if text == get_message('sell', lang):
            await message.reply_text(
                get_message('what_sell', lang),
                reply_markup=self.get_category_keyboard(lang),
                parse_mode=ParseMode.HTML
            )

        elif text == get_message('buy', lang):
            await message.reply_text(
                get_message('choose_category', lang),
                reply_markup=self.get_category_keyboard(lang),
                parse_mode=ParseMode.HTML
            )

        elif text == get_message('help', lang):
            await message.reply_text(
                get_message('help_text', lang),
                parse_mode=ParseMode.HTML
            )

        elif text == get_message('settings', lang):
            await message.reply_text(
                get_message('welcome', lang),
                reply_markup=self.get_language_keyboard(),
                parse_mode=ParseMode.HTML
            )

        # Handle state-based input
        elif state == 'awaiting_model':
            temp_data = self.db.get_temp_data(db_user['id']) or {}
            temp_data['model'] = text
            self.db.set_temp_data(db_user['id'], temp_data)
            self.db.update_user(user.id, {'state': 'awaiting_price'})

            await message.reply_text(
                get_message('enter_price', lang),
                parse_mode=ParseMode.HTML
            )

        elif state == 'awaiting_price':
            temp_data = self.db.get_temp_data(db_user['id']) or {}
            temp_data['price'] = text
            self.db.set_temp_data(db_user['id'], temp_data)
            self.db.update_user(user.id, {'state': 'awaiting_city'})

            await message.reply_text(
                get_message('enter_city', lang),
                parse_mode=ParseMode.HTML
            )

        elif state == 'awaiting_city':
            temp_data = self.db.get_temp_data(db_user['id']) or {}
            temp_data['city'] = text
            self.db.set_temp_data(db_user['id'], temp_data)
            self.db.update_user(user.id, {'state': 'awaiting_contact'})

            await message.reply_text(
                get_message('send_contact', lang),
                reply_markup=self.get_contact_keyboard(lang),
                parse_mode=ParseMode.HTML
            )

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        photo = update.message.photo[-1]  # Get the highest resolution photo

        db_user = self.db.get_user(user.id)
        if not db_user or db_user.get('state') != 'awaiting_photo':
            return

        lang = db_user.get('language_code', 'ru')

        try:
            # Download photo
            file = await context.bot.get_file(photo.file_id)
            file_path = f"uploads/{user.id}_{photo.file_id}.jpg"
            await file.download_to_drive(file_path)

            # Store photo path in temp data
            temp_data = self.db.get_temp_data(db_user['id']) or {}
            temp_data['photo_path'] = file_path
            self.db.set_temp_data(db_user['id'], temp_data)
            self.db.update_user(user.id, {'state': 'awaiting_model'})

            await update.message.reply_text(
                get_message('enter_model', lang),
                parse_mode=ParseMode.HTML
            )

        except Exception as e:
            logger.error(f"Error handling photo: {e}")
            await update.message.reply_text(
                get_message('error_occurred', lang),
                parse_mode=ParseMode.HTML
            )

    async def handle_contact(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        contact = update.message.contact

        db_user = self.db.get_user(user.id)
        if not db_user or db_user.get('state') != 'awaiting_contact':
            return

        lang = db_user.get('language_code', 'ru')

        # Store contact in temp data
        temp_data = self.db.get_temp_data(db_user['id']) or {}
        temp_data['contact_phone'] = contact.phone_number
        self.db.set_temp_data(db_user['id'], temp_data)

        # Show preview
        await self.show_advertisement_preview(update, context, db_user, temp_data, lang)

    async def show_advertisement_preview(self, update, context, user, temp_data, lang):
        category = self.db.get_category(temp_data['category_id'])
        brand = self.db.get_brand(temp_data['brand_id'])

        category_name = category['name_ru'] if lang == 'ru' else category['name_uz']

        preview_text = f"""
{category['icon']} {category_name}
🏷 Бренд: {brand['name']}
📘 Модель: {temp_data['model']}
💵 Цена: {temp_data['price']}
🌍 Город: {temp_data['city']}
📞 {temp_data['contact_phone']}
        """.strip()

        self.db.update_user(user['telegram_id'], {'state': 'confirming_ad'})

        try:
            # Send photo with caption
            with open(temp_data['photo_path'], 'rb') as photo_file:
                await update.message.reply_photo(
                    photo=photo_file,
                    caption=preview_text,
                    reply_markup=self.get_done_keyboard(lang),
                    parse_mode=ParseMode.HTML
                )
        except Exception as e:
            logger.error(f"Error sending photo: {e}")
            await update.message.reply_text(
                preview_text,
                reply_markup=self.get_done_keyboard(lang),
                parse_mode=ParseMode.HTML
            )

    async def complete_advertisement(self, query, context, user, lang):
        temp_data = self.db.get_temp_data(user['id'])

        if not temp_data:
            await query.edit_message_text(
                get_message('error_occurred', lang),
                parse_mode=ParseMode.HTML
            )
            return

        try:
            # Create advertisement
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

            self.db.create_advertisement(ad_data)

            # Clear temp data and reset state
            self.db.clear_temp_data(user['id'])
            self.db.update_user(user['telegram_id'], {'state': 'idle'})

            await query.edit_message_text(
                get_message('moderation', lang),
                parse_mode=ParseMode.HTML
            )

        except Exception as e:
            logger.error(f"Error creating advertisement: {e}")
            await query.edit_message_text(
                get_message('error_occurred', lang),
                parse_mode=ParseMode.HTML
            )

def main():
    bot = TelegramBot()

    # Create application
    application = Application.builder().token(bot.token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CallbackQueryHandler(bot.button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, bot.handle_photo))
    application.add_handler(MessageHandler(filters.CONTACT, bot.handle_contact))

    # Run the bot
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()