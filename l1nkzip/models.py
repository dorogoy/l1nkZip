from datetime import datetime, timezone
from pathlib import Path
from typing import List

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
        return str(Path(settings.api_domain, self.link))


class PhishTank(db.Entity):  # type: ignore
    _table_ = "phishtanks"
    id = PrimaryKey(int, size=32)
    url = Required(str, index=True)
    phish_detail_url = Optional(str)
    updated_at = Required(
        datetime, sql_type="TIMESTAMP WITH TIME ZONE", default=utcnow_zone_aware
    )


@db_session
def insert_link(url) -> Link:
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


@db_session
def get_visits(limit: int = 100) -> List[LinkInfo]:
    return [
        LinkInfo(
            link=link.link,
            full_link=link.full_link,
            url=link.url,
            visits=link.visits,
        )
        for link in list(Link.select()[:limit])
    ]


@db_session
def check_db_connection():
    try:
        with db_session:
            db.select("SELECT 1")
            return True
    except Exception as e:
        raise Exception(f"Database connection error: {e}")
