from aiogram import Router
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    CallbackQuery,
    KeyboardButtonRequestChat,
    ReplyKeyboardRemove,
    ChatAdministratorRights,
)

from schemas.general import UserRoles
from settings import config
from db import Session, rd
from db.manager import DBManager

from loguru import logger

from sqlalchemy.exc import NoResultFound

start_router = Router()


@start_router.message(
    lambda message: message.chat.type == "private"
    and (message.text == "/start" or message.text == "Главное меню"),
)
async def command_start_handler(message: Message) -> None:
    assert message.from_user is not None

    async with Session() as session:
        async with session.begin():
            dbm = DBManager(session)

            try:
                user = await dbm.get_user(chat_id=message.chat.id)
            except NoResultFound:
                user = await dbm.add_user(
                    chat_id=message.chat.id,
                    username=message.chat.username if message.chat.username else "",
                    status=True,
                )

            user_data = {
                "id": user.id,
                "username": user.username,
                "status": str(user.status),
            }

            async with rd.lock(f"lock-{config.redis.prefix}:{message.chat.id}"):
                rd_key = f"{config.redis.prefix}:{message.chat.id}"
                await rd.hmset(rd_key, user_data)

            logger.info(f"Update user redis data | {user_data=} | {rd_key=}")

            if not user.status:
                await message.answer(
                    "Доступ к боту ограничен",
                    reply_markup=ReplyKeyboardRemove(),
                )
                return

            message_text = (
                f"Привет, {message.from_user.full_name}!\n\n"
                "Инструкция по работе с ботом\n\n"
                "1⃣ Добавьте бота в канал и в чат в качестве администратора\n\n"
                "2⃣ Добавьте каналы и чаты, нажав на соответствующие кнопки "
                "меню: <b>➕ Добавить канал</b> и <b>➕ Добавить чат</b>\n\n"
                "3⃣ Для закрепления канала за чатом, перейдите в раздел меню <b>Чаты</b> и "
                "выберите нужный чат\n\n"
                "4️⃣ В появившемся меню нажмите на кнопку <b>➕ Привязать канал</b> "
                "и выберите нужный канал в появившемся списке\n\n"
                "Готово! Если нужно добавить еще канал для чата, добавьте канал и так же "
                "привяжите канал к нужному чату. Бот будет проверять подписку на все "
                "привязанные к чату каналы\n\n"
                "Удачного пользования :)"
            )

            bot_rights = ChatAdministratorRights(
                can_edit_messages=True,
                can_post_messages=True,
                can_delete_messages=True,
                can_manage_chat=False,
                can_manage_topics=False,
                can_manage_video_chats=False,
                can_pin_messages=False,
                can_invite_users=False,
                can_change_info=False,
                can_edit_stories=False,
                can_post_stories=False,
                can_delete_stories=False,
                can_promote_members=False,
                can_restrict_members=False,
                is_anonymous=False,
            )

            user_rights = ChatAdministratorRights(
                can_edit_messages=True,
                can_post_messages=True,
                can_delete_messages=True,
                can_manage_chat=False,
                can_manage_topics=False,
                can_manage_video_chats=False,
                can_pin_messages=False,
                can_invite_users=True,
                can_change_info=False,
                can_edit_stories=False,
                can_post_stories=False,
                can_delete_stories=False,
                can_promote_members=True,
                can_restrict_members=True,
                is_anonymous=False,
            )

            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    (
                        [KeyboardButton(text="Администрирование")]
                        if UserRoles.ADMIN in user.roles
                        else []
                    ),
                    [KeyboardButton(text="Каналы"), KeyboardButton(text="Чаты")],
                    [
                        KeyboardButton(
                            text="➕ Добавить канал",
                            request_chat=KeyboardButtonRequestChat(
                                request_id=1,
                                chat_is_channel=True,
                                bot_administrator_rights=bot_rights,
                                user_administrator_rights=user_rights,
                            ),
                        ),
                        KeyboardButton(
                            text="➕ Добавить чат",
                            request_chat=KeyboardButtonRequestChat(
                                request_id=2,
                                chat_is_channel=False,
                                bot_administrator_rights=bot_rights,
                                user_administrator_rights=user_rights,
                            ),
                        ),
                    ],
                ],
                resize_keyboard=True,
            )

            await message.answer(message_text, reply_markup=keyboard)


@start_router.callback_query(lambda callback: callback.data == "delete_message")
async def delete_message(callback: CallbackQuery) -> None:
    if not isinstance(callback.message, Message):
        raise ValueError("callback.message must be Message")

    await callback.message.delete()
