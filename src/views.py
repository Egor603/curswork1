from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from .logger import logger
from .utils import card_info, get_currency_rates, get_stock_prices, read_transactions, send_greeting, top_transactions

USER_SETTINGS_FILE = Path(__file__).resolve().parent.parent / "user_settings.json"
DEFAULT_SETTINGS = {"user_currencies": ["USD", "EUR"], "user_stocks": ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]}


def _load_settings() -> Dict[str, Any]:
    if USER_SETTINGS_FILE.exists():
        return json.loads(USER_SETTINGS_FILE.read_text(encoding="utf-8"))
    return DEFAULT_SETTINGS


def index(date_time_str: str, xlsx_path: str | Path = None) -> str:
    """Return JSON string for *Главная* page."""
    date_time = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")
    settings = _load_settings()

    # Prepare data
    df = read_transactions(xlsx_path or Path(__file__).resolve().parent.parent / "data" / "operations.xlsx")

    response: Dict[str, Any] = {
        "greeting": send_greeting(date_time),
        "cards": card_info(df),
        "top_transactions": top_transactions(df),
        "currency_rates": get_currency_rates(settings["user_currencies"]),
        "stock_prices": get_stock_prices(settings["user_stocks"]),
    }

    logger.info("Index page JSON generated.")
    return json.dumps(response, ensure_ascii=False, indent=2)
