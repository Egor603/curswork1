import argparse
from .views import index
from pathlib import Path
import pandas as pd
from .reports import spend_by_category


def main() -> None:
    parser = argparse.ArgumentParser(description="Coursework 1 demo CLI")
    parser.add_argument("--datetime", default="2023-12-15 15:30:00", help="Datetime 'YYYY-MM-DD HH:MM:SS'")
    parser.add_argument("--file", default=str(Path(__file__).resolve().parent.parent / "data" / "operations.xlsx"))
    args = parser.parse_args()

    print(index(args.datetime, args.file))


if __name__ == "__main__":
    main()


def main() -> None:
    filepath = Path(__file__).parent.parent / "data" / "transactions.xlsx"
    if filepath.exists():
        df = pd.read_excel(filepath)
        print(spend_by_category(df, category="Супермаркеты"))
    else:
        print("Нет файла с транзакциями, пропускаем отчёт.")


if __name__ == "__main__":
    main()
