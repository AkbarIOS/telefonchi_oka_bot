from typing import Dict, List
from app.utils.localization import LocalizationManager


class KeyboardBuilder:
    """Builder for Telegram keyboards with proper state management"""

    def __init__(self, localization: LocalizationManager):
        self.localization = localization

    def get_main_menu(self, language: str = 'ru') -> Dict:
        """Get main menu keyboard"""
        web_app_text = "📱 Mini App" if language == 'ru' else "📱 Mini Ilova"

        return {
            "inline_keyboard": [
                # TEMPORARILY HIDING OTHER BUTTONS - ONLY SHOWING MINI APP
                # [
                #     {"text": self.localization.get_text('sell_button', language), "callback_data": "sell"},
                #     {"text": self.localization.get_text('buy_button', language), "callback_data": "buy"}
                # ],
                # [
                #     {"text": self.localization.get_text('my_ads', language), "callback_data": "my_ads"},
                #     {"text": self.localization.get_text('my_favorites', language), "callback_data": "my_favorites"}
                # ],
                [
                    {"text": web_app_text, "web_app": {"url": "https://telefonchiokaminiapp-production.up.railway.app"}}
                ],

                # [
                #     {"text": self.localization.get_text('language_button', language), "callback_data": "language"},
                #     {"text": self.localization.get_text('help_button', language), "callback_data": "help"}
                # ]
            ]
        }

    def get_language_keyboard(self) -> Dict:
        """Get language selection keyboard"""
        languages = self.localization.get_available_languages()
        keyboard = []

        for lang_code, lang_name in languages.items():
            keyboard.append([{"text": lang_name, "callback_data": f"lang_{lang_code}"}])

        keyboard.append([{"text": "⬅️ Назад / Orqaga", "callback_data": "back"}])

        return {"inline_keyboard": keyboard}

    def get_categories_keyboard(self, categories: List[Dict], action: str, language: str = 'ru') -> Dict:
        """Get categories keyboard for sell or buy action"""
        keyboard = []

        for category in categories:
            category_name = category.get(f'name_{language}', category.get('name_ru', 'Category'))
            keyboard.append([{
                "text": category_name,
                "callback_data": f"{action}_category_{category['id']}"
            }])

        # Add navigation buttons
        keyboard.append([
            {"text": self.localization.get_text('back_button', language), "callback_data": "back"},
            {"text": self.localization.get_text('home_button', language), "callback_data": "home"}
        ])

        return {"inline_keyboard": keyboard}

    def get_brands_keyboard(self, brands: List[Dict], action: str, language: str = 'ru') -> Dict:
        """Get brands keyboard for sell or buy action"""
        keyboard = []

        # Split brands into rows of 2
        for i in range(0, len(brands), 2):
            row = []
            for j in range(i, min(i + 2, len(brands))):
                row.append({
                    "text": brands[j]['name'],
                    "callback_data": f"{action}_brand_{brands[j]['id']}"
                })
            keyboard.append(row)

        # Add navigation buttons
        keyboard.append([
            {"text": self.localization.get_text('back_button', language), "callback_data": "back"},
            {"text": self.localization.get_text('home_button', language), "callback_data": "home"}
        ])

        return {"inline_keyboard": keyboard}

    def get_back_home_keyboard(self, language: str = 'ru') -> Dict:
        """Get back and home keyboard"""
        return {
            "inline_keyboard": [
                [
                    {"text": self.localization.get_text('back_button', language), "callback_data": "back"},
                    {"text": self.localization.get_text('home_button', language), "callback_data": "home"}
                ]
            ]
        }

    def get_contact_keyboard(self, language: str = 'ru') -> Dict:
        """Get contact sharing keyboard (reply keyboard)"""
        return {
            "keyboard": [
                [
                    {"text": self.localization.get_text('share_contact', language), "request_contact": True}
                ]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": True
        }

    def get_payment_keyboard(self, ad_id: int, language: str = 'ru') -> Dict:
        """Get payment keyboard"""
        return {
            "inline_keyboard": [
                [
                    {"text": "💳 Оплатить / To'lash", "callback_data": f"pay_{ad_id}"}
                ],
                [
                    {"text": self.localization.get_text('home_button', language), "callback_data": "home"}
                ]
            ]
        }

    def get_payment_confirm_keyboard(self, language: str = 'ru') -> Dict:
        """Get payment confirmation keyboard"""
        if language == 'uz':
            paid_text = "✅ To'ladim"
        else:
            paid_text = "✅ Оплачено"

        return {
            "inline_keyboard": [
                [
                    {"text": paid_text, "callback_data": "payment_confirmed"}
                ],
                [
                    {"text": self.localization.get_text('home_button', language), "callback_data": "home"}
                ]
            ]
        }

    def get_advertisement_keyboard(self, ad_id: int, user_id: int, language: str = 'ru') -> Dict:
        """Get advertisement action keyboard"""
        return {
            "inline_keyboard": [
                [
                    {"text": self.localization.get_text('view_details', language), "callback_data": f"view_ad_{ad_id}"},
                    {"text": self.localization.get_text('add_favorite', language), "callback_data": f"favorite_add_{ad_id}"}
                ],
                [
                    {"text": self.localization.get_text('contact_seller', language), "callback_data": f"contact_{ad_id}"}
                ],
                [
                    {"text": self.localization.get_text('back_button', language), "callback_data": "back"},
                    {"text": self.localization.get_text('home_button', language), "callback_data": "home"}
                ]
            ]
        }

    def get_favorite_keyboard(self, ad_id: int, is_favorite: bool, language: str = 'ru') -> Dict:
        """Get favorite toggle keyboard"""
        if is_favorite:
            favorite_button = {
                "text": self.localization.get_text('remove_favorite', language),
                "callback_data": f"favorite_remove_{ad_id}"
            }
        else:
            favorite_button = {
                "text": self.localization.get_text('add_favorite', language),
                "callback_data": f"favorite_add_{ad_id}"
            }

        return {
            "inline_keyboard": [
                [
                    {"text": self.localization.get_text('view_details', language), "callback_data": f"view_ad_{ad_id}"},
                    favorite_button
                ],
                [
                    {"text": self.localization.get_text('contact_seller', language), "callback_data": f"contact_{ad_id}"}
                ],
                [
                    {"text": self.localization.get_text('back_button', language), "callback_data": "back"},
                    {"text": self.localization.get_text('home_button', language), "callback_data": "home"}
                ]
            ]
        }

    def get_admin_keyboard(self, ad_id: int, language: str = 'ru') -> Dict:
        """Get admin moderation keyboard"""
        return {
            "inline_keyboard": [
                [
                    {"text": "✅ Одобрить / Tasdiqlash", "callback_data": f"approve_{ad_id}"},
                    {"text": "❌ Отклонить / Rad etish", "callback_data": f"reject_{ad_id}"}
                ],
                [
                    {"text": "📝 Причина отклонения / Rad etish sababi", "callback_data": f"reject_reason_{ad_id}"}
                ]
            ]
        }

    def get_my_ads_keyboard(self, language: str = 'ru') -> Dict:
        """Get my advertisements keyboard"""
        return {
            "inline_keyboard": [
                [
                    {"text": "📋 Все / Hammasi", "callback_data": "my_ads_all"},
                    {"text": "⏳ На модерации / Moderatsiyada", "callback_data": "my_ads_pending"}
                ],
                [
                    {"text": "✅ Одобренные / Tasdiqlangan", "callback_data": "my_ads_approved"},
                    {"text": "❌ Отклоненные / Rad etilgan", "callback_data": "my_ads_rejected"}
                ],
                [
                    {"text": self.localization.get_text('back_button', language), "callback_data": "back"},
                    {"text": self.localization.get_text('home_button', language), "callback_data": "home"}
                ]
            ]
        }

    def get_remove_keyboard(self) -> Dict:
        """Get remove keyboard markup"""
        return {
            "remove_keyboard": True
        }

    def get_done_keyboard(self, language: str = 'ru') -> Dict:
        """Get done keyboard (for completing actions)"""
        return {
            "inline_keyboard": [
                [
                    {"text": self.localization.get_text('done_button', language), "callback_data": "done"}
                ],
                [
                    {"text": self.localization.get_text('back_button', language), "callback_data": "back"},
                    {"text": self.localization.get_text('home_button', language), "callback_data": "home"}
                ]
            ]
        }

    def get_pagination_keyboard(self, current_page: int, total_pages: int, callback_prefix: str, language: str = 'ru') -> Dict:
        """Get pagination keyboard"""
        keyboard = []

        # Navigation row
        nav_row = []
        if current_page > 1:
            nav_row.append({"text": "⬅️", "callback_data": f"{callback_prefix}_page_{current_page - 1}"})

        nav_row.append({"text": f"{current_page}/{total_pages}", "callback_data": "noop"})

        if current_page < total_pages:
            nav_row.append({"text": "➡️", "callback_data": f"{callback_prefix}_page_{current_page + 1}"})

        keyboard.append(nav_row)

        # Back and home buttons
        keyboard.append([
            {"text": self.localization.get_text('back_button', language), "callback_data": "back"},
            {"text": self.localization.get_text('home_button', language), "callback_data": "home"}
        ])

        return {"inline_keyboard": keyboard}