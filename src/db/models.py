from datetime import datetime

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    BigInteger,
    Boolean,
    UniqueConstraint,
    ARRAY,
    text,
)

from schemas.general import UserRoles


Base = declarative_base()


class User(Base):  # type: ignore
    __tablename__ = "users"
    __table_args__ = {"schema": "processing"}

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String)
    roles = Column(ARRAY(String), server_default=text(f"ARRAY['{UserRoles.USER}']::text[]"))
    creation_date = Column(DateTime, default=datetime.utcnow)
    status = Column(Boolean, default=True)


class Chat(Base):  # type: ignore
    __tablename__ = "chats"
    __table_args__ = (
        UniqueConstraint("uid", "chat_id", name="uid_chatid_unique"),
        {"schema": "processing"},
    )

    id = Column(Integer, primary_key=True)
    uid = Column(ForeignKey(User.id), nullable=False)
    chat_id = Column(BigInteger, nullable=False)
    title = Column(String)
    creation_date = Column(DateTime, default=datetime.utcnow)
    status = Column(Boolean, default=True)
    type = Column(String, default="group")


class ChatLink(Base):  # type: ignore
    __tablename__ = "chat_links"
    __table_args__ = (
        UniqueConstraint("target_chat_id", "checked_chat_id", name="chat_link_unique"),
        {"schema": "processing"},
    )

    id = Column(Integer, primary_key=True)
    target_chat_id = Column(ForeignKey(Chat.id), nullable=False)
    checked_chat_id = Column(ForeignKey(Chat.id), nullable=False)
