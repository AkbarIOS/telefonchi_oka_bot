from typing import Optional, Dict, List, Tuple
import os
import uuid
from datetime import datetime
import logging
from app.repositories.database import DatabaseRepository
from app.services.telegram_service import TelegramService
from app.core.config import settings

logger = logging.getLogger(__name__)


class AdvertisementService:
    """Service for advertisement-related business logic"""

    def __init__(self, db_repository: DatabaseRepository, telegram_service: TelegramService, config: settings):
        self.db = db_repository
        self.telegram = telegram_service
        self.config = config

    async def create_sell_advertisement(
        self,
        user_id: int,
        category_id: int,
        brand_id: int,
        model: str,
        price: int,
        description: str,
        phone: str,
        city: str,
        contact_phone: str,
        photo_path: str = None
    ) -> Tuple[bool, Optional[int], str]:
        """Create new sell advertisement"""
        try:
            # Validate advertisement data
            data = {
                'user_id': user_id,
                'category_id': category_id,
                'brand_id': brand_id,
                'model': model,
                'price': price,
                'description': description,
                'phone': phone,
                'city': city,
                'contact_phone': contact_phone,
                'photo_path': photo_path
            }

            is_valid, errors = await self.validate_advertisement_data(data)
            if not is_valid:
                return False, None, f"Validation failed: {', '.join(errors)}"

            ad_id = await self.db.create_advertisement(
                user_id=user_id,
                category_id=category_id,
                brand_id=brand_id,
                model=model,
                price=price,
                description=description,
                phone=phone,
                city=city,
                contact_phone=contact_phone,
                photo_path=photo_path
            )

            if ad_id:
                logger.info(f"Created advertisement {ad_id} for user {user_id}")
                return True, ad_id, "Advertisement created successfully"
            else:
                return False, None, "Failed to create advertisement"

        except Exception as e:
            logger.error(f"Error creating advertisement: {e}")
            return False, None, f"Error: {str(e)}"

    async def search_buy_advertisements(
        self,
        category_id: int = None,
        brand_id: int = None,
        search_term: str = None,
        max_results: int = 50
    ) -> List[Dict]:
        """Search advertisements for buying"""
        try:
            return await self.db.search_advertisements(
                category_id=category_id,
                brand_id=brand_id,
                search_term=search_term,
                status='approved'
            )
        except Exception as e:
            logger.error(f"Error searching advertisements: {e}")
            return []

    async def get_advertisement_details(self, ad_id: int) -> Optional[Dict]:
        """Get full advertisement details"""
        try:
            return await self.db.get_advertisement(ad_id)
        except Exception as e:
            logger.error(f"Error getting advertisement {ad_id}: {e}")
            return None

    async def get_categories(self, type_filter: str = None) -> List[Dict]:
        """Get all categories"""
        try:
            return await self.db.get_categories(type_filter)
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []

    async def get_brands(self, category_id: int = None) -> List[Dict]:
        """Get brands, optionally filtered by category"""
        try:
            return await self.db.get_brands(category_id)
        except Exception as e:
            logger.error(f"Error getting brands: {e}")
            return []

    async def approve_advertisement(self, ad_id: int) -> Tuple[bool, str]:
        """Approve advertisement for publication"""
        try:
            affected_rows = await self.db.update_advertisement_status(ad_id, 'approved')
            if affected_rows > 0:
                logger.info(f"Approved advertisement {ad_id}")
                return True, "Advertisement approved"
            else:
                return False, "Advertisement not found"
        except Exception as e:
            logger.error(f"Error approving advertisement {ad_id}: {e}")
            return False, f"Error: {str(e)}"

    async def reject_advertisement(self, ad_id: int, reason: str) -> Tuple[bool, str]:
        """Reject advertisement with reason"""
        try:
            affected_rows = await self.db.update_advertisement_status(ad_id, 'rejected', reason)
            if affected_rows > 0:
                logger.info(f"Rejected advertisement {ad_id} with reason: {reason}")
                return True, "Advertisement rejected"
            else:
                return False, "Advertisement not found"
        except Exception as e:
            logger.error(f"Error rejecting advertisement {ad_id}: {e}")
            return False, f"Error: {str(e)}"

    async def get_pending_advertisements(self) -> List[Dict]:
        """Get all pending advertisements for moderation"""
        try:
            return await self.db.get_pending_advertisements()
        except Exception as e:
            logger.error(f"Error getting pending advertisements: {e}")
            return []

    async def save_uploaded_photo(self, file_content: bytes, file_extension: str) -> Tuple[bool, str]:
        """Save uploaded photo and return path"""
        try:
            logger.info(f"Attempting to save photo, content size: {len(file_content)} bytes")

            # Validate file content
            if not file_content:
                logger.error("File content is empty")
                return False, "Empty file content"

            # Create uploads directory if it doesn't exist
            upload_dir = os.path.abspath(self.config.upload_dir)
            logger.info(f"Creating upload directory: {upload_dir}")
            os.makedirs(upload_dir, exist_ok=True)

            # Generate unique filename
            filename = f"{uuid.uuid4()}{file_extension}"
            file_path = os.path.join(upload_dir, filename)
            logger.info(f"Saving file to: {file_path}")

            # Save file
            try:
                with open(file_path, 'wb') as f:
                    f.write(file_content)

                # Verify file was saved
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    logger.info(f"Successfully saved photo: {file_path}, size: {file_size} bytes")
                    return True, file_path
                else:
                    logger.error(f"File was not saved: {file_path}")
                    return False, "File was not saved"

            except IOError as e:
                logger.error(f"IO Error saving file {file_path}: {e}")
                return False, f"IO Error: {str(e)}"

        except Exception as e:
            logger.error(f"Error saving photo: {e}")
            logger.exception("Full photo save error traceback:")
            return False, f"Error: {str(e)}"

    async def validate_advertisement_data(self, data: Dict) -> Tuple[bool, List[str]]:
        """Validate advertisement data before creation"""
        errors = []

        # Required fields
        required_fields = ['category_id', 'brand_id', 'model', 'price', 'description', 'phone', 'photo_path']
        for field in required_fields:
            if not data.get(field):
                if field == 'photo_path':
                    errors.append("Photo is required for advertisement")
                else:
                    errors.append(f"Missing required field: {field}")

        # Price validation
        try:
            price = int(data.get('price', 0))
            if price <= 0:
                errors.append("Price must be greater than 0")
            if price > 999999999:  # 999 million max
                errors.append("Price is too high")
        except (ValueError, TypeError):
            errors.append("Invalid price format")

        # Model length validation
        model = data.get('model', '')
        if len(model) < 2:
            errors.append("Model name is too short")
        if len(model) > 100:
            errors.append("Model name is too long")

        # Description length validation
        description = data.get('description', '')
        if len(description) < 10:
            errors.append("Description is too short (minimum 10 characters)")
        if len(description) > 1000:
            errors.append("Description is too long (maximum 1000 characters)")

        # Phone validation (basic)
        phone = data.get('phone', '')
        if len(phone) < 9:
            errors.append("Phone number is too short")
        if len(phone) > 20:
            errors.append("Phone number is too long")

        # Photo validation
        photo_path = data.get('photo_path')
        if photo_path and not os.path.exists(photo_path):
            errors.append("Photo file does not exist")

        return len(errors) == 0, errors

    async def create_payment_request(self, user_id: int, ad_id: int) -> Tuple[bool, Optional[int], str]:
        """Create payment request for advertisement"""
        try:
            payment_id = await self.db.create_payment(
                user_id=user_id,
                ad_id=ad_id,
                amount=self.config.advertisement_price
            )

            if payment_id:
                logger.info(f"Created payment request {payment_id} for user {user_id}, ad {ad_id}")
                return True, payment_id, "Payment request created"
            else:
                return False, None, "Failed to create payment request"

        except Exception as e:
            logger.error(f"Error creating payment request: {e}")
            return False, None, f"Error: {str(e)}"

    async def process_payment_receipt(self, payment_id: int, receipt_path: str) -> Tuple[bool, str]:
        """Process uploaded payment receipt"""
        try:
            affected_rows = await self.db.update_payment_receipt(payment_id, receipt_path)
            if affected_rows > 0:
                logger.info(f"Updated payment {payment_id} with receipt: {receipt_path}")
                return True, "Receipt uploaded successfully"
            else:
                return False, "Payment not found"

        except Exception as e:
            logger.error(f"Error processing payment receipt: {e}")
            return False, f"Error: {str(e)}"

    async def get_payment_details(self, payment_id: int) -> Optional[Dict]:
        """Get payment details"""
        try:
            return await self.db.get_payment(payment_id)
        except Exception as e:
            logger.error(f"Error getting payment {payment_id}: {e}")
            return None

    async def format_advertisement_text(self, ad: Dict, language: str = 'ru') -> str:
        """Format advertisement for display"""
        try:
            category_name = ad.get('category_name_uz' if language == 'uz' else 'category_name', 'N/A')

            # Safely format price
            try:
                price = int(ad.get('price', 0))
                formatted_price = f"{price:,}".replace(",", " ")
            except (ValueError, TypeError):
                formatted_price = str(ad.get('price', 'N/A'))

            if language == 'uz':
                text = f"""
📱 <b>{ad['model']}</b>

📂 Kategoriya: {category_name}
🏷️ Brend: {ad['brand_name']}
💰 Narx: {formatted_price} so'm
📞 Telefon: {ad['contact_phone']}

📝 Tavsif:
{ad['description']}

👤 Foydalanuvchi: @{ad.get('username', 'N/A')}
📅 E'lon qilingan: {ad['created_at'].strftime('%d.%m.%Y')}
"""
            else:
                text = f"""
📱 <b>{ad['model']}</b>

📂 Категория: {category_name}
🏷️ Бренд: {ad['brand_name']}
💰 Цена: {formatted_price} сум
📞 Телефон: {ad['contact_phone']}

📝 Описание:
{ad['description']}

👤 Пользователь: @{ad.get('username', 'N/A')}
📅 Опубликовано: {ad['created_at'].strftime('%d.%m.%Y')}
"""
            return text.strip()

        except Exception as e:
            logger.error(f"Error formatting advertisement text: {e}")
            return "Ошибка отображения объявления / E'lonni ko'rsatishda xatolik"

    async def get_category_statistics(self) -> Dict:
        """Get statistics by category"""
        try:
            categories = await self.db.get_categories()
            stats = {}

            for category in categories:
                ads = await self.db.search_advertisements(
                    category_id=category['id'],
                    status='approved'
                )
                stats[category['name_ru']] = len(ads)

            return stats
        except Exception as e:
            logger.error(f"Error getting category statistics: {e}")
            return {}

    async def search_user_advertisements_by_status(self, user_id: int, status: str) -> List[Dict]:
        """Search user's advertisements by status"""
        try:
            return await self.db.get_user_advertisements(user_id, status)
        except Exception as e:
            logger.error(f"Error searching user advertisements: {e}")
            return []

    async def mark_advertisement_sold(self, ad_id: int, user_id: int) -> Tuple[bool, str]:
        """Mark advertisement as sold"""
        try:
            # First verify that the advertisement belongs to the user
            ad = await self.db.get_advertisement(ad_id)
            if not ad:
                return False, "Advertisement not found"

            # Get user's internal ID from telegram ID
            user = await self.db.get_user(user_id)
            if not user:
                return False, "User not found"

            # Check if the ad belongs to the user
            if ad['user_id'] != user['id']:
                return False, "You can only mark your own advertisements as sold"

            # Check if the ad is approved (only approved ads can be marked as sold)
            if ad['status'] != 'approved':
                return False, "Only approved advertisements can be marked as sold"

            # Update advertisement status to sold
            affected_rows = await self.db.update_advertisement_status(ad_id, 'sold')
            if affected_rows > 0:
                logger.info(f"Marked advertisement {ad_id} as sold by user {user_id}")
                return True, "Advertisement marked as sold successfully"
            else:
                return False, "Failed to update advertisement status"

        except Exception as e:
            logger.error(f"Error marking advertisement {ad_id} as sold: {e}")
            return False, f"Error: {str(e)}"