from datetime import timedelta
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
import httpx

from l1nkzip.config import settings
from l1nkzip.models import PhishTank, Url, db_session, utcnow_zone_aware


def build_phishtank_url() -> str:
    """Build PhishTank API URL based on configuration"""
    base_url = "http://data.phishtank.com/data"
    if isinstance(settings.phishtank, str) and settings.phishtank != "anonymous":
        return f"{base_url}/{settings.phishtank}/online-valid.json"
    return f"{base_url}/online-valid.json"


async def fetch_phishtank_data(client: httpx.AsyncClient, url: str) -> List[Dict[str, Any]]:
    """Fetch PhishTank data from API"""
    response = await client.get(
        url,
        headers={
            "User-Agent": f"phishtank/{settings.api_name}",
            "accept-encoding": "gzip",
        },
        follow_redirects=True,
    )
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@db_session
def process_phishtank_items(items: List[Dict[str, Any]]) -> None:
    """Process and store PhishTank items in database"""
    for item in items:
        phishtank = PhishTank.get(id=item["phish_id"])
        if phishtank:
            phishtank.updated_at = utcnow_zone_aware()
        else:
            PhishTank(
                id=item["phish_id"],
                url=item["url"],
                phish_detail_url=item["phish_detail_url"],
            )


async def update_phishtanks(client: Optional[httpx.AsyncClient] = None) -> None:
    """Update PhishTank database from online source"""
    url = build_phishtank_url()

    # Use provided client or create new one
    async def fetch_and_process(client_obj):
        items = await fetch_phishtank_data(client_obj, url)
        process_phishtank_items(items)

    if client is None:
        async with httpx.AsyncClient() as new_client:
            await fetch_and_process(new_client)
    else:
        await fetch_and_process(client)


@db_session
def get_phish(url_info: Url) -> PhishTank | None:
    return PhishTank.get(url=str(url_info.url))


@db_session
def delete_old_phishes(days: int) -> int:
    phishes = PhishTank.select(lambda p: p.updated_at < utcnow_zone_aware() - timedelta(days=days))
    delete_count = phishes.count()
    phishes.delete(bulk=True)
    return delete_count
