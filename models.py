from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class TelegramUser(BaseModel):
    id: int
    is_bot: bool
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None
    is_premium: Optional[bool] = None

class Chat(BaseModel):
    id: int
    type: str
    title: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class PhotoSize(BaseModel):
    file_id: str
    file_unique_id: str
    width: int
    height: int
    file_size: Optional[int] = None

class Contact(BaseModel):
    phone_number: str
    first_name: str
    last_name: Optional[str] = None
    user_id: Optional[int] = None
    vcard: Optional[str] = None

class MessageEntity(BaseModel):
    type: str
    offset: int
    length: int
    url: Optional[str] = None
    user: Optional[TelegramUser] = None
    language: Optional[str] = None

class Message(BaseModel):
    message_id: int
    from_: Optional[TelegramUser] = Field(None, alias="from")
    sender_chat: Optional[Chat] = None
    date: int
    chat: Chat
    forward_from: Optional[TelegramUser] = None
    forward_from_chat: Optional[Chat] = None
    forward_from_message_id: Optional[int] = None
    forward_signature: Optional[str] = None
    forward_sender_name: Optional[str] = None
    forward_date: Optional[int] = None
    is_automatic_forward: Optional[bool] = None
    reply_to_message: Optional["Message"] = None
    via_bot: Optional[TelegramUser] = None
    edit_date: Optional[int] = None
    has_protected_content: Optional[bool] = None
    media_group_id: Optional[str] = None
    author_signature: Optional[str] = None
    text: Optional[str] = None
    entities: Optional[List[MessageEntity]] = None
    animation: Optional[Dict[str, Any]] = None
    audio: Optional[Dict[str, Any]] = None
    document: Optional[Dict[str, Any]] = None
    photo: Optional[List[PhotoSize]] = None
    sticker: Optional[Dict[str, Any]] = None
    video: Optional[Dict[str, Any]] = None
    video_note: Optional[Dict[str, Any]] = None
    voice: Optional[Dict[str, Any]] = None
    caption: Optional[str] = None
    caption_entities: Optional[List[MessageEntity]] = None
    contact: Optional[Contact] = None
    dice: Optional[Dict[str, Any]] = None
    game: Optional[Dict[str, Any]] = None
    poll: Optional[Dict[str, Any]] = None
    venue: Optional[Dict[str, Any]] = None
    location: Optional[Dict[str, Any]] = None
    new_chat_members: Optional[List[TelegramUser]] = None
    left_chat_member: Optional[TelegramUser] = None
    new_chat_title: Optional[str] = None
    new_chat_photo: Optional[List[PhotoSize]] = None
    delete_chat_photo: Optional[bool] = None
    group_chat_created: Optional[bool] = None
    supergroup_chat_created: Optional[bool] = None
    channel_chat_created: Optional[bool] = None
    message_auto_delete_timer_changed: Optional[Dict[str, Any]] = None
    migrate_to_chat_id: Optional[int] = None
    migrate_from_chat_id: Optional[int] = None
    pinned_message: Optional["Message"] = None
    invoice: Optional[Dict[str, Any]] = None
    successful_payment: Optional[Dict[str, Any]] = None
    connected_website: Optional[str] = None
    passport_data: Optional[Dict[str, Any]] = None
    proximity_alert_triggered: Optional[Dict[str, Any]] = None
    video_chat_scheduled: Optional[Dict[str, Any]] = None
    video_chat_started: Optional[Dict[str, Any]] = None
    video_chat_ended: Optional[Dict[str, Any]] = None
    video_chat_participants_invited: Optional[Dict[str, Any]] = None
    web_app_data: Optional[Dict[str, Any]] = None
    reply_markup: Optional[Dict[str, Any]] = None

class InlineKeyboardButton(BaseModel):
    text: str
    url: Optional[str] = None
    callback_data: Optional[str] = None
    web_app: Optional[Dict[str, Any]] = None
    login_url: Optional[Dict[str, Any]] = None
    switch_inline_query: Optional[str] = None
    switch_inline_query_current_chat: Optional[str] = None
    callback_game: Optional[Dict[str, Any]] = None
    pay: Optional[bool] = None

class CallbackQuery(BaseModel):
    id: str
    from_: TelegramUser = Field(alias="from")
    message: Optional[Message] = None
    inline_message_id: Optional[str] = None
    chat_instance: str
    data: Optional[str] = None
    game_short_name: Optional[str] = None

class InlineQuery(BaseModel):
    id: str
    from_: TelegramUser = Field(alias="from")
    query: str
    offset: str
    chat_type: Optional[str] = None
    location: Optional[Dict[str, Any]] = None

class ChosenInlineResult(BaseModel):
    result_id: str
    from_: TelegramUser = Field(alias="from")
    location: Optional[Dict[str, Any]] = None
    inline_message_id: Optional[str] = None
    query: str

class ShippingQuery(BaseModel):
    id: str
    from_: TelegramUser = Field(alias="from")
    invoice_payload: str
    shipping_address: Dict[str, Any]

class PreCheckoutQuery(BaseModel):
    id: str
    from_: TelegramUser = Field(alias="from")
    currency: str
    total_amount: int
    invoice_payload: str
    shipping_option_id: Optional[str] = None
    order_info: Optional[Dict[str, Any]] = None

class Poll(BaseModel):
    id: str
    question: str
    options: List[Dict[str, Any]]
    total_voter_count: int
    is_closed: bool
    is_anonymous: bool
    type: str
    allows_multiple_answers: bool
    correct_option_id: Optional[int] = None
    explanation: Optional[str] = None
    explanation_entities: Optional[List[MessageEntity]] = None
    open_period: Optional[int] = None
    close_date: Optional[int] = None

class PollAnswer(BaseModel):
    poll_id: str
    user: TelegramUser
    option_ids: List[int]

class ChatMemberUpdated(BaseModel):
    chat: Chat
    from_: TelegramUser = Field(alias="from")
    date: int
    old_chat_member: Dict[str, Any]
    new_chat_member: Dict[str, Any]
    invite_link: Optional[Dict[str, Any]] = None

class ChatJoinRequest(BaseModel):
    chat: Chat
    from_: TelegramUser = Field(alias="from")
    date: int
    bio: Optional[str] = None
    invite_link: Optional[Dict[str, Any]] = None

class TelegramUpdate(BaseModel):
    update_id: int
    message: Optional[Message] = None
    edited_message: Optional[Message] = None
    channel_post: Optional[Message] = None
    edited_channel_post: Optional[Message] = None
    inline_query: Optional[InlineQuery] = None
    chosen_inline_result: Optional[ChosenInlineResult] = None
    callback_query: Optional[CallbackQuery] = None
    shipping_query: Optional[ShippingQuery] = None
    pre_checkout_query: Optional[PreCheckoutQuery] = None
    poll: Optional[Poll] = None
    poll_answer: Optional[PollAnswer] = None
    my_chat_member: Optional[ChatMemberUpdated] = None
    chat_member: Optional[ChatMemberUpdated] = None
    chat_join_request: Optional[ChatJoinRequest] = None

# Database models
class User(BaseModel):
    id: int
    telegram_id: int
    first_name: Optional[str] = None
    username: Optional[str] = None
    language_code: str = "ru"
    state: str = "idle"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Category(BaseModel):
    id: int
    name_ru: str
    name_uz: str
    icon: str
    is_active: bool = True
    created_at: Optional[datetime] = None

class Brand(BaseModel):
    id: int
    category_id: int
    name: str
    is_active: bool = True
    created_at: Optional[datetime] = None

class Advertisement(BaseModel):
    id: int
    user_id: int
    category_id: int
    brand_id: int
    model: str
    price: str
    city: str
    contact_phone: str
    photo_path: Optional[str] = None
    status: str = "pending"
    rejection_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Favorite(BaseModel):
    id: int
    user_id: int
    advertisement_id: int
    created_at: Optional[datetime] = None

# API Response models
class ApiResponse(BaseModel):
    status: str
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class BotStats(BaseModel):
    total_users: int
    total_ads: int
    pending_ads: int
    approved_ads: int
    total_categories: int
    total_brands: int