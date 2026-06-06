from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    ip: str
    is_admin: bool
    is_superadmin: bool
    is_mutemaster: bool = False
    created_at: datetime

    @field_validator("ip", mode="before")
    @classmethod
    def _stringify_ip(cls, v: Any) -> Any:
        # SQLAlchemy's INET column hands us an ipaddress.IPv4Address / IPv6Address.
        return str(v) if v is not None else v


class MeOut(BaseModel):
    user: UserOut | None
    needs_claim: bool
    ip: str


class ClaimIn(BaseModel):
    username: str = Field(min_length=2, max_length=64, pattern=r"^[A-Za-z0-9_\- ]+$")


class UserPatchIn(BaseModel):
    is_admin: bool | None = None
    is_mutemaster: bool | None = None


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime
    sound_count: int = 0


class CategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=64)


class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime
    sound_count: int = 0


class SoundOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    display_name: str
    mime_type: str
    size_bytes: int
    uploaded_by_user_id: int
    uploader_username: str
    category_id: int | None
    category_name: str | None
    tags: list[str]
    created_at: datetime
    url: str
    is_favorite: bool = False
    duration_ms: int | None = None


class SoundPatchIn(BaseModel):
    # PATCH semantics via Pydantic's `exclude_unset`: omit a field to leave it
    # unchanged; send `category_id: null` to clear the category;
    # send `tags: []` to clear all tags.
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    category_id: int | None = None
    tags: list[str] | None = None


class SoundStatOut(BaseModel):
    sound_id: int
    display_name: str
    category_name: str | None
    play_count: int


class UserStatOut(BaseModel):
    user_id: int
    username: str
    play_count: int


class CategoryStatOut(BaseModel):
    category_id: int | None
    category_name: str | None
    play_count: int


class OverviewStatOut(BaseModel):
    total_sounds: int
    total_users: int
    total_plays: int
    plays_day: int
    plays_week: int
    plays_month: int


class ExploreResult(BaseModel):
    title: str
    mp3_url: str


class ExploreSearchOut(BaseModel):
    query: str
    page: int
    results: list[ExploreResult]
    has_more: bool


class YoutubeFetchIn(BaseModel):
    url: str = Field(min_length=4, max_length=512)


class YoutubeFetchOut(BaseModel):
    title: str
    duration_ms: int
    preview_url: str


class PlayOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sound_id: int
    sound_display_name: str
    played_by_user_id: int
    played_by_username: str
    played_at: datetime


# WebSocket events (documented; not part of OpenAPI)

class WsPlayEvent(BaseModel):
    type: Literal["play"] = "play"
    sound_id: int
    sound_url: str
    display_name: str
    by: str
    at: datetime


class WsSoundAddedEvent(BaseModel):
    type: Literal["sound_added"] = "sound_added"
    sound: SoundOut
    by: str


class WsSoundUpdatedEvent(BaseModel):
    type: Literal["sound_updated"] = "sound_updated"
    sound: SoundOut
    by: str


class WsSoundRemovedEvent(BaseModel):
    type: Literal["sound_removed"] = "sound_removed"
    sound_id: int
    display_name: str
    by: str


class WsTagRemovedEvent(BaseModel):
    type: Literal["tag_removed"] = "tag_removed"
    name: str


class WsTagRenamedEvent(BaseModel):
    type: Literal["tag_renamed"] = "tag_renamed"
    id: int
    old_name: str
    new_name: str


class WsCategoryRenamedEvent(BaseModel):
    type: Literal["category_renamed"] = "category_renamed"
    id: int
    new_name: str


class PresenceUser(BaseModel):
    id: int
    username: str
    ip: str
    is_admin: bool = False
    is_superadmin: bool = False
    volume: int = 100

    @field_validator("ip", mode="before")
    @classmethod
    def _stringify_ip(cls, v: Any) -> Any:
        return str(v) if v is not None else v


class WsPresenceEvent(BaseModel):
    type: Literal["presence"] = "presence"
    users: list[PresenceUser]


class GlobalMuteState(BaseModel):
    active: bool
    by: str | None = None
    at: datetime | None = None
    expires_at: datetime | None = None


class GlobalMuteSetIn(BaseModel):
    active: bool
    # null = forever; otherwise minutes until auto-unmute.
    duration_minutes: int | None = None


class WsGlobalMuteEvent(BaseModel):
    type: Literal["global_mute"] = "global_mute"
    active: bool
    by: str | None = None
    at: datetime | None = None
    expires_at: datetime | None = None


class WsStopAllEvent(BaseModel):
    type: Literal["stop_all"] = "stop_all"
    by: str
