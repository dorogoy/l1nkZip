from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, responses, status
from fastapi.templating import Jinja2Templates

from l1nkzip.config import fastapi_settings, settings
from l1nkzip.models import GenericInfo, LinkInfo, Url, db, insert_link, set_visit
from l1nkzip.phishtank import delete_old_phishes, get_phish, update_phishtanks


@db.on_connect(provider="sqlite")
def sqlite_litestream(db, connection):
    cursor = connection.cursor()
    cursor.execute("PRAGMA busy_timeout = 5000;")
    cursor.execute("PRAGMA synchronous = NORMAL;")
    cursor.execute("PRAGMA wal_autocheckpoint = 0;")


db.bind(provider="sqlite", filename=settings.sqlite_db, create_db=True)
db.generate_mapping(create_tables=True)


app = FastAPI(**fastapi_settings)

BASE_PATH = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=f"{BASE_PATH}/templates")


@app.get("/", include_in_schema=False)
async def root() -> responses.RedirectResponse:
    return responses.RedirectResponse(
        settings.site_domain, status_code=status.HTTP_301_MOVED_PERMANENTLY
    )


@app.get("/404", response_class=responses.HTMLResponse, include_in_schema=False)
async def not_found(request: Request):
    return templates.TemplateResponse(
        "404.html",
        {
            "request": request,
            "homepage": settings.site_domain,
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
        await update_phishtanks()
        deleted_phishes = delete_old_phishes(days=cleanup_days)
        return GenericInfo(
            detail=f"PhishTank list updated. {deleted_phishes} entries have been deleted"
        )


@app.get("/{link}", tags=["urls"])
def get_url(link: str) -> responses.RedirectResponse:
    """Redirect to the full URL. If the URL is a phishing URL, it will be redirected to the PhishTank page."""
    redirect: responses.RedirectResponse
    link_data = set_visit(link)
    phish = get_phish(Url(url=link_data.url)) if link_data else False

    if phish:
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
def create_url(url: Url) -> LinkInfo:
    """Create a short URL.
    If the URL is a phishing URL, it will be rejected.
    If the URL is already in the database, the information about it will be returned.
    """
    phish = get_phish(url)
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
