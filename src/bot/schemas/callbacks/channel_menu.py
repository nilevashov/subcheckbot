from aiogram.filters.callback_data import CallbackData


class ChannelsList(CallbackData, prefix="user_channels_list"): ...


class ChannelInfo(CallbackData, prefix="user_channel_info"):
    channel_id: int
    from_chat_section: bool = False


class UnpinChannel(CallbackData, prefix="unpin_channel"):
    channel_id: int
    group_id: int


class DeleteChannel(CallbackData, prefix="delete_channel"):
    channel_id: int
