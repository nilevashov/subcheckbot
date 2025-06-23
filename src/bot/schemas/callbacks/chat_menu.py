from aiogram.filters.callback_data import CallbackData


class ChatsList(CallbackData, prefix="user_chats_list"): ...


class ChatInfo(CallbackData, prefix="user_chat_info"):
    group_id: int


class ChannelsListForPin(CallbackData, prefix="channels_for_pin"):
    group_id: int


class DeleteChat(CallbackData, prefix="delete_chat"):
    group_id: int


class PinChannelToChat(CallbackData, prefix="pin_channel_to_chat"):
    channel_id: int
    group_id: int
