from typing import Any, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings


# Published alphabet. Short codes are a reversible encoding of sequential ids,
# so this value must not be used as a deployment secret.
PUBLIC_GENERATOR_ALPHABET = "mn6j2c4rv8bpygw95z7hsdaetxuk3fq"


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

    @field_validator("site_url")
    @classmethod
    def _site_url_scheme(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        return v if v.lower().startswith(("http://", "https://")) else None

    # Keep the token secret
    token: str = "__change_me__"
    # Required secret. The historical default is rejected at startup.
    generator_string: str = PUBLIC_GENERATOR_ALPHABET
    # Rate limiting settings
    rate_limit_create: str = "10/minute"  # Rate limit for URL creation
    rate_limit_redirect: str = "120/minute"  # Rate limit for URL redirection
    # Redis caching settings
    redis_server: Optional[str] = None  # Full Redis URL (e.g., redis://localhost:6379/0)
    redis_ttl: int = 86400  # Default TTL for cached URLs (24 hours in seconds)
    # Monitoring configuration
    metrics_enabled: bool = False  # Enable Prometheus metrics endpoint
    log_level: str = "INFO"  # Logging level: DEBUG, INFO, WARN, ERROR
    log_format: str = "text"  # Log format: text or json
    # MCP is on unless MCP_ENABLED=false. Tool calls use the HTTP rate limits.
    mcp_enabled: bool = True

    @field_validator("generator_string")
    @classmethod
    def _generator_string_secret(cls, v: str) -> str:
        if v == PUBLIC_GENERATOR_ALPHABET:
            raise ValueError(
                "GENERATOR_STRING must be set to a long random alphabet. The public default alphabet is not allowed."
            )
        if len(v) < len(PUBLIC_GENERATOR_ALPHABET):
            raise ValueError(
                "GENERATOR_STRING must be a long random alphabet "
                f"of at least {len(PUBLIC_GENERATOR_ALPHABET)} characters."
            )
        if len(set(v)) != len(v):
            raise ValueError("GENERATOR_STRING must not contain repeated characters.")
        return v


settings = Settings()


openapi_tags: list[dict[str, Any]] = [
    {
        "name": "urls",
        "description": "Operations with URLs management. The **URL** parameter is the URL to be shortened.",
    },
    {
        "name": "phishtank",
        "description": "Operations with PhishTank management. The **token** parameter is the secret "
        "token from the configuration to allow the update of the PhishTank database.",
    },
    {
        "name": "mcp",
        "description": "Model Context Protocol (MCP) endpoints for AI agent integration via SSE transport.",
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
