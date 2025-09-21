from typing import Dict

class LocalizationManager:
    """Manages localization for multiple languages"""

    def __init__(self):
        self.translations = {
            'ru': {
                # Main menu
                'main_menu': '🏠 Главное меню\n\nВыберите действие:',
                'sell_button': '💰 Продать',
                'buy_button': '🛒 Купить',
                'my_ads': '📋 Мои объявления',
                'my_favorites': '❤️ Избранное',
                'language_button': '🌐 Язык',
                'help_button': '❓ Помощь',

                # Categories and selection
                'select_category_sell': '📂 Выберите категорию для продажи:',
                'select_category_buy': '🔍 Выберите категорию для поиска:',
                'select_brand': '🏷️ Выберите бренд:',
                'select_language': '🌐 Выберите язык:',

                # Input prompts
                'enter_model': '📱 Введите модель устройства:',
                'enter_price': '💰 Введите цену (в сумах):',
                'enter_description': '📝 Введите описание (минимум 10 символов):',
                'enter_city': '🏙️ Введите город:',
                'send_photo': '📸 Отправьте фото товара:',
                'send_phone': '📞 Поделитесь контактом или введите номер телефона:',
                'send_receipt': '📷 Отправьте скриншот чека об оплате:',

                # Buttons
                'back_button': '⬅️ Назад',
                'home_button': '🏠 Главная',
                'skip_button': '⏭️ Пропустить',
                'share_contact': '📞 Поделиться контактом',
                'done_button': '✅ Готово',

                # Messages
                'ad_created_payment': '✅ Объявление создано!\n\n💳 Для публикации необходимо оплатить {price} сум.\nОтправьте чек об оплате.',
                'ad_created_success': '✅ Объявление успешно создано и отправлено на модерацию!',
                'payment_instructions': '💳 Переведите {price} сум на карту:\n\n{card_number}\n\nПосле оплаты отправьте чек.',
                'language_changed': '✅ Язык изменен!',
                'found_ads': '📋 Найдено объявлений: {count}',
                'no_ads_found': '😔 Объявления не найдены',
                'no_categories': '❌ Категории не найдены',
                'no_brands': '❌ Бренды не найдены',

                # Validation messages
                'invalid_price': '❌ Неверная цена. Введите число больше 0.',
                'description_too_short': '❌ Описание слишком короткое. Минимум 10 символов.',
                'city_too_short': '❌ Название города слишком короткое. Минимум 2 символа.',
                'photo_upload_error': '❌ Ошибка загрузки фото. Попробуйте еще раз.',
                'photo_upload_timeout': '⏰ Загрузка фото заняла слишком много времени. Попробуйте загрузить фото снова.',
                'ad_creation_error': '❌ Ошибка создания объявления. Попробуйте еще раз.',
                'language_change_error': '❌ Ошибка изменения языка.',

                # States
                'waiting_for_photo': '📸 Ожидаю фото товара...',
                'waiting_for_contact': '📞 Ожидаю контакт или номер телефона...',
                'phone_received': '✅ Телефон получен!',

                # Help and other
                'help_message': '❓ Помощь\n\n🤖 Я бот для продажи и покупки техники.\n\n💰 Продажа:\n- Выберите категорию и бренд\n- Введите модель, цену и описание\n- Добавьте фото\n- Поделитесь контактом\n- Оплатите публикацию\n\n🛒 Покупка:\n- Выберите категорию\n- Просматривайте объявления\n- Добавляйте в избранное\n- Связывайтесь с продавцами',
                'unknown_command': '❌ Неизвестная команда',

                # Advertisement actions
                'view_details': '👀 Подробнее',
                'add_favorite': '❤️ В избранное',
                'remove_favorite': '💔 Убрать из избранного',
                'contact_seller': '📞 Связаться',
            },
            'uz': {
                # Main menu
                'main_menu': '🏠 Asosiy menyu\n\nAmalni tanlang:',
                'sell_button': '💰 Sotish',
                'buy_button': '🛒 Sotib olish',
                'my_ads': '📋 Mening e\'lonlarim',
                'my_favorites': '❤️ Sevimlilar',
                'language_button': '🌐 Til',
                'help_button': '❓ Yordam',

                # Categories and selection
                'select_category_sell': '📂 Sotish uchun kategoriyani tanlang:',
                'select_category_buy': '🔍 Qidirish uchun kategoriyani tanlang:',
                'select_brand': '🏷️ Brendni tanlang:',
                'select_language': '🌐 Tilni tanlang:',

                # Input prompts
                'enter_model': '📱 Qurilma modelini kiriting:',
                'enter_price': '💰 Narxni kiriting (so\'mda):',
                'enter_description': '📝 Tavsifni kiriting (kamida 10 belgi):',
                'enter_city': '🏙️ Shaharni kiriting:',
                'send_photo': '📸 Mahsulot rasmini yuboring:',
                'send_phone': '📞 Kontakt bilan bo\'lishing yoki telefon raqamini kiriting:',
                'send_receipt': '📷 To\'lov kvitansiyasining skrinshotini yuboring:',

                # Buttons
                'back_button': '⬅️ Orqaga',
                'home_button': '🏠 Bosh sahifa',
                'skip_button': '⏭️ O\'tkazib yuborish',
                'share_contact': '📞 Kontakt ulashish',
                'done_button': '✅ Tayyor',

                # Messages
                'ad_created_payment': '✅ E\'lon yaratildi!\n\n💳 Nashr qilish uchun {price} so\'m to\'lash kerak.\nTo\'lov chekini yuboring.',
                'ad_created_success': '✅ E\'lon muvaffaqiyatli yaratildi va moderatsiyaga yuborildi!',
                'payment_instructions': '💳 {price} so\'mni karta raqamiga o\'tkazing:\n\n{card_number}\n\nTo\'lovdan keyin chekni yuboring.',
                'language_changed': '✅ Til o\'zgartirildi!',
                'found_ads': '📋 Topilgan e\'lonlar: {count}',
                'no_ads_found': '😔 E\'lonlar topilmadi',
                'no_categories': '❌ Kategoriyalar topilmadi',
                'no_brands': '❌ Brendlar topilmadi',

                # Validation messages
                'invalid_price': '❌ Noto\'g\'ri narx. 0dan katta raqam kiriting.',
                'description_too_short': '❌ Tavsif juda qisqa. Kamida 10 belgi.',
                'city_too_short': '❌ Shahar nomi juda qisqa. Kamida 2 belgi.',
                'photo_upload_error': '❌ Rasm yuklashda xatolik. Qaytadan urinib ko\'ring.',
                'photo_upload_timeout': '⏰ Rasm yuklash juda uzoq vaqt oldi. Rasmni qaytadan yuklashga harakat qiling.',
                'ad_creation_error': '❌ E\'lon yaratishda xatolik. Qaytadan urinib ko\'ring.',
                'language_change_error': '❌ Tilni o\'zgartirishda xatolik.',

                # States
                'waiting_for_photo': '📸 Mahsulot rasmini kutmoqda...',
                'waiting_for_contact': '📞 Kontakt yoki telefon raqamini kutmoqda...',
                'phone_received': '✅ Telefon qabul qilindi!',

                # Help and other
                'help_message': '❓ Yordam\n\n🤖 Men texnika sotish va sotib olish boti.\n\n💰 Sotish:\n- Kategoriya va brendni tanlang\n- Model, narx va tavsifni kiriting\n- Rasm qo\'shing\n- Kontakt ulashing\n- Nashrni to\'lang\n\n🛒 Sotib olish:\n- Kategoriyani tanlang\n- E\'lonlarni ko\'ring\n- Sevimlilar ro\'yxatiga qo\'shing\n- Sotuvchilar bilan bog\'laning',
                'unknown_command': '❌ Noma\'lum buyruq',

                # Advertisement actions
                'view_details': '👀 Batafsil',
                'add_favorite': '❤️ Sevimlilar ro\'yxatiga',
                'remove_favorite': '💔 Sevimlilardan olib tashlash',
                'contact_seller': '📞 Bog\'lanish',
            }
        }

    def get_text(self, key: str, language: str = 'ru') -> str:
        """Get localized text"""
        if language not in self.translations:
            language = 'ru'

        return self.translations[language].get(key, key)

    def get_available_languages(self) -> Dict[str, str]:
        """Get available languages"""
        return {
            'ru': '🇷🇺 Русский',
            'uz': '🇺🇿 O\'zbekcha'
        }