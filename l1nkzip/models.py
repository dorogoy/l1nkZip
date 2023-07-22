from datetime import datetime, timezone
from pathlib import Path

from pony.orm import Database, Optional, PrimaryKey, Required, db_session
from pydantic import BaseModel, HttpUrl

from l1nkzip import generator
from l1nkzip.config import settings

db = Database()


class Url(BaseModel):
    url: HttpUrl


class LinkInfo(BaseModel):
    link: str
    full_link: HttpUrl
    url: HttpUrl
    visits: int


class GenericInfo(BaseModel):
    detail: str


def utcnow_zone_aware():
    return datetime.now(tz=timezone.utc)


def build_link(id: int) -> str:
    return generator.encode_url(id)


class Link(db.Entity):  # type: ignore
    _table_ = "links"
    id = PrimaryKey(int, size=32, auto=True)
    link = Optional(str, index=True, unique=True)
    url = Required(str, index=True)
    created_at = Required(
        datetime, sql_type="TIMESTAMP WITH TIME ZONE", default=utcnow_zone_aware
    )
    visits = Required(int, default=0)

    @property
    def full_link(self) -> str:
        return str(Path(settings.domain_redirect, self.link))


class PhishTank(db.Entity):  # type: ignore
    _table_ = "phishtanks"
    id = PrimaryKey(int, size=32)
    url = Required(str, index=True)
    phish_detail_url = Optional(str)
    updated_at = Required(
        datetime, sql_type="TIMESTAMP WITH TIME ZONE", default=utcnow_zone_aware
    )


@db_session
def insert_link(url):
    already_exists = Link.get(url=url)
    if already_exists:
        return already_exists
    link_data = Link(url=url)
    link_data.flush()
    link_data.link = build_link(link_data.id)
    return link_data


@db_session
def set_visit(link) -> Link:
    link_data = Link.get(link=link)
    if link_data:
        link_data.visits += 1
    return link_data