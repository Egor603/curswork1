from __future__ import annotations

import json
import math
import os
import re
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv

from src.logger import logger

# ---------------- Общие ----------------


def _jsonify(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


# ---------------- Простой поиск ----------------


def services_page() -> Dict:
    """Страница сервисов"""
    return {
        'message': 'Сервисы банка',
        'services': ['Переводы', 'Платежи', 'Шаблоны']
    }


def simple_search(query: str, transactions: List[Dict[str, Any]]) -> str:
    """Return transactions whose *query* substring appears in description or
    category."""
    q = query.lower()
    filtered = [
        t for t in transactions
        if q in str(t.get("Описание", "")).lower()
        or q in str(t.get("Категория", "")).lower()
    ]
    logger.info("Simple search for '%s': %d results", query, len(filtered))
    return _jsonify(filtered)


# ---------------- Инвесткопилка ----------------


def investment_bank(
    month: str,
    transactions: List[Dict[str, Any]],
    limit: int
) -> float:
    """Return rounded savings for *month* and *limit* (10, 50, 100)."""
    try:
        period = datetime.strptime(month, "%Y-%m")
    except ValueError as exc:
        raise ValueError("month must be in 'YYYY-MM' format") from exc

    if limit not in (10, 50, 100):
        raise ValueError("limit must be 10, 50 or 100")

    total_saved = 0.0
    for t in transactions:
        op_date = datetime.strptime(str(t["Дата операции"]), "%Y-%m-%d")
        if op_date.year == period.year and op_date.month == period.month:
            amount = float(t["Сумма операции"])
            rounded = math.ceil(amount / limit) * limit
            total_saved += rounded - amount
    logger.info("Investment bank calculated: %.2f", total_saved)
    return round(total_saved, 2)


# ---------------- Поиск по телефону ----------------


PHONE_RE = re.compile(r"(\+7\s?\d{3}\s?\d{3}[-\s]?\d{2}[-\s]?\d{2})")


def phone_search(transactions: List[Dict[str, Any]]) -> str:
    matched = [
        t for t in transactions
        if PHONE_RE.search(str(t.get("Описание", "")))
    ]
    logger.info("Phone search: %d matches", len(matched))
    return _jsonify(matched)


# ---------------- Поиск переводов физлицам ----------------


PERSON_RE = re.compile(r"^[А-ЯЁ][а-яё]+\s[А-ЯЁ]\.?$")


def people_transfer_search(transactions: List[Dict[str, Any]]) -> str:
    matched = [
        t
        for t in transactions
        if t.get("Категория") == "Переводы"
        and PERSON_RE.search(str(t.get("Описание", "")).strip())
    ]
    logger.info("People transfer search: %d matches", len(matched))
    return _jsonify(matched)


load_dotenv()  # подхватываем .env

API_KEY = os.getenv("API_KEY")
# docs ➜ [currencyapi.com](https://currencyapi.com/docs/latest)
API_URL = "https://api.currencyapi.com/v3/latest"


class CurrencyServiceError(RuntimeError):
    """Чет-то пошло не так при обращении к API."""


@lru_cache(maxsize=1)  # кэшируем на время life-run тестов
def get_rates(base: str = "USD") -> Dict[str, float]:
    """Возвращает словарь {'RUB': 94.1, 'EUR': 0.92, …} для указанной
    base-валюты.
    """
    resp = requests.get(
        API_URL,
        params={"base_currency": base},
        headers={"apikey": API_KEY},
        timeout=10,
    )
    try:
        resp.raise_for_status()
        data = resp.json()["data"]
    except (ValueError, KeyError) as exc:
        raise CurrencyServiceError("Некорректный ответ currencyapi") from exc

    return {code: float(info["value"]) for code, info in data.items()}


def convert(amount: float, from_curr: str, to_curr: str = "USD") -> float:
    """Конвертирует сумму через свежие курсы. При необходимости кэш обновляется."""
    rates = get_rates(base=to_curr.upper())
    rate = rates.get(from_curr.upper())
    if rate is None:
        raise CurrencyServiceError(
            f"Нет курса для {from_curr}"
        )
    return amount / rate


def suggest_products(transactions: List[Dict[str, Any]]) -> str:
    """Анализирует транзакции пользователя и предлагает подходящие финансовые
    продукты.
    """
    # Анализ транзакций
    total_spent = sum(abs(float(t["Сумма операции"])) for t in transactions)
    avg_monthly_spend = total_spent / 3  # предполагаем 3 месяца истории
    categories = set(t.get("Категория", "") for t in transactions)

    # Определение потенциальных продуктов
    products = []

    # Кредитная карта
    if avg_monthly_spend > 30000:
        products.append({
            "name": "Кредитная карта с кэшбэком",
            "description": "До 10% кэшбэка на основные категории",
            "reason": "Ваши ежемесячные расходы позволяют максимизировать "
                      "выгоду от кэшбэка"
        })

    # Инвестиционный счет
    if "Переводы" in categories and avg_monthly_spend > 50000:
        products.append({
            "name": "Инвестиционный счёт",
            "description": "Доходность до 8% годовых с возможностью "
                           "частичного снятия",
            "reason": "У вас есть свободные средства для инвестирования"
        })

    # Накопительный счет
    if len(products) == 0 and avg_monthly_spend > 20000:
        products.append({
            "name": "Накопительный счёт",
            "description": "3.5% годовых на остаток",
            "reason": "Позволит сохранить и приумножить ваши сбережения"
        })

    # Дебетовая карта с кэшбэком (базовое предложение)
    if len(products) == 0:
        products.append({
            "name": "Дебетовая карта с кэшбэком 1%",
            "description": "1% кэшбэка на все покупки",
            "reason": "Базовое предложение для всех клиентов"
        })

    logger.info(
        "Suggested %d products based on transaction history",
        len(products)
    )
    return _jsonify({
        "analysis": {
            "avg_monthly_spend": round(avg_monthly_spend, 2),
            "main_categories": list(categories)
        },
        "suggested_products": products
    })
