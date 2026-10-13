from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class TravelSite:
    name: str
    url: str


@dataclass(frozen=True)
class Settings:
    bot_token: str
    openai_api_key: str | None
    openai_model: str
    database_path: Path
    start_image_path: Path
    travel_sites: tuple[TravelSite, ...]


def get_settings() -> Settings:
    database_path = Path(os.getenv("DATABASE_PATH", str(BASE_DIR / "loveis.sqlite3")))

    return Settings(
        bot_token=os.getenv("BOT_TOKEN", "").strip(),
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip() or None,
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip(),
        database_path=database_path,
        start_image_path=BASE_DIR / "assets" / "start.jpg",
        travel_sites=(
            TravelSite("Aviasales", "https://www.aviasales.ru/"),
            TravelSite("OneTwoTrip", "https://www.onetwotrip.com/"),
            TravelSite("Tutu", "https://www.tutu.ru/"),
            TravelSite("Яндекс Путешествия", "https://travel.yandex.ru/"),
            TravelSite("Google Travel", "https://www.google.com/travel/"),
            TravelSite("Booking", "https://www.booking.com/"),
            TravelSite("Ostrovok", "https://ostrovok.ru/"),
        ),
    )

