from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_name: str = "l1nkZip"
    api_domain: str = "https://l1nk.zip"
    site_domain: str = "https://dorogoy.github.io/l1nkZip/"
    sqlite_db: str = "l1nkzip.sqlite"
    token: str = "__change_me__"
    # Change this to your own random generator string
    generator_string: str = "mn6j2c4rv8bpygw95z7hsdaetxuk3fq"


settings = Settings()

fastapi_settings = {
    "title": "l1nkZip",
    "description": "Simple API URL shortener that removes all the crap. Here you don't need an account or tokens to shorten a URL.",
    "summary": "Uncompromised URL shortener",
    "version": "0.1.5",
    "license_info": {
        "name": "MIT",
        "identifier": "MIT",
    },
    "redoc_url": None,
    "openapi_tags": [
        {
            "name": "urls",
            "description": "Operations with URLs management. The **URL** parameter is the URL to be shortened.",
        },
        {
            "name": "phishtank",
            "description": "Operations with PhishTank management. The **token** parameter is the secret token from the configuration to allow the update of the PhishTank database.",
        },
    ],
}
