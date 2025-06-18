import math

from .models import User, Chat, ChatLink

from typing import Literal

from sqlalchemy import select, insert, update, delete, and_, func, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine.row import Row


class DBManager:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_user(self, chat_id: int, username: str, status: bool = True) -> User:
        user = User(chat_id=chat_id, username=username, status=status)
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_user(
        self, uid: int | None = None, chat_id: int | None = None, for_update: bool = False
    ) -> User:
        filters = {}

        if uid:
            filters["id"] = uid
        elif chat_id:
            filters["chat_id"] = chat_id
        else:
            raise ValueError("one of uid or chat_id required")

        stmt = select(User).filter_by(**filters)

        if for_update:
            stmt = stmt.with_for_update()

        user: User = (await self.session.execute(stmt)).scalars().one()

        return user

    async def update_user(self, uid: int, status: bool) -> User:
        user = await self.get_user(uid=uid, for_update=True)

        stmt = update(User).values(status=status).where(User.id == user.id).returning(User)
        updated_user: User = (await self.session.execute(stmt)).scalars().one()

        return updated_user

    async def get_users(self, page_number: int = 1, limit: int = 10) -> tuple[list[User], int]:
        stmt = select(User).offset((page_number - 1) * limit).limit(limit)
        users: list[User] = (await self.session.execute(stmt)).scalars().all()
        users_count = (await self.session.execute(select(func.count()).select_from(User))).scalar()
        total_pages = math.ceil(users_count / limit)

        return users, total_pages

    async def get_chat(self, pk_id: int | None = None, chat_id: int | None = None) -> Row:
        stmt = (
            select(
                Chat.id,
                Chat.chat_id,
                Chat.uid,
                Chat.type,
                Chat.title,
                Chat.creation_date,
                Chat.status,
                func.coalesce(ChatLink.target_chat_id, None).label("target_chat_id"),
            )
            .outerjoin(ChatLink, ChatLink.checked_chat_id == Chat.id)
            .order_by(asc(Chat.id))
        )

        if pk_id:
            stmt = stmt.filter(Chat.id == pk_id)
        if chat_id:
            stmt = stmt.filter(Chat.chat_id == chat_id)

        return (await self.session.execute(stmt)).first()

    async def get_chats(
        self, user_id: int | None = None, chat_type: Literal["group", "channel"] | None = None
    ) -> list[Chat]:
        stmt = select(Chat)

        if user_id:
            stmt = stmt.filter_by(uid=user_id)
        if chat_type:
            stmt = stmt.filter_by(type=chat_type)

        chats: list[Chat] = (await self.session.execute(stmt)).scalars().all()
        return chats

    async def add_chat(
        self, title: str, chat_id: int, user_id: int, chat_type: Literal["group", "channel"]
    ) -> Chat:
        chat = Chat(title=title, chat_id=chat_id, uid=user_id, type=chat_type)
        self.session.add(chat)
        await self.session.flush()

        return chat

    async def delete_chat(self, pk_id: int) -> Chat:
        chat: Chat = await self.session.get(Chat, pk_id)
        await self.session.delete(chat)
        await self.session.flush()
        return chat

    async def get_linked_chats(self, target_chat_id: int) -> list[Chat]:
        stmt = (
            select(Chat)
            .outerjoin(
                ChatLink,
                Chat.id == ChatLink.checked_chat_id,
            )
            .where(ChatLink.target_chat_id == target_chat_id, ChatLink.target_chat_id.is_not(None))
        )

        chats: list[Chat] = (await self.session.execute(stmt)).scalars().all()

        return chats

    async def get_unlinked_chats(self, target_chat_id: int, user_id: int) -> list[Chat]:
        stmt = (
            select(Chat)
            .outerjoin(
                ChatLink,
                Chat.id == ChatLink.checked_chat_id,
            )
            .where(Chat.id != target_chat_id, Chat.uid == user_id)
        )

        chats: list[Chat] = (await self.session.execute(stmt)).scalars().all()

        return chats

    async def add_chat_link(self, target_chat_id: int, checked_chat_id: int) -> ChatLink:
        chat_link = ChatLink(
            target_chat_id=target_chat_id,
            checked_chat_id=checked_chat_id,
        )
        self.session.add(chat_link)
        await self.session.flush()

        return chat_link

    async def delete_chat_link(self, target_chat_id: int, checked_chat_id: int) -> ChatLink:
        stmt = select(ChatLink).where(
            (ChatLink.target_chat_id == target_chat_id) &
            (ChatLink.checked_chat_id == checked_chat_id)
        )
        chat_link: ChatLink = (await self.session.execute(stmt)).scalars().one()
        await self.session.delete(chat_link)
        await self.session.flush()

        return chat_link
