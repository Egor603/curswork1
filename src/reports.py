from __future__ import annotations

import json
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict

import pandas as pd

from .logger import logger

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


def _default_filename(func_name: str) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return REPORTS_DIR / f"{func_name}_{ts}.json"


def save_report(
    filename: str | None = None,
) -> Callable[[Callable[..., Dict[str, Any]]], Callable[..., Dict[str, Any]]]:

    def decorator(func: Callable[..., Dict[str, Any]]) -> Callable[..., Dict[str, Any]]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Dict[str, Any]:
            result = func(*args, **kwargs)
            out_path = Path(filename) if filename else _default_filename(func.__name__)
            out_path.write_text(
                json.dumps(result, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            logger.info("Report saved to %s", out_path)
            return result

        return wrapper

    return decorator


# ----------------------------------------------------------------------
# Отчёт &laquo;Траты по категории&raquo;
# ----------------------------------------------------------------------

@save_report()
def spend_by_category(
    df: pd.DataFrame,
    category: str,
    date_str: str | None = None,
) -> Dict[str, Any]:

    # определяем границы периода (последние 90 дней)
    end_date = (
        datetime.strptime(date_str, "%Y-%m-%d")
        if date_str
        else datetime.now()
    )
    start_date = end_date - timedelta(days=90)

    # приводим колонку &laquo;Дата операции&raquo; к строке YYYY‑MM‑DD, если нужно
    if not pd.api.types.is_string_dtype(df["Дата операции"]):
        df = df.assign(
            **{"Дата операции": df["Дата операции"].dt.strftime("%Y-%m-%d")}
        )

    # фильтрация по дате и категории
    mask = (
        (df["Дата операции"] >= start_date.strftime("%Y-%m-%d"))
        & (df["Дата операции"] <= end_date.strftime("%Y-%m-%d"))
        & (df["Категория"] == category)
    )

    total = float(df.loc[mask, "Сумма платежа"].sum())

    result = {
        "category": category,
        "total_spent": round(total, 2),
        "date_from": start_date.strftime("%Y-%m-%d"),
        "date_to": end_date.strftime("%Y-%m-%d"),
    }
    logger.debug("Spend by category result: %s", result)
    return result
