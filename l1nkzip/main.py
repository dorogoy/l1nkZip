import asyncio
from contextlib import asynccontextmanager
import ipaddress
from pathlib import Path
import re
import secrets
import socket
from typing import List, Optional
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Request, responses, status
from fastapi.templating import Jinja2Templates
from pydantic import HttpUrl
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.extension import Limiter
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
import validators

from l1nkzip.cache import cache
from l1nkzip.config import openapi_tags, ponyorm_settings, settings
from l1nkzip.logging import get_logger
from l1nkzip.mcp import mcp_request, mcp_server, sse_transport
from l1nkzip.metrics import metrics, record_request_end, record_request_start
from l1nkzip.models import (
    GenericInfo,
    LinkInfo,
    Url,
    check_db_connection,
    db,
    get_visits,
    increment_visit_async,
    insert_link,
    set_visit,
)
from l1nkzip.phishtank import (
    PhishTank,
    delete_old_phishes,
    get_phish,
    update_phishtanks,
)
from l1nkzip.version import VERSION_NUMBER


logger = get_logger(__name__)


# Constants
MIN_CLEANUP_DAYS = 1
MAX_CLEANUP_DAYS = 365


# Validation helper functions
def _is_blocked_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Address classes that must never be accepted as shortening targets."""
    if isinstance(ip, ipaddress.IPv6Address):
        # Unwrapping embedded IPv4 addresses fully delegates evaluation to the
        # embedded target IPv4 address, allowing valid public IPv4 destinations
        # while blocking private/loopback/non-global targets.
        if ip.ipv4_mapped is not None:
            return _is_blocked_ip(ip.ipv4_mapped)
        if ip.sixtofour is not None:
            return _is_blocked_ip(ip.sixtofour)
        # Check Well-Known Prefix for NAT64 (64:ff9b::/96)
        if ip.packed.startswith(b"\x00\x64\xff\x9b" + b"\x00" * 8):
            return _is_blocked_ip(ipaddress.IPv4Address(ip.packed[-4:]))
        # Check Local-Use Prefix for NAT64 (64:ff9b:1::/48, RFC 8215)
        if ip.packed.startswith(b"\x00\x64\xff\x9b\x00\x01" + b"\x00" * 6):
            return _is_blocked_ip(ipaddress.IPv4Address(ip.packed[-4:]))
        # ISATAP interface identifier (0000:5efe:<ipv4>) embeds an IPv4 address
        if ip.packed[8:12] == b"\x00\x00\x5e\xfe":
            return _is_blocked_ip(ipaddress.IPv4Address(ip.packed[-4:]))
        # Check IPv4-compatible IPv6 addresses (::/96 prefix, starting with 12 zero bytes)
        if ip.packed.startswith(b"\x00" * 12):
            return _is_blocked_ip(ipaddress.IPv4Address(ip.packed[-4:]))
        # Teredo (2001:0000::/32) is non-global (is_private=True via 2001::/23)
        # and the protocol is deprecated. Block the whole prefix outright:
        if ip.packed.startswith(b"\x20\x01\x00\x00"):
            return True
        # ORCHIDv2 (2001:20::/28) non-routable Overlay Routable Cryptographic Hash Identifiers
        if ip.packed.startswith(b"\x20\x01\x00") and (ip.packed[3] & 0xF0) == 0x20:
            return True
        # ORCHIDv1 (2001:10::/28, legacy RFC 4843 range) is non-routable too; block
        # it explicitly rather than relying on stdlib is_private classification
        if ip.packed.startswith(b"\x20\x01\x00") and (ip.packed[3] & 0xF0) == 0x10:
            return True
        # AMT (2001:3::/32, Automatic Multicast Tunneling, RFC 7450) non-routable range
        if ip.packed.startswith(b"\x20\x01\x00\x03"):
            return True
        # IETF Protocol Assignments (2001:1::/32, RFC 2928): CPython exempts the
        # globally reachable anycast addresses inside this block (PCP 2001:1::1,
        # TURN 2001:1::2) from the private 2001::/23 range, so block the whole /32
        if ip.packed.startswith(b"\x20\x01\x00\x01"):
            return True
        # AS112 IPv6 prefix (2001:4:112::/48, RFC 7534) non-routable sinkhole range
        if ip.packed.startswith(b"\x20\x01\x00\x04\x01\x12"):
            return True
    if isinstance(ip, ipaddress.IPv4Address):
        if ip.packed[0] == 0:
            return True
        # IETF Protocol Assignments IPv4 prefix (192.0.0.0/24, RFC 6890): CPython exempts
        # PCP (192.0.0.9) and TURN (192.0.0.10) anycast addresses from is_private=True,
        # so block the 192.0.0.0/24 range explicitly.
        if ip.packed[:3] == b"\xc0\x00\x00":
            return True
        # AMT IPv4 Anycast prefix (192.52.193.0/24, Automatic Multicast Tunneling, RFC 7450) non-routable range
        if ip.packed[:3] == b"\xc0\x34\xc1":
            return True
        # Deprecated 6to4 Anycast IPv4 prefix (192.88.99.0/24, RFC 7526)
        if ip.packed[:3] == b"\xc0\x58\x63":
            return True
        # AS112 IPv4 prefix (192.175.48.0/24, RFC 7534) non-routable sinkhole range
        if ip.packed[:3] == b"\xc0\xaf\x30":
            return True
        # AS112 Redirection IPv4 prefix (192.31.196.0/24, RFC 7535)
        if ip.packed[:3] == b"\xc0\x1f\xc4":
            return True
    return (
        not ip.is_global
        or ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or getattr(ip, "is_site_local", False)
        or ip.is_reserved
        or ip.is_unspecified
        or ip.is_multicast
    )


async def validate_url(url: str) -> str:
    """Validate and sanitize URL input"""
    if not url or not isinstance(url, str):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="URL is required and must be a string",
        )

    # Strip whitespace
    url = url.strip()

    # Check length
    if len(url) > 2048:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="URL is too long (maximum 2048 characters)",
        )

    # Validate URL format
    try:
        if not validators.url(url):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Invalid URL format",
            )
    except Exception as e:
        # validators.url() raises ValidationError for invalid URLs
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid URL format",
        ) from e

    # Parse URL to check scheme
    parsed = urlparse(url)
    if parsed.scheme not in ["http", "https"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Only HTTP and HTTPS URLs are allowed",
        )

    # Check for dangerous schemes
    dangerous_schemes = ["javascript", "data", "file", "vbscript"]
    if parsed.scheme in dangerous_schemes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Dangerous URL scheme not allowed",
        )

    # Additional validation for malformed URLs
    if not parsed.netloc or parsed.netloc == "":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid URL format - missing domain",
        )

    # Check for local and private network addresses (SSRF prevention)
    hostname = parsed.hostname
    if hostname:
        hostname_lower = hostname.lower()
        if hostname_lower == "localhost" or hostname_lower.endswith(".localhost"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Invalid URL: local or private network address not allowed",
            )
        try:
            # Check for alternative IPv4 address representations (dec, hex, octal, shorthand)
            try:
                packed = socket.inet_aton(hostname)
                ip = ipaddress.ip_address(packed)
            except Exception:
                ip = ipaddress.ip_address(hostname)

            if _is_blocked_ip(ip):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail="Invalid URL: local or private network address not allowed",
                )
        except ValueError:
            # Hostname is not an IP literal; resolve off the event loop and check
            # every resolved address (IPv4 and IPv6) against the blocked ranges.
            # Note: Validation-time DNS resolution prevents SSRF for client-side 301 redirects.
            # If a future feature ever fetches stored URLs (e.g., link previews), DNS resolution
            # must be repeated at fetch time to prevent DNS rebinding.
            try:
                loop = asyncio.get_running_loop()
                addr_info = await loop.getaddrinfo(hostname, None)
                for res in addr_info:
                    try:
                        ip = ipaddress.ip_address(res[4][0])
                        if _is_blocked_ip(ip):
                            raise HTTPException(
                                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                                detail="Invalid URL: local or private network address not allowed",
                            )
                    except ValueError:
                        pass
            except socket.gaierror:
                pass

    return url


def validate_admin_token(token: str) -> str:
    """Validate admin token"""
    if not token or len(token) < 16:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin token")

    # Check for allowed characters (alphanumeric + special)
    if not re.fullmatch(r"[a-zA-Z0-9!@#$%^&*()_\-+=]+", token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token format",
        )

    return token


def validate_short_link(link: str) -> str:
    """Validate short link format"""
    if not link or not re.fullmatch(r"[a-zA-Z0-9_-]{4,20}", link):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid short link format")
    return link


async def retry_phishtank_check(url: str, max_retries: int = 3) -> Optional[PhishTank]:
    """Check URL against PhishTank with retry logic"""
    from pydantic import HttpUrl

    try:
        http_url = HttpUrl(url)
        url_obj = Url(url=http_url)
    except Exception:
        return None

    for attempt in range(max_retries):
        try:
            phish = get_phish(url_obj)
            return phish
        except Exception as e:
            if attempt == max_retries - 1:
                # Log error and continue without phishing check
                logger.warning(
                    "PhishTank check failed after retries",
                    extra={
                        "max_retries": max_retries,
                        "error": str(e),
                        "url": str(url) if url else None,
                    },
                )
                return None
            # Exponential backoff
            await asyncio.sleep(2**attempt)
    return None


@db.on_connect(provider="sqlite")
def sqlite_litestream(db, connection):
    cursor = connection.cursor()
    cursor.execute("PRAGMA busy_timeout = 5000;")
    cursor.execute("PRAGMA synchronous = NORMAL;")
    cursor.execute("PRAGMA wal_autocheckpoint = 0;")


# Only bind database if not already bound
if not db.provider:
    db.bind(**ponyorm_settings[settings.db_type])
    db.generate_mapping(create_tables=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # Gracefully close active SSE connections on shutdown
    try:
        writers = list(sse_transport._read_stream_writers.values())
        for writer in writers:
            try:
                writer.close()
            except Exception:
                pass
    except Exception as e:
        logger.warning(
            "Error closing active SSE connections during shutdown",
            extra={"error": str(e)},
        )


app = FastAPI(
    title=settings.api_name,
    description="Simple API URL shortener that removes all the crap. Here you don't need an "
    "account or tokens to shorten a URL.",
    summary="Uncompromised URL shortener",
    version=VERSION_NUMBER,
    license_info={
        "name": "MIT",
        "identifier": "MIT",
    },
    redoc_url=None,
    openapi_tags=openapi_tags,
    lifespan=lifespan,
)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


def _handle_rate_limit_exceeded(request: Request, exc: Exception) -> responses.Response:
    """Adapt slowapi's handler to Starlette's ExceptionHandler signature.

    slowapi types the exception as RateLimitExceeded, which is not assignable
    to Starlette's ExceptionHandler (exc: Exception). ty rejects the direct
    registration.
    """
    if not isinstance(exc, RateLimitExceeded):
        raise exc
    return _rate_limit_exceeded_handler(request, exc)


# Add rate limiting middleware and exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _handle_rate_limit_exceeded)
app.add_middleware(SlowAPIMiddleware)


@limiter.shared_limit(settings.rate_limit_create, scope="/url")
async def count_url_create(request: Request) -> None:
    """Count one creation on the same per-client budget as POST /url.

    The scope matches that route's path key. Storage is the process-wide
    limiter, so every MCP connection for this client shares it.
    """
    del request


@limiter.shared_limit(settings.rate_limit_redirect, scope="resolve")
async def count_url_resolve(request: Request) -> None:
    """Count one resolution against RATE_LIMIT_REDIRECT for this client IP.

    One bucket per client for the process, not one bucket per MCP connection.
    """
    del request


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Middleware to add security headers to HTTP responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "frame-ancestors 'none'"
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    return response


BASE_PATH = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=f"{BASE_PATH}/templates")


@app.get("/", include_in_schema=False)
async def root() -> responses.RedirectResponse:
    redirect: responses.RedirectResponse
    if settings.site_url:
        redirect = responses.RedirectResponse(settings.site_url, status_code=status.HTTP_301_MOVED_PERMANENTLY)
    else:
        redirect = responses.RedirectResponse("/404")
    return redirect


@app.get("/health", tags=["system"])
async def health_check():
    """Check if the application and database are working properly"""
    try:
        if check_db_connection():
            return "OK"
    except Exception as e:
        raise HTTPException(status_code=503, detail="Service unavailable - Database connection failed") from e


@app.get("/metrics", tags=["system"], include_in_schema=False)
def metrics_endpoint():
    """Prometheus metrics endpoint"""
    if not settings.metrics_enabled:
        raise HTTPException(status_code=404, detail="Metrics not enabled")

    from l1nkzip.metrics import get_metrics_response

    response = get_metrics_response()
    return responses.Response(content=response, media_type="text/plain; charset=utf-8")


@app.get("/404", response_class=responses.HTMLResponse, include_in_schema=False)
async def not_found(request: Request):
    return templates.TemplateResponse(
        request,
        "404.html",
        {
            "homepage": settings.site_url,
            "api_name": settings.api_name,
        },
        status_code=404,
    )


@app.get("/phishtank/update/{token}", tags=["phishtank"])
async def update_phishtank(token: str, cleanup_days: int = 5) -> GenericInfo:
    """Webhook to update the PhishTank database. The database can clean X days older entries."""
    validate_admin_token(token)
    # Use constant-time comparison to prevent timing side-channel attacks
    if not secrets.compare_digest(token, settings.token):
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not (MIN_CLEANUP_DAYS <= cleanup_days <= MAX_CLEANUP_DAYS):
        raise HTTPException(
            status_code=422,
            detail=f"cleanup_days must be between {MIN_CLEANUP_DAYS} and {MAX_CLEANUP_DAYS}",
        )

    if not settings.phishtank:
        raise HTTPException(status_code=501, detail="PhishTank is not implemented")

    try:
        # Note: update_phishtanks is synchronous, not async
        await update_phishtanks()
        deleted_phishes = delete_old_phishes(days=cleanup_days)
        return GenericInfo(detail=f"PhishTank list updated. {deleted_phishes} entries have been deleted")
    except Exception as e:
        logger.error("PhishTank update error", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Failed to update PhishTank database") from e


@app.get("/list/{token}", tags=["urls"])
def get_list(token: str, limit: int = 100) -> List[LinkInfo]:
    """Get a list of all the URLs shortened by this API."""
    validate_admin_token(token)
    # Use constant-time comparison to prevent timing side-channel attacks
    if not secrets.compare_digest(token, settings.token):
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Validate limit parameter
    if limit < 1 or limit > 1000:
        raise HTTPException(status_code=422, detail="Limit must be between 1 and 1000")

    try:
        visits = get_visits(limit=limit)
        # Convert to proper types for LinkInfo
        from pydantic import HttpUrl

        return [
            LinkInfo(
                link=visit.link or "",
                full_link=HttpUrl(visit.full_link),
                url=HttpUrl(visit.url),
                visits=visit.visits,
            )
            for visit in visits
        ]
    except Exception as e:
        logger.error(
            "Database error in get_list",
            extra={"error": str(e), "limit": limit},
        )
        raise HTTPException(status_code=500, detail="Internal server error while retrieving URL list") from e


@app.get("/{link}", tags=["urls"])
@limiter.limit(settings.rate_limit_redirect)
async def get_url(request: Request, link: str) -> responses.RedirectResponse:
    """Redirect to the full URL. If the URL is a phishing URL, it will be redirected to the PhishTank page."""
    start_time = record_request_start("GET", "/{link}") if settings.metrics_enabled else None

    try:
        redirect: responses.RedirectResponse
        phish: Optional[PhishTank] = None

        # Validate short link format
        validate_short_link(link)

        # Check cache first if enabled
        cached_url = None
        if cache.is_enabled():
            try:
                cached_url = await cache.get(f"redirect:{link}")
                if settings.metrics_enabled and cached_url:
                    metrics.record_cache_operation("get", hit=True)
                elif settings.metrics_enabled:
                    metrics.record_cache_operation("get", hit=False)
            except Exception as e:
                logger.error("Cache error in get_url", extra={"error": str(e), "link": link})
                if settings.metrics_enabled:
                    metrics.record_cache_operation("get", success=False)

        if cached_url:
            # Cache hit - redirect immediately and update visit count asynchronously
            try:
                # Start async visit count update (fire and forget)
                import asyncio

                asyncio.create_task(increment_visit_async(link))
            except Exception as e:
                logger.error("Async visit count error", extra={"error": str(e), "link": link})

            # Check for phishing in cached URL
            if settings.phishtank:
                phish = await retry_phishtank_check(cached_url)

            if phish:
                if settings.metrics_enabled:
                    metrics.record_phishing_block()
                record_request_end("GET", "/{link}", 307, "get_url", start_time)
                redirect = responses.RedirectResponse(
                    str(phish.phish_detail_url) if phish and phish.phish_detail_url else "https://phishtank.org/",
                    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                )
            else:
                if settings.metrics_enabled:
                    metrics.record_redirect()
                record_request_end("GET", "/{link}", 301, "get_url", start_time)
                redirect = responses.RedirectResponse(cached_url, status_code=status.HTTP_301_MOVED_PERMANENTLY)
        else:
            # Cache miss - use database
            try:
                link_data = set_visit(link)
            except Exception as e:
                logger.error("Database error in get_url", extra={"error": str(e), "link": link})
                record_request_end("GET", "/{link}", 500, "get_url", start_time)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal server error: database failure",
                ) from e

            if settings.phishtank and link_data:
                phish = await retry_phishtank_check(str(link_data.url))

            if phish:
                if settings.metrics_enabled:
                    metrics.record_phishing_block()
                record_request_end("GET", "/{link}", 307, "get_url", start_time)
                redirect = responses.RedirectResponse(
                    str(phish.phish_detail_url) if phish and phish.phish_detail_url else "https://phishtank.org/",
                    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                )
            elif link_data:
                # Cache the successful lookup
                try:
                    await cache.set(f"redirect:{link}", str(link_data.url))
                    if settings.metrics_enabled:
                        metrics.record_cache_operation("set", success=True)
                except Exception as e:
                    logger.error("Cache set error", extra={"error": str(e), "link": link})
                    if settings.metrics_enabled:
                        metrics.record_cache_operation("set", success=False)

                if settings.metrics_enabled:
                    metrics.record_redirect()
                record_request_end("GET", "/{link}", 301, "get_url", start_time)
                redirect = responses.RedirectResponse(str(link_data.url), status_code=status.HTTP_301_MOVED_PERMANENTLY)
            else:
                record_request_end("GET", "/{link}", 404, "get_url", start_time)
                redirect = responses.RedirectResponse("/404")

        return redirect
    except Exception as e:
        logger.error("Unexpected error in get_url", extra={"error": str(e), "link": link})
        record_request_end("GET", "/{link}", 500, "get_url", start_time)
        return responses.RedirectResponse("/404")


@app.post("/url", tags=["urls"])
@limiter.limit(settings.rate_limit_create)
async def create_url(request: Request, url: Url) -> LinkInfo:
    """Create a short URL.
    If the URL is a phishing URL, it will be rejected.
    If the URL is already in the database, the information about it will be returned.
    """
    start_time = record_request_start("POST", "/url") if settings.metrics_enabled else None

    # Validate the URL
    try:
        validated_url = await validate_url(str(url.url))
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(
            "Validation error in create_url",
            extra={"error": str(e), "url": str(url.url) if url else None},
        )
        record_request_end("POST", "/url", 422, "create_url", start_time)
        raise HTTPException(status_code=422, detail="Invalid URL provided") from e

    # Check for phishing
    try:
        phish = await retry_phishtank_check(validated_url) if settings.phishtank else None
        if phish:
            if settings.metrics_enabled:
                metrics.record_phishing_block()
            record_request_end("POST", "/url", 403, "create_url", start_time)
            raise HTTPException(
                status_code=403,
                detail=f"Phishing URLs are Forbidden. More details about the URL: {phish.phish_detail_url or 'https://phishtank.org/'}",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Phishing check error in create_url",
            extra={"error": str(e), "url": validated_url},
        )
        record_request_end("POST", "/url", 500, "create_url", start_time)
        raise HTTPException(status_code=500, detail="Internal server error during phishing check") from e

    # Insert link
    try:
        link_data = insert_link(validated_url)

        if settings.metrics_enabled:
            metrics.record_url_created()

        record_request_end("POST", "/url", 201, "create_url", start_time)
        return LinkInfo(
            link=str(link_data.link) if link_data.link is not None else "",
            full_link=HttpUrl(link_data.full_link),
            url=HttpUrl(str(link_data.url)),
            visits=int(link_data.visits) if link_data.visits is not None and str(link_data.visits).isdigit() else 0,
        )
    except Exception as e:
        logger.error(
            "Database error in create_url",
            extra={"error": str(e), "url": validated_url},
        )
        record_request_end("POST", "/url", 500, "create_url", start_time)
        raise HTTPException(status_code=500, detail="Internal server error while creating URL") from e


def _require_mcp() -> None:
    if not settings.mcp_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MCP is disabled")


@app.get("/mcp/sse", tags=["mcp"])
async def handle_sse(request: Request) -> None:
    _require_mcp()
    # request._send is a private Starlette attribute. This is necessary because
    # MCP's connect_sse/handle_post_message require ASGI channels directly.
    # Tool handlers run on this task, so the rate limit sees this client.
    context = mcp_request.set(request)
    try:
        try:
            connect_ctx = sse_transport.connect_sse(
                request.scope,
                request.receive,
                request._send,
            )
        except Exception as e:
            logger.error(
                "Failed to initialize MCP SSE connection",
                extra={"error": str(e)},
            )
            raise HTTPException(status_code=400, detail="Failed to initialize SSE connection") from e

        try:
            async with connect_ctx as streams:
                await mcp_server.run(
                    streams[0],
                    streams[1],
                    mcp_server.create_initialization_options(),
                )
        except asyncio.CancelledError:
            logger.info("MCP SSE client connection cancelled/disconnected gracefully")
        except Exception as e:
            err_msg = str(e).lower()
            is_disconnect = any(
                p in err_msg
                for p in (
                    "broken pipe",
                    "connection reset",
                    "connection closed",
                    "closed",
                    "cancelled",
                    "client disconnected",
                )
            ) or isinstance(e, (ConnectionResetError, BrokenPipeError))

            if is_disconnect:
                logger.info(
                    "MCP SSE client connection disconnected abruptly",
                    extra={"error": str(e)},
                )
            else:
                logger.error(
                    "Unexpected error in MCP SSE connection",
                    extra={"error": str(e)},
                )
    finally:
        mcp_request.reset(context)


@app.post("/mcp/messages", tags=["mcp"])
async def handle_messages(request: Request) -> None:
    _require_mcp()
    # request._send is a private Starlette attribute. This is necessary because
    # MCP's connect_sse/handle_post_message require ASGI channels directly.
    context = mcp_request.set(request)
    try:
        try:
            await sse_transport.handle_post_message(
                request.scope,
                request.receive,
                request._send,
            )
        except Exception as e:
            logger.error(
                "Error handling MCP message POST request",
                extra={"error": str(e)},
            )
            raise HTTPException(status_code=500, detail="Internal server error in message route") from e
    finally:
        mcp_request.reset(context)
