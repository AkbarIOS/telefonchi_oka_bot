"""
Message localization system
"""

MESSAGES = {
    'ru': {
        'welcome': 'Добро пожаловать!\nВыберите язык:',
        'home_menu': '🏠 Главное меню',
        'buy': '🔎 Купить',
        'sell': '➕ Продать',
        'favorites': '⭐ Избранное',
        'my_ads': '📦 Мои объявления',
        'help': 'ℹ️ Помощь',
        'settings': '⚙️ Настройки',
        'back': '⬅️ Назад',
        'home': '🏠 Домой',
        'next': '➡️ Следующее',
        'previous': '⬅️ Предыдущее',
        'add_to_favorites': '⭐ В избранное',
        'contact': '📞 Связаться',
        'done': '✅ Готово',
        'sold': '📕 Продано',
        'delete': '🗑 Удалить',
        'what_sell': '📱 Что продаёшь?',
        'photo_required': '📷 Загрузите фото товара:',
        'choose_brand': '🏷 Выберите бренд:',
        'choose_category': '📱 Выберите категорию:',
        'enter_model': '📘 Введите модель:',
        'enter_price': '💵 Введите цену:',
        'enter_city': '🌍 Введите город:',
        'send_contact': '📱 Отправить мой номер',
        'payment_required': 'Для публикации объявления оплатите 30 000 сум.\nКарта: 0000 0000 0000 0000',
        'send_receipt': '📷 Отправить скриншот чека',
        'moderation': '⏳ Объявление отправлено на модерацию',
        'approved': '✅ Ваше объявление одобрено',
        'rejected': '❌ Ваше объявление отклонено',
        'approve': '✅ Одобрить',
        'reject': '❌ Отклонить',
        'enter_reason': 'Введите причину отклонения:',
        'no_ads': 'По этому бренду пока нет объявлений',
        'empty_favorites': 'Избранное пустое',
        'no_user_ads': 'У вас нет объявлений',
        'added_to_favorites': 'Добавлено в избранное',
        'removed_from_favorites': 'Удалено из избранного',
        'status_pending': '⏳ На модерации',
        'status_approved': '✅ Активно',
        'status_rejected': '❌ Отклонено',
        'help_text': """🔎 Чтобы купить → «Купить».
➕ Чтобы продать → «Продать».
💳 Стоимость публикации → 30 000 сум (оплата на карту).
📷 После оплаты → отправьте скриншот чека.
⭐ Чтобы сохранить товар → «Избранное».
📦 Чтобы следить за своими объявлениями → «Мои объявления».
⚙️ Чтобы сменить язык → «Настройки».""",
        'error_occurred': '❌ Произошла ошибка. Попробуйте еще раз.',
    },
    'uz': {
        'welcome': 'Xush kelibsiz!\nTilni tanlang:',
        'home_menu': '🏠 Asosiy menyu',
        'buy': '🔎 Sotib olish',
        'sell': '➕ Sotish',
        'favorites': '⭐ Sevimlilar',
        'my_ads': '📦 Mening e\'lonlarim',
        'help': 'ℹ️ Yordam',
        'settings': '⚙️ Sozlamalar',
        'back': '⬅️ Orqaga',
        'home': '🏠 Bosh sahifa',
        'next': '➡️ Keyingisi',
        'previous': '⬅️ Oldingisi',
        'add_to_favorites': '⭐ Sevimlilar',
        'contact': '📞 Bog\'lanish',
        'done': '✅ Tayyor',
        'sold': '📕 Sotilgan',
        'delete': '🗑 O\'chirish',
        'what_sell': '📱 Nima sotasiz?',
        'photo_required': '📷 Mahsulot rasmini yuklang:',
        'choose_brand': '🏷 Brendni tanlang:',
        'choose_category': '📱 Kategoriyani tanlang:',
        'enter_model': '📘 Modelni kiriting:',
        'enter_price': '💵 Narxni kiriting:',
        'enter_city': '🌍 Shaharni kiriting:',
        'send_contact': '📱 Telefon raqamni yuborish',
        'payment_required': 'E\'lon joylash uchun 30 000 so\'m to\'lang.\nKarta: 0000 0000 0000 0000',
        'send_receipt': '📷 Chek rasmini yuboring',
        'moderation': '⏳ E\'lon moderatsiyaga yuborildi',
        'approved': '✅ Sizning e\'loningiz tasdiqlandi',
        'rejected': '❌ Sizning e\'loningiz rad etildi',
        'approve': '✅ Tasdiqlash',
        'reject': '❌ Rad etish',
        'enter_reason': 'Rad etish sababini kiriting:',
        'no_ads': 'Bu brend bo\'yicha e\'lonlar yo\'q',
        'empty_favorites': 'Sevimlilar bo\'sh',
        'no_user_ads': 'Sizning e\'lonlaringiz yo\'q',
        'added_to_favorites': 'Sevimlilarga qo\'shildi',
        'removed_from_favorites': 'Sevimlilardan o\'chirildi',
        'status_pending': '⏳ Moderatsiyada',
        'status_approved': '✅ Faol',
        'status_rejected': '❌ Rad etilgan',
        'help_text': """🔎 Sotib olish uchun → «Sotib olish».
➕ Sotish uchun → «Sotish».
💳 E\'lon narxi → 30 000 so\'m (karta orqali to\'lov).
📷 To\'lovdan keyin → chek rasmini yuboring.
⭐ Mahsulotni saqlash → «Sevimlilar».
📦 O\'z e\'lonlaringizni kuzatish → «Mening e\'lonlarim».
⚙️ Tilni o\'zgartirish → «Sozlamalar».""",
        'error_occurred': '❌ Xatolik yuz berdi. Qaytadan urinib ko\'ring.',
    }
}

def get_message(key: str, lang: str = 'ru') -> str:
    """
    Get localized message by key and language

    Args:
        key: Message key
        lang: Language code ('ru' or 'uz')

    Returns:
        Localized message string
    """
    if lang not in MESSAGES:
        lang = 'ru'  # fallback to Russian

    return MESSAGES[lang].get(key, f'[{key}]')  # fallback to key in brackets