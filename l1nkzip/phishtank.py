from datetime import timedelta

import httpx
from fastapi import HTTPException

from l1nkzip.config import settings
from l1nkzip.models import PhishTank, Url, db_session, utcnow_zone_aware


async def update_phishtanks():
    phishtank_url = "http://data.phishtank.com/data"
    if isinstance(settings.phishtank, str) and settings.phishtank != "anonymous":
        phishtank_url = f"{phishtank_url}/{settings.phishtank}"
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{phishtank_url}/online-valid.json",
            headers={"User-Agent": f"phishtank/{settings.api_name}", "accept-encoding": "gzip"},
            follow_redirects=True,
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        else:
            with db_session:
                for item in response.json():
                    phishtank = PhishTank.get(id=item["phish_id"])
                    if phishtank:
                        phishtank.updated_at = utcnow_zone_aware()
                    else:
                        PhishTank(
                            id=item["phish_id"],
                            url=item["url"],
                            phish_detail_url=item["phish_detail_url"],
                        )


@db_session
def get_phish(url_info: Url) -> PhishTank:
    return PhishTank.get(url=str(url_info.url))


@db_session
def delete_old_phishes(days: int) -> int:
    phishes = PhishTank.select(
        lambda p: p.updated_at < utcnow_zone_aware() - timedelta(days=days)
    )
    delete_count = phishes.count()
    phishes.delete(bulk=True)
    return delete_count
