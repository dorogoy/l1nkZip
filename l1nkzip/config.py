from typing import Any, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_name: str = "l1nkZip"
    api_domain: str = "https://l1nk.zip"
    db_type: str = "inmemory"
    db_name: str = "l1nkzip.sqlite"
    db_user: Optional[str] = None
    db_password: Optional[str] = None
    db_host: Optional[str] = None
    db_dsn: Optional[str] = None
    phishtank: Optional[str] = None
    site_url: Optional[str] = "https://dorogoy.github.io/l1nkZip/"
    # Keep the token secret
    token: str = "__change_me__"
    # Change this to your own random generator string
    generator_string: str = "mn6j2c4rv8bpygw95z7hsdaetxuk3fq"
    # Rate limiting settings
    rate_limit_create: str = "5/minute"  # Rate limit for URL creation
    rate_limit_redirect: str = "60/minute"  # Rate limit for URL redirection


settings = Settings()


openapi_tags: list[dict[str, Any]] = [
    {
        "name": "urls",
        "description": "Operations with URLs management. The **URL** parameter is the URL to be shortened.",
    },
    {
        "name": "phishtank",
        "description": "Operations with PhishTank management. The **token** parameter is the secret token from the configuration to allow the update of the PhishTank database.",
    },
]


ponyorm_settings = {
    "inmemory": {"provider": "sqlite", "filename": ":sharedmemory:"},
    "sqlite": {
        "provider": settings.db_type,
        "filename": settings.db_name,
        "create_db": True,
    },
    "postgres": {
        "provider": settings.db_type,
        "user": settings.db_user,
        "password": settings.db_password,
        "database": settings.db_name,
        "host": settings.db_host,
    },
    "mysql": {
        "provider": settings.db_type,
        "user": settings.db_user,
        "passwd": settings.db_password,
        "database": settings.db_name,
        "host": settings.db_host,
    },
    "oracle": {
        "provider": settings.db_type,
        "user": settings.db_user,
        "password": settings.db_password,
        "dsn": settings.db_dsn,
    },
    "cockroachdb": {
        "provider": settings.db_type,
        "user": settings.db_user,
        "password": settings.db_password,
        "database": settings.db_name,
        "host": settings.db_host,
        "sslmode": "disable",
    },
}
