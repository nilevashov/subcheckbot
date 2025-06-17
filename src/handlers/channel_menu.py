from aiogram import Router
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.exceptions import TelegramBadRequest
from aiogram import F

from bot import bot
from db import Session
from db.manager import DBManager

from sqlalchemy.exc import NoResultFound, IntegrityError

from schemas.callbacks.channel_menu import (
    ChannelsList,
    ChannelInfo,
    UnpinChannel,
    DeleteChannel,
)
from schemas.callbacks.chat_menu import ChatInfo
from . import utils


channel_router = Router()


async def send_channels_list(message: Message):
    async with Session() as session:
        async with session.begin():
            dbm = DBManager(session)
            try:
                user = await dbm.get_user(chat_id=message.chat.id)
                channels = await dbm.get_chats(user_id=user.id, chat_type="channel")
            except NoResultFound:
                channels = []

            message_text = "<code>Список ваших каналов:\n" "----------------------\n"

            buttons = [[]]

            for i, channel in enumerate(channels):
                message_text += f"{i+1:2}  {channel.title}\n"
                buttons[0].append(
                    InlineKeyboardButton(
                        text=str(i + 1),
                        callback_data=ChannelInfo(channel_id=channel.id).pack(),
                    )
                )

            buttons.append(
                [
                    InlineKeyboardButton(text="❌ Скрыть", callback_data="delete_message"),
                ]
            )

            message_text += "</code>"

            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

            await utils.send_message(message, message_text, keyboard)


@channel_router.message(F.text == "Каналы")
@channel_router.callback_query(ChannelsList.filter())
async def get_channels_list(update, callback_data: ChannelsList = None):
    if isinstance(update, Message):
        message = update
    elif isinstance(update, CallbackQuery):
        message = update.message
    else:
        return

    await send_channels_list(message)


async def send_channel_info(message: Message, channel_id: int, from_chat_section: bool = False):
    async with Session() as session:
        async with session.begin():
            dbm = DBManager(session)
            channel = await dbm.get_chat(pk_id=channel_id)

            if channel.target_chat_id:
                chat = await dbm.get_chat(pk_id=channel.target_chat_id)
                chat_title = chat.title
            else:
                chat_title = "Нет"

            message_text = (
                "<code>Информация о канале/чате\n"
                "-------------\n"
                f"Название: {channel.title}\n"
                f"Привязан к чату: {chat_title}</code>"
            )

            buttons = [
                [
                    InlineKeyboardButton(
                        text="Удалить",
                        callback_data=DeleteChannel(channel_id=channel.id).pack(),
                    )
                ],
                [
                    (
                        InlineKeyboardButton(
                            text="⬅ Назад",
                            callback_data=ChatInfo(group_id=channel.target_chat_id).pack(),
                        )
                        if from_chat_section
                        else InlineKeyboardButton(
                            text="⬅ Назад",
                            callback_data=ChannelsList().pack(),
                        )
                    ),
                    InlineKeyboardButton(
                        text="❌ Скрыть",
                        callback_data=f"delete_message",
                    ),
                ],
            ]

            if channel.target_chat_id:
                buttons[0].append(
                    InlineKeyboardButton(
                        text="Отвязать от чата",
                        callback_data=UnpinChannel(
                            channel_id=channel.id, group_id=channel.target_chat_id
                        ).pack(),
                    )
                )

            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

            await utils.send_message(message, message_text, keyboard)


@channel_router.callback_query(ChannelInfo.filter())
async def get_channel_info(callback: CallbackQuery, callback_data: ChannelInfo):
    await send_channel_info(message=callback.message, **callback_data.model_dump())


@channel_router.callback_query(UnpinChannel.filter())
async def unpin_channel_from_chat(callback: CallbackQuery, callback_data: UnpinChannel):
    async with Session() as session:
        async with session.begin():
            dbm = DBManager(session)
            await dbm.delete_chat_link(
                checked_chat_id=callback_data.channel_id, target_chat_id=callback_data.group_id
            )

    await send_channel_info(message=callback.message, channel_id=callback_data.channel_id)


@channel_router.callback_query(DeleteChannel.filter())
async def delete_channel(callback: CallbackQuery, callback_data: DeleteChannel):
    async with Session() as session:
        async with session.begin():
            dbm = DBManager(session)
            await dbm.delete_chat(pk_id=callback_data.channel_id)

    await send_channels_list(callback.message)


@channel_router.message(
    F.chat_shared,
    lambda message: message.chat_shared.request_id == 1 and message.chat.type == "private",
)
async def channel_shared(message: Message):
    try:
        chat_info = await bot.get_chat(chat_id=message.chat_shared.chat_id)
    except TelegramBadRequest:
        await message.answer(
            text=(
                "Нельзя добавить канал. "
                "Сначала добавьте бота в этот канал с правами администратора"
            )
        )
        return
    async with Session() as session:
        async with session.begin():
            dbm = DBManager(session)
            user = await dbm.get_user(chat_id=message.chat.id)
            try:
                channel = await dbm.add_chat(
                    chat_id=chat_info.id,
                    title=chat_info.title,
                    user_id=user.id,
                    chat_type="channel",
                )
                await session.commit()
            except IntegrityError:
                await message.answer(text="Канал уже добавлен в бот")
                return

    await send_channel_info(message=message, channel_id=channel.id)
