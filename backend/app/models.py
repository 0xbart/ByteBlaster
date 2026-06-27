from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Table, func
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


sound_tags = Table(
    "sound_tags",
    Base.metadata,
    Column("sound_id", Integer, ForeignKey("sounds.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    Index("ix_sound_tags_tag_id", "tag_id"),
)


sound_favorites = Table(
    "sound_favorites",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("sound_id", Integer, ForeignKey("sounds.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "created_at",
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    ),
    Index("ix_sound_favorites_user", "user_id"),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    ip: Mapped[str] = mapped_column(INET, unique=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_superadmin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_mutemaster: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_banned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    # NULL while banned = indefinite ban; otherwise the ban auto-expires at this time.
    ban_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    sounds: Mapped[list["Sound"]] = relationship(back_populates="uploader")
    plays: Mapped[list["Play"]] = relationship(back_populates="user")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    sounds: Mapped[list["Sound"]] = relationship(back_populates="category")


class Sound(Base):
    __tablename__ = "sounds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    original_filename: Mapped[str | None] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(64), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    uploaded_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    uploader: Mapped[User] = relationship(back_populates="sounds")
    category: Mapped[Category | None] = relationship(back_populates="sounds")
    tags: Mapped[list["Tag"]] = relationship(secondary=sound_tags, back_populates="sounds")
    plays: Mapped[list["Play"]] = relationship(back_populates="sound", cascade="all, delete-orphan")

    __table_args__ = (Index("ix_sounds_created_at_desc", created_at.desc()),)


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    sounds: Mapped[list[Sound]] = relationship(secondary=sound_tags, back_populates="tags")


class Play(Base):
    __tablename__ = "plays"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sound_id: Mapped[int] = mapped_column(
        ForeignKey("sounds.id", ondelete="CASCADE"), nullable=False
    )
    played_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    played_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    sound: Mapped[Sound] = relationship(back_populates="plays")
    user: Mapped[User] = relationship(back_populates="plays")

    __table_args__ = (Index("ix_plays_played_at_desc", played_at.desc()),)
