from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from settings import config
from bot import bot
from db import Session, rd
from db.manager import DBManager

from sqlalchemy.exc import NoResultFound

from loguru import logger

group_router = Router()


@group_router.message(lambda message: message.chat.type == "supergroup")
async def handler_group_message(message: Message):
    if message.from_user.username and message.from_user.username == "GroupAnonymousBot":
        return

    async with Session() as session:
        async with session.begin():
            dbm = DBManager(session)
            try:
                group = await dbm.get_chat(chat_id=message.chat.id)

                if not group:
                    if config.debug:
                        logger.warning(
                            f"Chat not found in DB | {message.chat.title=} | {message.chat.id=}"
                        )
                    return

                checked_chats = await dbm.get_linked_chats(target_chat_id=group.id)
                user = await dbm.get_user(uid=group.uid)
            except NoResultFound:
                return

            if not user.status:
                return

            data = {
                "id": group.id,
                "owner_user_id": group.uid,
                "chat_id": group.chat_id,
                "chat_title": group.title,
                "tg_username": message.from_user.username,
                "tg_fullname": message.from_user.full_name,
                "tg_user_id": message.from_user.id,
            }

            buttons = []

            for chat in checked_chats:
                try:
                    chat_obj = await bot.get_chat(chat_id=chat.chat_id)
                except (TelegramBadRequest, TelegramForbiddenError):
                    logger.warning(
                        f"Message sent to channel, where bot is not admin or kicked | "
                        f"{chat.title=} | {chat.chat_id=}"
                    )
                    return

                # TODO: Сделать проверку есть ли бот в канале,
                # если нет, то писать создателю канала в бот, чтобы добавил его

                try:
                    user_channel_status = await bot.get_chat_member(
                        chat_id=chat.chat_id, user_id=message.from_user.id
                    )
                except (TelegramBadRequest, TelegramForbiddenError):
                    logger.warning(
                        f"Bot not found in channel | {chat.title} | {chat.chat_id} | {data=}"
                    )
                    # Здесь отправка в celery
                    return

                if (
                    user_channel_status.status != ChatMemberStatus.MEMBER
                    and user_channel_status.status != ChatMemberStatus.CREATOR
                    and user_channel_status.status != ChatMemberStatus.ADMINISTRATOR
                ):
                    invite_link = (
                        f"https://t.me/{chat_obj.username}" if chat_obj.username
                        else chat_obj.invite_link
                    )
                    buttons.append(
                        [
                            InlineKeyboardButton(
                                text=f"Подписаться на {chat.title}",
                                url=invite_link,
                            )
                        ]
                    )

            if buttons:
                keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
                rd_key = f"subchecker:bot:mediagroup_id:{message.media_group_id}"

                mention = (
                    f"@{message.from_user.username}"
                    if message.from_user.username
                    else f'<a href="tg://user?id={message.from_user.id}">'
                    f"{message.from_user.full_name}"
                    f"</a>"
                )

                if (
                    message.from_user.username
                    and "channel_bot" in message.from_user.username.lower()
                ):
                    message_text = (
                        "В данный чат нельзя писать от имени канала. Переключитесь на "
                        "сообщения от своего лица, чтобы избежать удаления сообщения"
                    )
                else:
                    bot_info = await message.bot.get_me()
                    message_text = (
                        f"{mention} подпишитесь на каналы/чаты ниже, "
                        f"чтобы писать сообщения в этот чат\n\n"
                        f"❔ Хотите проверять подписки в своем чате? "
                        f"Переходите в бот "
                        f'<a href="https://t.me/{bot_info.username}">{bot_info.first_name}</a>. '
                        f"Это просто и бесплатно 😉"
                    )

                try:
                    if not message.media_group_id:
                        await message.answer(
                            text=message_text,
                            reply_markup=keyboard,
                            parse_mode="HTML",
                            disable_web_page_preview=True,
                        )
                    elif not await rd.hget(rd_key, "123"):
                        await rd.hset(rd_key, "123", "123")
                        await rd.expire(rd_key, 10)

                        await message.answer(
                            text=message_text,
                            reply_markup=keyboard,
                            parse_mode="HTML",
                            disable_web_page_preview=True,
                        )
                except TelegramBadRequest as ex:
                    logger.error(f"Telegram error | {ex=} | chat_info={dict(group)}")
                    return

                try:
                    await message.delete()
                except Exception as ex:
                    logger.error(f"Message to delete not found | ex={ex} | {message=}")

                logger.warning(f"message restricted | {data=}")
            else:
                logger.success(f"message approved | {data=}")
