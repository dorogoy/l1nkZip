import re
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

import validators
from fastapi import FastAPI, HTTPException, Request, responses, status
from fastapi.templating import Jinja2Templates
from slowapi.extension import Limiter
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from l1nkzip.config import openapi_tags, ponyorm_settings, settings
from l1nkzip.models import (
    GenericInfo,
    LinkInfo,
    Url,
    check_db_connection,
    db,
    get_visits,
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


# Validation helper functions
def validate_url(url: str) -> str:
    """Validate and sanitize URL input"""
    if not url or not isinstance(url, str):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="URL is required and must be a string",
        )

    # Strip whitespace
    url = url.strip()

    # Check length
    if len(url) > 2048:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="URL is too long (maximum 2048 characters)",
        )

    # Validate URL format
    try:
        if not validators.url(url):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid URL format",
            )
    except Exception:
        # validators.url() raises ValidationError for invalid URLs
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid URL format",
        )

    # Parse URL to check scheme
    parsed = urlparse(url)
    if parsed.scheme not in ["http", "https"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only HTTP and HTTPS URLs are allowed",
        )

    # Check for dangerous schemes
    dangerous_schemes = ["javascript", "data", "file", "vbscript"]
    if parsed.scheme in dangerous_schemes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Dangerous URL scheme not allowed",
        )

    # Additional validation for malformed URLs
    if not parsed.netloc or parsed.netloc == "":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid URL format - missing domain",
        )

    return url


def validate_admin_token(token: str) -> str:
    """Validate admin token"""
    if not token or len(token) < 16:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin token"
        )

    # Check for allowed characters (alphanumeric + special)
    if not re.match(r"^[a-zA-Z0-9!@#$%^&*()_+-=]+$", token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token format",
        )

    return token


def validate_short_link(link: str) -> str:
    """Validate short link format"""
    if not link or not re.match(r"^[a-zA-Z0-9_-]{4,20}$", link):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid short link format"
        )
    return link


def retry_phishtank_check(url: str, max_retries: int = 3) -> Optional[PhishTank]:
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
                print(f"PhishTank check failed after {max_retries} attempts: {e}")
                return None
            # Exponential backoff
            import time

            time.sleep(2**attempt)
    return None


@db.on_connect(provider="sqlite")
def sqlite_litestream(db, connection):
    cursor = connection.cursor()
    cursor.execute("PRAGMA busy_timeout = 5000;")
    cursor.execute("PRAGMA synchronous = NORMAL;")
    cursor.execute("PRAGMA wal_autocheckpoint = 0;")


db.bind(**ponyorm_settings[settings.db_type])
db.generate_mapping(create_tables=True)


app = FastAPI(
    title=settings.api_name,
    description="Simple API URL shortener that removes all the crap. Here you don't need an account or tokens to shorten a URL.",
    summary="Uncompromised URL shortener",
    version=VERSION_NUMBER,
    license_info={
        "name": "MIT",
        "identifier": "MIT",
    },
    redoc_url=None,
    openapi_tags=openapi_tags,
)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Add rate limiting middleware
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

BASE_PATH = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=f"{BASE_PATH}/templates")


@app.get("/", include_in_schema=False)
async def root() -> responses.RedirectResponse:
    redirect: responses.RedirectResponse
    if settings.site_url:
        redirect = responses.RedirectResponse(
            settings.site_url, status_code=status.HTTP_301_MOVED_PERMANENTLY
        )
    else:
        redirect = responses.RedirectResponse("/404")
    return redirect


@app.get("/health", tags=["system"])
async def health_check():
    """Check if the application and database are working properly"""
    try:
        if check_db_connection():
            return "OK"
    except Exception:
        raise HTTPException(
            status_code=503, detail="Service unavailable - Database connection failed"
        )


@app.get("/404", response_class=responses.HTMLResponse, include_in_schema=False)
async def not_found(request: Request):
    return templates.TemplateResponse(
        "404.html",
        {
            "request": request,
            "homepage": settings.site_url,
            "api_name": settings.api_name,
        },
        status_code=404,
    )


@app.get("/phishtank/update/{token}", tags=["phishtank"])
async def update_phishtank(token: str, cleanup_days: int = 5) -> GenericInfo:
    """Webhook to update the PhishTank database. The database can clean X days older entries."""
    validate_admin_token(token)
    if token != settings.token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not settings.phishtank:
        raise HTTPException(status_code=501, detail="PhishTank is not implemented")

    try:
        # Note: update_phishtanks is synchronous, not async
        await update_phishtanks()
        deleted_phishes = delete_old_phishes(days=cleanup_days)
        return GenericInfo(
            detail=f"PhishTank list updated. {deleted_phishes} entries have been deleted"
        )
    except Exception as e:
        print(f"PhishTank update error: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to update PhishTank database"
        )


@app.get("/list/{token}", tags=["urls"])
def get_list(token: str, limit: int = 100) -> List[LinkInfo]:
    """Get a list of all the URLs shortened by this API."""
    validate_admin_token(token)
    if token != settings.token:
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
        print(f"Database error in get_list: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error while retrieving URL list"
        )


@app.get("/{link}", tags=["urls"])
@limiter.limit(settings.rate_limit_redirect)
def get_url(request: Request, link: str) -> responses.RedirectResponse:
    """Redirect to the full URL. If the URL is a phishing URL, it will be redirected to the PhishTank page."""
    redirect: responses.RedirectResponse
    phish: Optional[PhishTank] = None

    # Validate short link format
    validate_short_link(link)

    try:
        link_data = set_visit(link)
    except Exception as e:
        print(f"Database error in get_url: {e}")
        return responses.RedirectResponse("/404")

    if settings.phishtank and link_data:
        phish = retry_phishtank_check(link_data.url)

    if phish:
        redirect = responses.RedirectResponse(
            phish.phish_detail_url or "https://phishtank.org/",
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )
    elif link_data:
        redirect = responses.RedirectResponse(
            link_data.url, status_code=status.HTTP_301_MOVED_PERMANENTLY
        )
    else:
        redirect = responses.RedirectResponse("/404")

    return redirect


@app.post("/url", tags=["urls"])
@limiter.limit(settings.rate_limit_create)
def create_url(request: Request, url: Url) -> LinkInfo:
    """Create a short URL.
    If the URL is a phishing URL, it will be rejected.
    If the URL is already in the database, the information about it will be returned.
    """
    # Validate the URL
    validated_url = validate_url(str(url.url))

    # Check for phishing
    phish = retry_phishtank_check(validated_url) if settings.phishtank else None
    if phish:
        raise HTTPException(
            status_code=403,
            detail=f"Phishing URLs are Forbidden. More details about the URL: {phish.phish_detail_url or 'https://phishtank.org/'}",
        )

    try:
        link_data = insert_link(validated_url)
        from pydantic import HttpUrl

        return LinkInfo(
            link=link_data.link or "",
            full_link=HttpUrl(link_data.full_link),
            url=HttpUrl(link_data.url),
            visits=link_data.visits,
        )
    except Exception as e:
        print(f"Database error in create_url: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error while creating URL"
        )
