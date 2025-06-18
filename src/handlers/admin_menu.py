from aiogram import Router, F
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from db.models import User
from handlers import utils
from schemas.callbacks.admin_menu import (
    UserInfo,
    UserInfoParameters,
    UserInfoParameterValue,
    UsersList,
)
from settings import config
from db import Session, rd
from db.manager import DBManager
from middlewares.admin_auth import AdminAuthMiddleware

admin_router = Router()

admin_router.message.middleware(AdminAuthMiddleware())
admin_router.callback_query.middleware(AdminAuthMiddleware())


@admin_router.message(F.text == "Администрирование")
async def admin_menu(message: Message) -> None:
    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text="Пользователи")],
            [KeyboardButton(text="Главное меню")],
        ],
    )

    await message.answer(text="Администрироване", reply_markup=keyboard)


@admin_router.message(F.text == "Пользователи")
@admin_router.callback_query(UsersList.filter())
async def get_users_list(update: Message | CallbackQuery, callback_data: UsersList = None) -> None:
    if isinstance(update, Message):
        message = update
        page_number = 1
    elif isinstance(update, CallbackQuery):
        message = utils.get_callback_message(update)
        if callback_data is None:
            raise ValueError("CallbackQuery must have callback_data")
        page_number = callback_data.page_number
    else:
        raise TypeError(f"Unexpected update type: {type(update)}")

    async with Session() as session:
        dbm = DBManager(session)
        users, total_pages = await dbm.get_users(page_number=page_number)

        message_text = "<code>Пользователи\n" "----------------\n"

        buttons = []
        row = []

        for i, user in enumerate(users):
            order_num = (page_number - 1) * 10 + (i + 1)
            message_text += f"{order_num}  {user.username:20} {'✅' if user.status else '❌'}\n"
            row.append(
                InlineKeyboardButton(
                    text=str(order_num), callback_data=UserInfo(user_id=user.id).pack()
                )
            )

            if len(row) == 5 or i == len(users) - 1:
                buttons.append(row)
                row = []

        pagination_row = []

        if page_number > 1:
            pagination_row.append(
                InlineKeyboardButton(
                    text="<<<", callback_data=UsersList(page_number=page_number - 1).pack()
                )
            )
        if page_number < total_pages:
            pagination_row.append(
                InlineKeyboardButton(
                    text=">>>", callback_data=UsersList(page_number=page_number + 1).pack()
                )
            )

        buttons.append(pagination_row)

        buttons.append(
            [
                InlineKeyboardButton(text="❌ Скрыть", callback_data="delete_message"),
                InlineKeyboardButton(
                    text="🔄 Обновить",
                    callback_data=UsersList(page_number=page_number).pack(),
                ),
            ]
        )

        try:
            await message.delete()
        except:
            pass

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        message_text += "</code>"

    await message.answer(text=message_text, reply_markup=keyboard)


async def send_user_info(message: Message, user: User, delete_message: bool = False) -> None:
    message_text = f"<code>{'Имя пользователя':16.16} : {user.username}\n{'Статус':16.16} : {'✅' if user.status else '❌'}</code>"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Отключить" if user.status else "Включить",
                    callback_data=UserInfo(
                        user_id=user.id,
                        parameter=UserInfoParameters.status,
                        parameter_value=UserInfoParameterValue.off
                        if user.status
                        else UserInfoParameterValue.on,
                        delete_message=True,
                    ).pack(),
                )
            ],
            [
                InlineKeyboardButton(text="❌ Скрыть", callback_data="delete_message"),
                InlineKeyboardButton(
                    text="🔄 Обновить",
                    callback_data=UserInfo(user_id=user.id, delete_message=True).pack(),
                ),
            ],
        ]
    )

    if delete_message:
        try:
            await message.delete()
        except:
            pass

    await message.answer(text=message_text, reply_markup=keyboard)


@admin_router.callback_query(UserInfo.filter(F.parameter == None))
async def get_user_info(callback: CallbackQuery, callback_data: UserInfo) -> None:
    async with Session() as session:
        dbm = DBManager(session)
        user = await dbm.get_user(uid=callback_data.user_id)

    await send_user_info(utils.get_callback_message(callback), user=user, delete_message=callback_data.delete_message)


@admin_router.callback_query(UserInfo.filter(F.parameter == UserInfoParameters.status))
async def change_user_status(callback: CallbackQuery, callback_data: UserInfo) -> None:
    async with Session() as session:
        async with session.begin():
            dbm = DBManager(session)
            user = await dbm.get_user(uid=callback_data.user_id)
            rd_key = f"{config.redis.prefix}:{user.chat_id}"

            if callback_data.parameter == UserInfoParameters.status:
                if callback_data.parameter_value == UserInfoParameterValue.on:
                    user = await dbm.update_user(uid=user.id, status=True)
                    await rd.hset(rd_key, "status", "True")
                elif callback_data.parameter_value == UserInfoParameterValue.off:
                    user = await dbm.update_user(uid=user.id, status=False)
                    await rd.hset(rd_key, "status", "False")

    await send_user_info(utils.get_callback_message(callback), user=user, delete_message=True)
