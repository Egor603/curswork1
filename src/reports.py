from __future__ import annotations

import json
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import pandas as pd

from .logger import logger
from .services import convert

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


def _default_filename(func_name: str) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return REPORTS_DIR / f"{func_name}_{ts}.json"


def save_report(
    filename: str | None = None,
) -> Callable[[Callable[..., Dict[str, Any]]], Callable[..., Dict[str, Any]]]:
    def decorator(
            func: Callable[..., Dict[str, Any]]
    ) -> Callable[..., Dict[str, Any]]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Dict[str, Any]:
            result = func(*args, **kwargs)
            out_path = (
                Path(filename)
                if filename
                else _default_filename(func.__name__)
            )
            out_path.write_text(
                json.dumps(result, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            logger.info("Report saved to %s", out_path)
            return result

        return wrapper

    return decorator


@save_report()
def spend_by_category(
    data: Union[pd.DataFrame, List[Dict]],
    category: Optional[str] = None,
    date_str: Optional[str] = None,
    base_currency: str = "USD"
) -> Dict[str, Any]:
    """
    Универсальная функция для анализа расходов по категориям.

    Параметры:
    - data: входные данные (DataFrame или список словарей)
    - category: опциональная категория для фильтрации
    - date_str: опциональная дата окончания периода (формат 'YYYY-MM-DD')
    - base_currency: валюта для конвертации (по умолчанию 'USD')

    Возвращает:
    - Словарь с результатами анализа
    """
    result: Dict[str, Any] = {}

    # Обработка DataFrame
    if isinstance(data, pd.DataFrame):
        df = data.copy()

        # Преобразование дат
        df['Дата операции'] = pd.to_datetime(df['Дата операции'])

        # Фильтрация по дате
        if date_str:
            end_date = pd.to_datetime(date_str)
            start_date = end_date - timedelta(days=90)
            df = df[(df['Дата операции'] >= start_date)
                    & (df['Дата операции'] <= end_date)]
            result.update({
                "date_from": start_date.strftime("%Y-%m-%d"),
                "date_to": end_date.strftime("%Y-%m-%d")
            })

        # Фильтрация по категории
        if category:
            df = df[df['Категория'] == category]

        # Суммирование
        if category:
            total = float(df['Сумма платежа'].sum())
            result.update({
                "category": category,
                "total_spent": round(total, 2)
            })
        else:
            summary = df.groupby('Категория')['Сумма платежа'].sum().to_dict()
            result["by_category"] = {
                k: round(float(v), 2) for k, v in summary.items()
            }

    # Обработка списка словарей
    elif isinstance(data, list):
        summary: Dict[str, float] = {}
        for tx in data:
            amount = convert(
                tx.get("amount", 0),
                tx.get("currency", "USD"),
                base_currency
            )
            summary[tx.get("category", "Other")] = (
                summary.get(tx.get("category", "Other"), 0) + amount
            )

        if category:
            result = {
                "category": category,
                "total_spent": round(summary.get(category, 0), 2),
                "currency": base_currency
            }
        else:
            result = {
                "by_category": {k: round(v, 2) for k, v in summary.items()},
                "currency": base_currency
            }

    logger.debug("Spend by category result: %s", result)
    return result
