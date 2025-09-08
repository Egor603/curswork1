import argparse
from pathlib import Path
import pandas as pd

from src.services import suggest_products
from src.views import index
from src.reports import spend_by_category


def main() -> None:
    """Основная функция для вызова всех функций приложения"""
    parser = argparse.ArgumentParser(description="Coursework 1 demo CLI")
    parser.add_argument(
        "--datetime",
        default="2023-12-15 15:30:00",
        help="Datetime 'YYYY-MM-DD HH:MM:SS'"
    )
    parser.add_argument(
        "--file",
        default=str(Path(__file__).resolve().parent.parent / "data" / "operations.xlsx"),
        help="Path to operations file"
    )
    parser.add_argument(
        "--category",
        default="Супермаркеты",
        help="Category for spend report"
    )
    args = parser.parse_args()

    # Вызов функции главной страницы
    print("Главная страница:")
    print(index(args.datetime, args.file))
    print("\n")

    # Вызов функции отчетов
    print("Отчет по категориям:")
    if Path(args.file).exists():
        df = pd.read_excel(args.file)
        print(f"Расходы по категории '{args.category}':",
              spend_by_category(df, category=args.category))
    else:
        print("Файл с транзакциями не найден")
    print("\n")

    # Вызов функции сервисов
    print("Сервисы - рекомендации товаров:")

    # Создаем список словарей с данными транзакций для рекомендаций
    if Path(args.file).exists():
        df = pd.read_excel(args.file)
        # Преобразуем DataFrame в список словарей (предполагаем, что функция ожидает такой формат)
        transactions_data = df.to_dict('records')
        print(suggest_products(transactions_data))
    else:
        print("Файл с транзакциями не найден, рекомендации недоступны")


if __name__ == "__main__":
    main()
