import pandas as pd

from src.reports import spend_by_category

df = pd.DataFrame(
    {
        "Дата операции": ["2023-10-10", "2023-11-05", "2023-12-01"],
        "Категория": ["Супермаркеты", "Супермаркеты", "Кафе и рестораны"],
        "Сумма платежа": [100, 150, 200],
    }
)


def test_spend_by_category(tmp_path):
    res = spend_by_category(df, "Супермаркеты", "2023-12-15")
    assert res["total_spent"] == 250
