import asyncio
import secrets

from mcp.server import Server
from mcp.server.sse import SseServerTransport
import mcp.types as types

from l1nkzip import config
from l1nkzip.cache import cache
from l1nkzip.logging import get_logger
from l1nkzip.metrics import metrics


logger = get_logger(__name__)

mcp_server = Server("l1nkzip-mcp-server")

sse_transport = SseServerTransport("/mcp/messages")


@mcp_server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="shorten_url",
            description="Shorten a long URL and return the short link.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The long URL to shorten (must start with http:// or https://)",
                    }
                },
                "required": ["url"],
            },
        ),
        types.Tool(
            name="get_original_url",
            description="Retrieve the destination URL for a previously shortened link.",
            inputSchema={
                "type": "object",
                "properties": {
                    "link": {
                        "type": "string",
                        "description": "The short link identifier (4-20 chars from [a-zA-Z0-9_-]).",
                    }
                },
                "required": ["link"],
            },
        ),
        types.Tool(
            name="list_urls",
            description="List shortened URLs with their stats. Requires admin authorization (token).",
            inputSchema={
                "type": "object",
                "properties": {
                    "token": {
                        "type": "string",
                        "description": "Admin authorization token.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of URLs to return (1-1000).",
                        "default": 100,
                    },
                },
                "required": ["token"],
            },
        ),
    ]


@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "shorten_url":
        return await _handle_shorten_url(arguments)
    if name == "get_original_url":
        return await _handle_get_original_url(arguments)
    if name == "list_urls":
        return await _handle_list_urls(arguments)
    raise ValueError(f"Unknown tool: {name}")


async def _handle_shorten_url(arguments: dict) -> list[types.TextContent]:
    from fastapi import HTTPException

    from l1nkzip.main import insert_link, retry_phishtank_check, validate_url

    if not isinstance(arguments, dict):
        raise ValueError("Invalid arguments: expected object")

    url = arguments.get("url")
    if not url:
        raise ValueError("Missing required parameter: url")

    if not isinstance(url, str):
        raise ValueError("Invalid URL: must be a string")

    try:
        validated_url = validate_url(url)
    except HTTPException as e:
        raise ValueError(f"Invalid URL: {e.detail}") from e
    except Exception as e:
        raise ValueError(f"Invalid URL: {e}") from e

    if config.settings.phishtank:
        try:
            phish = await retry_phishtank_check(validated_url)
        except Exception as e:
            logger.warning("PhishTank check failed in shorten_url", extra={"error": str(e), "url": validated_url})
            phish = None
        if phish:
            if config.settings.metrics_enabled:
                try:
                    metrics.record_phishing_block()
                except Exception as metric_exc:
                    logger.warning("metrics.record_phishing_block failed", extra={"error": str(metric_exc)})
            detail = str(getattr(phish, "phish_detail_url", "")) or "https://phishtank.org/"
            raise ValueError(f"URL is flagged as phishing. Details: {detail}")

    loop = asyncio.get_running_loop()
    try:
        link_data = await loop.run_in_executor(None, insert_link, validated_url)
    except Exception as e:
        logger.error("MCP shorten_url insert failed", extra={"error": str(e), "url": validated_url})
        raise ValueError("Failed to create short URL") from e

    link = getattr(link_data, "link", None)
    if not link:
        raise ValueError("Failed to create short URL: invalid link data")

    if config.settings.metrics_enabled:
        try:
            metrics.record_url_created()
        except Exception as metric_exc:
            logger.warning("metrics.record_url_created failed", extra={"error": str(metric_exc)})

    api_domain = config.settings.api_domain
    if not api_domain:
        raise ValueError("api_domain is not configured")
    short_url = f"{api_domain.rstrip('/')}/{link}"
    return [types.TextContent(type="text", text=short_url)]


async def _handle_get_original_url(arguments: dict) -> list[types.TextContent]:
    from fastapi import HTTPException

    from l1nkzip.main import retry_phishtank_check, set_visit, validate_short_link
    from l1nkzip.models import increment_visit_async

    if not isinstance(arguments, dict):
        raise ValueError("Invalid arguments: expected object")

    link = arguments.get("link")
    if not link:
        raise ValueError("Missing required parameter: link")

    if not isinstance(link, str):
        raise ValueError("Invalid short link: must be a string")

    try:
        validated_link = validate_short_link(link)
    except HTTPException as e:
        raise ValueError(f"Invalid short link: {e.detail}") from e
    except Exception as e:
        raise ValueError(f"Invalid short link: {e}") from e

    loop = asyncio.get_running_loop()
    original_url: str | None = None
    cache_hit = False

    if cache.is_enabled():
        try:
            cached_url = await cache.get(f"redirect:{validated_link}")
            if isinstance(cached_url, bytes):
                cached_url = cached_url.decode()
            if config.settings.metrics_enabled:
                metrics.record_cache_operation("get", hit=bool(cached_url))
            if cached_url:
                original_url = cached_url
                cache_hit = True
        except Exception as e:
            logger.error("Cache get error in get_original_url", extra={"error": str(e), "link": validated_link})
            if config.settings.metrics_enabled:
                try:
                    metrics.record_cache_operation("get", success=False)
                except Exception as metric_exc:
                    logger.warning("metrics.record_cache_operation failed", extra={"error": str(metric_exc)})

    if original_url is None:
        try:
            link_data = await loop.run_in_executor(None, set_visit, validated_link)
        except Exception as e:
            logger.error(
                "Database error in get_original_url",
                extra={"error": str(e), "link": validated_link},
            )
            raise ValueError("Failed to retrieve short URL") from e

        if not link_data:
            raise ValueError(f"Short link not found: {validated_link}")

        original_url = getattr(link_data, "url", None)
        if not original_url:
            raise ValueError("Failed to retrieve short URL: invalid link data")
        original_url = str(original_url)

        if cache.is_enabled():
            try:
                await cache.set(f"redirect:{validated_link}", original_url)
                if config.settings.metrics_enabled:
                    metrics.record_cache_operation("set", success=True)
            except Exception as e:
                logger.error(
                    "Cache set error in get_original_url",
                    extra={"error": str(e), "link": validated_link},
                )
                if config.settings.metrics_enabled:
                    try:
                        metrics.record_cache_operation("set", success=False)
                    except Exception as metric_exc:
                        logger.warning("metrics.record_cache_operation failed", extra={"error": str(metric_exc)})

    if config.settings.phishtank:
        try:
            phish = await retry_phishtank_check(original_url)
        except Exception as e:
            logger.warning("PhishTank check failed in get_original_url", extra={"error": str(e), "url": original_url})
            phish = None
        if phish:
            if config.settings.metrics_enabled:
                try:
                    metrics.record_phishing_block()
                except Exception as metric_exc:
                    logger.warning("metrics.record_phishing_block failed", extra={"error": str(metric_exc)})
            detail = str(getattr(phish, "phish_detail_url", "")) or "https://phishtank.org/"
            raise ValueError(f"URL is flagged as phishing. Details: {detail}")

    if config.settings.metrics_enabled:
        try:
            metrics.record_redirect()
        except Exception as metric_exc:
            logger.warning("metrics.record_redirect failed", extra={"error": str(metric_exc)})

    if cache_hit:
        asyncio.create_task(_safe_increment_visit(increment_visit_async, validated_link))

    return [types.TextContent(type="text", text=original_url)]


async def _handle_list_urls(arguments: dict) -> list[types.TextContent]:
    import json

    from fastapi import HTTPException

    from l1nkzip.main import validate_admin_token
    from l1nkzip.models import get_visits

    if not isinstance(arguments, dict):
        raise ValueError("Invalid arguments: expected object")

    token = arguments.get("token")
    if not isinstance(token, str):
        raise ValueError("Unauthorized")

    try:
        validate_admin_token(token)
    except HTTPException:
        raise ValueError("Unauthorized") from None
    except Exception:
        raise ValueError("Unauthorized") from None

    if not secrets.compare_digest(token, config.settings.token):
        raise ValueError("Unauthorized")

    limit = arguments.get("limit", 100)
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise ValueError("Invalid limit: must be an integer")
    if limit < 1 or limit > 1000:
        raise ValueError("Limit must be between 1 and 1000")

    loop = asyncio.get_running_loop()
    try:
        link_list = await loop.run_in_executor(None, get_visits, limit)
    except Exception as e:
        logger.error("MCP list_urls retrieval failed", extra={"error": str(e), "limit": limit})
        raise ValueError("Failed to retrieve URL list") from e

    try:
        data = [item.model_dump(mode="json") for item in link_list]
    except Exception as e:
        logger.error("MCP list_urls serialization failed", extra={"error": str(e), "limit": limit})
        raise ValueError("Failed to retrieve URL list") from e
    return [types.TextContent(type="text", text=json.dumps(data, default=str))]


async def _safe_increment_visit(increment_fn, link: str) -> None:
    try:
        await increment_fn(link)
    except Exception as e:
        logger.warning("Async visit increment failed", extra={"error": str(e), "link": link})
