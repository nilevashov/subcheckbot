from aiogram import Router, F
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from aiogram.exceptions import TelegramBadRequest

from bot import bot, utils
from db import Session
from db.manager import DBManager

from sqlalchemy.exc import NoResultFound, IntegrityError

from bot.schemas.callbacks.channel_menu import ChannelInfo
from bot.schemas.callbacks.chat_menu import (
    ChatsList,
    ChannelsListForPin,
    ChatInfo,
    DeleteChat,
    PinChannelToChat,
)

chat_router = Router()


async def send_chats_list(message: Message) -> None:
    async with Session() as session:
        async with session.begin():
            dbm = DBManager(session)
            try:
                user = await dbm.get_user(chat_id=message.chat.id)
                groups = await dbm.get_chats(user_id=user.id, chat_type="group")
            except NoResultFound:
                groups = []

            message_text = "<code>Список ваших чатов:\n" "----------------------\n"

            buttons: list[list[InlineKeyboardButton]] = [[]]

            for i, group in enumerate(groups):
                message_text += f"{i+1:2}  {group.title}\n"
                buttons[0].append(
                    InlineKeyboardButton(
                        text=str(i + 1), callback_data=ChatInfo(group_id=group.id).pack()
                    )
                )

            buttons.append(
                [InlineKeyboardButton(text="❌ Скрыть", callback_data="delete_message")]
            )

            message_text += "</code>"

            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

            await utils.send_message(message=message, message_text=message_text, keyboard=keyboard)


@chat_router.message(F.text == "Чаты")
@chat_router.callback_query(ChatsList.filter())
async def get_chats_list(update: Message | CallbackQuery) -> None:
    if isinstance(update, Message):
        message = update
    elif isinstance(update, CallbackQuery):
        message = utils.get_callback_message(update)
    else:
        return

    await send_chats_list(message)


async def send_chat_info(message: Message, group_id: int) -> None:
    async with Session() as session:
        async with session.begin():
            dbm = DBManager(session)
            chat_info = await dbm.get_chat(pk_id=group_id)
            message_text = (
                "<code>Информация о чате\n"
                "-------------\n"
                f"Название: {chat_info.title}\n\n"
                f"----- Проверяемые каналы/чаты -----\n"
            )

            channels = await dbm.get_linked_chats(target_chat_id=group_id)

            buttons: list[list[InlineKeyboardButton]] = [[]]

            for i, channel in enumerate(channels):
                message_text += f"{i+1:2}  {channel.title}\n"
                buttons[0].append(
                    InlineKeyboardButton(
                        text=str(i + 1),
                        callback_data=ChannelInfo(
                            channel_id=channel.id, from_chat_section=True
                        ).pack(),
                    )
                )

            message_text += "</code>"
            buttons.append(
                [
                    InlineKeyboardButton(
                        text="➕ Привязать канал/чат",
                        callback_data=ChannelsListForPin(group_id=chat_info.id).pack(),
                    ),
                    InlineKeyboardButton(
                        text="Удалить", callback_data=DeleteChat(group_id=group_id).pack()
                    ),
                ]
            )
            buttons.append(
                [
                    InlineKeyboardButton(
                        text="⬅ Назад",
                        callback_data=ChatsList().pack(),
                    ),
                    InlineKeyboardButton(
                        text="❌ Скрыть",
                        callback_data="delete_message",
                    ),
                ]
            )

            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

            await utils.send_message(message=message, message_text=message_text, keyboard=keyboard)


@chat_router.callback_query(ChatInfo.filter())
async def get_chat_info(callback: CallbackQuery, callback_data: ChatInfo) -> None:
    await send_chat_info(utils.get_callback_message(callback), **callback_data.model_dump())


@chat_router.callback_query(ChannelsListForPin.filter())
async def get_channel_list_for_pin(
    callback: CallbackQuery, callback_data: ChannelsListForPin
) -> None:
    async with Session() as session:
        async with session.begin():
            dbm = DBManager(session)
            user = await dbm.get_user(chat_id=callback.from_user.id)
            channels = await dbm.get_unlinked_chats(
                target_chat_id=callback_data.group_id, user_id=user.id
            )
            message_text = (
                "<code>Выберите канал/чат, который вы хотите закрепить за чатом\n"
                "-------------\n"
            )

            buttons: list[list[InlineKeyboardButton]] = [[]]

            for i, channel in enumerate(channels):
                message_text += f"{i+1:2}  {channel.title}\n"
                buttons[0].append(
                    InlineKeyboardButton(
                        text=str(i + 1),
                        callback_data=PinChannelToChat(
                            channel_id=channel.id, group_id=callback_data.group_id
                        ).pack(),
                    )
                )

            buttons.append(
                [
                    InlineKeyboardButton(
                        text="⬅ Назад",
                        callback_data=ChatInfo(group_id=callback_data.group_id).pack(),
                    ),
                    InlineKeyboardButton(text="❌ Скрыть", callback_data="delete_message"),
                ]
            )

            message_text += "</code>"

            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

            await utils.send_message(
                message=utils.get_callback_message(callback),
                message_text=message_text,
                keyboard=keyboard,
            )


@chat_router.callback_query(PinChannelToChat.filter())
async def pin_channel_to_chat(callback: CallbackQuery, callback_data: PinChannelToChat) -> None:
    async with Session() as session:
        async with session.begin():
            dbm = DBManager(session)
            await dbm.add_chat_link(
                checked_chat_id=callback_data.channel_id, target_chat_id=callback_data.group_id
            )
            # chat = await dbm.get_group(group_id=group_id)
            # await callback.message.answer(
            #     text=f"Канал <code>{channel.title}</code> успешно привязан к чату "
            #     f"<code>{chat.title}</code>! "
            #     f"Теперь участникам чата необходимо подписаться на канал "
            #     f"<code>{channel.title}</code>, "
            #     f"чтобы писать в чате <code>{chat.title}</code>"
            # )
    await send_chat_info(utils.get_callback_message(callback), group_id=callback_data.group_id)


@chat_router.callback_query(DeleteChat.filter())
async def delete_chat_handler(callback: CallbackQuery, callback_data: DeleteChat) -> None:
    async with Session() as session:
        async with session.begin():
            dbm = DBManager(session)
            group = await dbm.delete_chat(pk_id=callback_data.group_id)

        await send_chats_list(utils.get_callback_message(callback))

        message = utils.get_callback_message(callback)
        await message.answer(text=f"Чат <code>{group.title}</code> успешно удален из бота")


@chat_router.message(
    F.chat_shared,
    lambda message: message.chat_shared.request_id == 2 and message.chat.type == "private",
)
async def chat_shared(message: Message) -> None:
    assert message.chat_shared is not None

    try:
        chat_info = await bot.get_chat(chat_id=message.chat_shared.chat_id)
    except TelegramBadRequest:
        await message.answer(
            text="Нельзя добавить чат. Сначала добавьте бота в этот чат с правами администратора"
        )
        return
    async with Session() as session:
        async with session.begin():
            dbm = DBManager(session)
            user = await dbm.get_user(chat_id=message.chat.id)
            try:
                group = await dbm.add_chat(
                    chat_id=chat_info.id, title=chat_info.title, user_id=user.id, chat_type="group"
                )
                await session.commit()
            except IntegrityError:
                await message.answer(text="Чат уже был добавлен вами ранее")
                return
            await send_chat_info(message, group_id=group.id)

            # await message.answer(text="Чат успешно добавлен")
