"""Utility helpers for coursework project."""

from __future__ import annotations

import random
import requests  # Added missing import
from datetime import datetime, time
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from .logger import logger
import os
from dotenv import load_dotenv

load_dotenv()

DATA_COL_DATE = "Дата операции"
DATA_COL_CARD = "Номер карты"
DATA_COL_PAYMENT = "Сумма платежа"
DATA_COL_CASHBACK = "Кэшбэк"
DATA_COL_CATEGORY = "Категория"
DATA_COL_DESCRIPTION = "Описание"

GREETINGS = {
    "morning": "Доброе утро",
    "day": "Добрый день",
    "evening": "Добрый вечер",
    "night": "Доброй ночи",
}


def _get_part_of_day(now: time) -> str:
    if time(6, 0) <= now < time(12, 0):
        return GREETINGS["morning"]
    if time(12, 0) <= now < time(18, 0):
        return GREETINGS["day"]
    if time(18, 0) <= now < time(23, 0):
        return GREETINGS["evening"]
    return GREETINGS["night"]


# ------------------------------------------------------------
# Public helpers
# ------------------------------------------------------------


def send_greeting(date_time: datetime | None = None) -> str:
    """Return greeting phrase depending on *date_time*."""
    date_time = date_time or datetime.now()
    greeting = _get_part_of_day(date_time.time())
    logger.debug("Greeting generated: %s", greeting)
    return greeting


def read_transactions(xlsx_path: str | Path) -> pd.DataFrame:
    """Read Excel file with bank transactions into *pandas* DataFrame."""
    df = pd.read_excel(xlsx_path)
    logger.info("Loaded %s transactions from %s", len(df), xlsx_path)
    return df


def card_info(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Aggregate total spent & cashback for every card."""
    summaries = []
    for last_digits, group in df.groupby(DATA_COL_CARD):
        total = float(group[DATA_COL_PAYMENT].sum())
        cashback = float(group[DATA_COL_CASHBACK].sum())
        summaries.append(
            {
                "last_digits": str(last_digits),
                "total_spent": round(total, 2),
                "cashback": round(cashback, 2),
            }
        )
    logger.debug("Card info calculated: %s", summaries)
    return summaries


def top_transactions(df: pd.DataFrame, limit: int = 5) -> List[Dict[str, Any]]:
    df_sorted = df.reindex(df[DATA_COL_PAYMENT].abs().sort_values(ascending=False).index).head(limit)
    res = df_sorted[[DATA_COL_DATE, DATA_COL_PAYMENT, DATA_COL_CATEGORY, DATA_COL_DESCRIPTION]].to_dict(
        orient="records"
    )
    logger.debug("Top %d transactions: %s", limit, res)
    return res


# ---------------- External data (stubs) ----------------------


def _dummy_price() -> float:
    return round(random.uniform(50, 500), 2)


def get_currency_rates(currencies: List[str], base_currency: str = 'USD') -> List[Dict[str, Any]]:
    """Return list of dicts with real currency rates from an API."""
    try:
        # Example using ExchangeRate-API (you'll need an API key)
        api_key = os.getenv("API_KEY")
        url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{base_currency}"

        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        rates = []
        for currency in currencies:
            if currency in data['conversion_rates']:
                rates.append({
                    "currency": currency,
                    "rate": data['conversion_rates'][currency],
                    "base": base_currency
                })

        logger.info("Real currency rates fetched for %s", currencies)
        return rates

    except Exception as e:
        logger.error("Failed to fetch currency rates: %s", str(e))
        # Fallback to dummy data or raise
        return [{"currency": cur, "rate": 1.0} for cur in currencies]


def get_stock_prices(stocks: List[str]) -> List[Dict[str, Any]]:
    """Return list of dicts with real stock prices from an API."""
    try:
        # Example using Alpha Vantage (you'll need an API key)
        api_key = os.getenv("API_KEY_ALPHA")
        prices = []

        for stock in stocks:
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={stock}&apikey={api_key}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            if 'Global Quote' in data:
                prices.append({
                    "stock": stock,
                    "price": float(data['Global Quote']['05. price']),
                    "currency": "USD",  # Assuming USD, adjust if needed
                    "change": data['Global Quote']['09. change']
                })

        logger.info("Real stock prices fetched for %s", stocks)
        return prices

    except Exception as e:
        logger.error("Failed to fetch stock prices: %s", str(e))
        # Fallback to dummy data or raise
        return [{"stock": st, "price": 100.0} for st in stocks]


def format_money(amount: float, currency: str = "USD") -> str:
    return f"{amount:,.2f} {currency}"
