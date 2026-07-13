from sqlalchemy.orm import DeclarativeBase, mapped_column, relationship
from sqlalchemy import String, DateTime, JSON, ForeignKey

class Base(DeclarativeBase):
    pass

class Profile(Base):
    __tablename__ = "profiles"

    user_id = mapped_column(String, primary_key=True)
    major = mapped_column(String, nullable=True)
    level = mapped_column(String, nullable=True)
    year = mapped_column(String, nullable=True)
    personalization_notes = mapped_column(String, nullable=True)

class Conversation(Base):
    __tablename__ = "conversations"

    id = mapped_column(String, primary_key=True)
    title = mapped_column(String, nullable=True)
    profile_id = mapped_column(String, ForeignKey("profiles.user_id"), nullable=True)

class Message(Base):
    __tablename__ = "messages"

    id = mapped_column(String, primary_key=True)
    role = mapped_column(String, nullable=False)
    text = mapped_column(String, nullable=False)
    content = mapped_column(JSON, nullable=True)
    created_at = mapped_column(DateTime, nullable=False)
    conversation_id = mapped_column(String, ForeignKey("conversations.id"), nullable=False)
