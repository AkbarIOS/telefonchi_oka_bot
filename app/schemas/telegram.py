from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field


class TelegramUser(BaseModel):
    id: int
    is_bot: bool
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None


class TelegramChat(BaseModel):
    id: int
    type: str
    title: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class TelegramPhotoSize(BaseModel):
    file_id: str
    file_unique_id: str
    width: int
    height: int
    file_size: Optional[int] = None


class TelegramContact(BaseModel):
    phone_number: str
    first_name: str
    last_name: Optional[str] = None
    user_id: Optional[int] = None


class TelegramMessage(BaseModel):
    message_id: int
    from_: Optional[TelegramUser] = Field(None, alias="from")
    sender_chat: Optional[TelegramChat] = None
    date: int
    chat: TelegramChat
    forward_from: Optional[TelegramUser] = None
    forward_from_chat: Optional[TelegramChat] = None
    forward_from_message_id: Optional[int] = None
    forward_signature: Optional[str] = None
    forward_sender_name: Optional[str] = None
    forward_date: Optional[int] = None
    is_automatic_forward: Optional[bool] = None
    reply_to_message: Optional['TelegramMessage'] = None
    via_bot: Optional[TelegramUser] = None
    edit_date: Optional[int] = None
    has_protected_content: Optional[bool] = None
    media_group_id: Optional[str] = None
    author_signature: Optional[str] = None
    text: Optional[str] = None
    entities: Optional[List[Dict[str, Any]]] = None
    animation: Optional[Dict[str, Any]] = None
    audio: Optional[Dict[str, Any]] = None
    document: Optional[Dict[str, Any]] = None
    photo: Optional[List[TelegramPhotoSize]] = None
    sticker: Optional[Dict[str, Any]] = None
    video: Optional[Dict[str, Any]] = None
    video_note: Optional[Dict[str, Any]] = None
    voice: Optional[Dict[str, Any]] = None
    caption: Optional[str] = None
    caption_entities: Optional[List[Dict[str, Any]]] = None
    contact: Optional[TelegramContact] = None
    dice: Optional[Dict[str, Any]] = None
    game: Optional[Dict[str, Any]] = None
    poll: Optional[Dict[str, Any]] = None
    venue: Optional[Dict[str, Any]] = None
    location: Optional[Dict[str, Any]] = None
    new_chat_members: Optional[List[TelegramUser]] = None
    left_chat_member: Optional[TelegramUser] = None
    new_chat_title: Optional[str] = None
    new_chat_photo: Optional[List[TelegramPhotoSize]] = None
    delete_chat_photo: Optional[bool] = None
    group_chat_created: Optional[bool] = None
    supergroup_chat_created: Optional[bool] = None
    channel_chat_created: Optional[bool] = None
    message_auto_delete_timer_changed: Optional[Dict[str, Any]] = None
    migrate_to_chat_id: Optional[int] = None
    migrate_from_chat_id: Optional[int] = None
    pinned_message: Optional['TelegramMessage'] = None
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


class TelegramCallbackQuery(BaseModel):
    id: str
    from_: TelegramUser = Field(..., alias="from")
    message: Optional[TelegramMessage] = None
    inline_message_id: Optional[str] = None
    chat_instance: str
    data: Optional[str] = None
    game_short_name: Optional[str] = None


class TelegramInlineQuery(BaseModel):
    id: str
    from_: TelegramUser = Field(..., alias="from")
    query: str
    offset: str
    chat_type: Optional[str] = None
    location: Optional[Dict[str, Any]] = None


class TelegramChosenInlineResult(BaseModel):
    result_id: str
    from_: TelegramUser = Field(..., alias="from")
    location: Optional[Dict[str, Any]] = None
    inline_message_id: Optional[str] = None
    query: str


class TelegramShippingQuery(BaseModel):
    id: str
    from_: TelegramUser = Field(..., alias="from")
    invoice_payload: str
    shipping_address: Dict[str, Any]


class TelegramPreCheckoutQuery(BaseModel):
    id: str
    from_: TelegramUser = Field(..., alias="from")
    currency: str
    total_amount: int
    invoice_payload: str
    shipping_option_id: Optional[str] = None
    order_info: Optional[Dict[str, Any]] = None


class TelegramPoll(BaseModel):
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
    explanation_entities: Optional[List[Dict[str, Any]]] = None
    open_period: Optional[int] = None
    close_date: Optional[int] = None


class TelegramPollAnswer(BaseModel):
    poll_id: str
    user: TelegramUser
    option_ids: List[int]


class TelegramMyChatMember(BaseModel):
    chat: TelegramChat
    from_: TelegramUser = Field(..., alias="from")
    date: int
    old_chat_member: Dict[str, Any]
    new_chat_member: Dict[str, Any]


class TelegramChatMember(BaseModel):
    chat: TelegramChat
    from_: TelegramUser = Field(..., alias="from")
    date: int
    old_chat_member: Dict[str, Any]
    new_chat_member: Dict[str, Any]


class TelegramChatJoinRequest(BaseModel):
    chat: TelegramChat
    from_: TelegramUser = Field(..., alias="from")
    date: int
    bio: Optional[str] = None
    invite_link: Optional[Dict[str, Any]] = None


class TelegramUpdate(BaseModel):
    update_id: int
    message: Optional[TelegramMessage] = None
    edited_message: Optional[TelegramMessage] = None
    channel_post: Optional[TelegramMessage] = None
    edited_channel_post: Optional[TelegramMessage] = None
    inline_query: Optional[TelegramInlineQuery] = None
    chosen_inline_result: Optional[TelegramChosenInlineResult] = None
    callback_query: Optional[TelegramCallbackQuery] = None
    shipping_query: Optional[TelegramShippingQuery] = None
    pre_checkout_query: Optional[TelegramPreCheckoutQuery] = None
    poll: Optional[TelegramPoll] = None
    poll_answer: Optional[TelegramPollAnswer] = None
    my_chat_member: Optional[TelegramMyChatMember] = None
    chat_member: Optional[TelegramChatMember] = None
    chat_join_request: Optional[TelegramChatJoinRequest] = None


# Forward reference resolution
TelegramMessage.model_rebuild()