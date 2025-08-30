from pathlib import Path
from typing import List

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
    if token != settings.token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    else:
        if not settings.phishtank:
            raise HTTPException(status_code=501, detail="PhishTank is not implemented")
        await update_phishtanks()
        deleted_phishes = delete_old_phishes(days=cleanup_days)
        return GenericInfo(
            detail=f"PhishTank list updated. {deleted_phishes} entries have been deleted"
        )


@app.get("/list/{token}", tags=["urls"])
def get_list(token: str, limit: int = 100) -> List[LinkInfo]:
    """Get a list of all the URLs shortened by this API."""
    if token != settings.token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    else:
        return get_visits(limit=limit)


@app.get("/{link}", tags=["urls"])
@limiter.limit(settings.rate_limit_redirect)
def get_url(request: Request, link: str) -> responses.RedirectResponse:
    """Redirect to the full URL. If the URL is a phishing URL, it will be redirected to the PhishTank page."""
    redirect: responses.RedirectResponse
    phish = False
    link_data = set_visit(link)

    if settings.phishtank and link_data:
        phish = get_phish(Url(url=link_data.url))

    if isinstance(phish, PhishTank):
        redirect = responses.RedirectResponse(
            phish.phish_detail_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT
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
    phish = get_phish(url) if settings.phishtank else None
    if phish:
        raise HTTPException(
            status_code=403,
            detail=f"Phishing URLs are Forbidden. More details about the URL: {phish.phish_detail_url}",
        )
    link_data = insert_link(str(url.url))
    return LinkInfo(
        link=link_data.link,
        full_link=link_data.full_link,
        url=link_data.url,
        visits=link_data.visits,
    )
