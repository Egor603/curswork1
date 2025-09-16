from unittest.mock import patch, MagicMock
import sys
import os
import pytest
import requests.exceptions

# Добавляем путь к src в PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Импортируем из src.services — подавляем E402, так как sys.path.insert обязателен до этого
from src.services import (  # noqa: E402
    get_rates,
    convert,
    CurrencyServiceError,
    simple_search,
    investment_bank,
    phone_search,
    people_transfer_search,
)


# Вспомогательная функция: сбрасывает кэш get_rates
def clear_get_rates_cache():
    get_rates.cache_clear()


# 0. Тест: сброс кэша перед каждым тестом (чтобы не мешал)
@pytest.fixture(autouse=True)
def clear_cache():
    clear_get_rates_cache()


# =================== ТЕСТЫ get_rates ===================

# 1. Успешный вызов
@patch("src.services.requests.get")
def test_get_rates_success(mock_get):
    mock_get.return_value.json.return_value = {
        "data": {
            "EUR": {"value": "0.9"},
            "RUB": {"value": "94.5"},
        }
    }
    mock_get.return_value.raise_for_status = lambda: None

    with patch("src.services.API_KEY", "dummy_key"):
        result = get_rates("USD")
        assert result["EUR"] == 0.9
        assert result["RUB"] == 94.5
        assert isinstance(result["EUR"], float)  # ← убедились, что конвертация в float работает


# 2. API_KEY не задан
def test_get_rates_no_api_key():
    with patch("src.services.API_KEY", None):
        with pytest.raises(CurrencyServiceError, match="API_KEY не задан в окружении"):
            get_rates("USD")


# 3. Сетевая ошибка
@patch("src.services.requests.get")
def test_get_rates_network_error(mock_get):
    mock_get.side_effect = requests.exceptions.ConnectionError("Network down")

    with patch("src.services.API_KEY", "dummy_key"):
        with pytest.raises(requests.exceptions.ConnectionError):
            get_rates("USD")


# 4. HTTP ошибка (например, 401)
@patch("src.services.requests.get")
def test_get_rates_http_error(mock_get):
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("401 Unauthorized")
    mock_get.return_value = mock_response

    with patch("src.services.API_KEY", "dummy_key"):
        with pytest.raises(requests.exceptions.HTTPError):
            get_rates("USD")


# 5. Некорректный ответ (нет ключа "data")
@patch("src.services.requests.get")
def test_get_rates_invalid_response(mock_get):
    mock_get.return_value.raise_for_status = lambda: None
    mock_get.return_value.json.return_value = {"error": "something went wrong"}

    with patch("src.services.API_KEY", "dummy_key"):
        with pytest.raises(CurrencyServiceError, match="Некорректный ответ currencyapi"):
            get_rates("USD")


# 6. Проверка кэширования (@lru_cache)
@patch("src.services.requests.get")
def test_get_rates_cache(mock_get):
    mock_get.return_value.json.return_value = {"data": {"EUR": {"value": "0.9"}}}
    mock_get.return_value.raise_for_status = lambda: None

    with patch("src.services.API_KEY", "dummy_key"):
        # Первый вызов — должен вызвать requests.get
        get_rates("USD")
        assert mock_get.call_count == 1

        # Второй вызов — должен взять из кэша, НЕ вызывая requests.get
        get_rates("USD")
        assert mock_get.call_count == 1  # ← не изменилось!

        # Сбросим кэш и вызовем снова — должен вызвать снова
        clear_get_rates_cache()
        get_rates("USD")
        assert mock_get.call_count == 2


# =================== ТЕСТЫ convert ===================

# 7. Успешная конвертация
@patch("src.services.get_rates")
def test_convert_success(mock_get_rates):
    mock_get_rates.return_value = {"RUB": 90.0, "EUR": 0.85}
    result = convert(9000.0, "RUB", "USD")
    assert result == pytest.approx(100.0)  # 9000 / 90 = 100


# 8. Валюта не найдена
@patch("src.services.get_rates")
def test_convert_currency_not_found(mock_get_rates):
    mock_get_rates.return_value = {"EUR": 0.85}
    with pytest.raises(CurrencyServiceError, match="Нет курса для RUB"):
        convert(100.0, "RUB", "USD")


# =================== ТЕСТЫ простого поиска ===================

# 9. Простой поиск по описанию
def test_simple_search_description():
    transactions = [
        {"Описание": "Покупка в СТАРОМ АРБАТЕ", "Категория": "Еда"},
        {"Описание": "Такси", "Категория": "Транспорт"},
    ]
    result = simple_search("арбат", transactions)
    assert "СТАРОМ АРБАТЕ" in result
    assert "Такси" not in result


# 10. Простой поиск по категории
def test_simple_search_category():
    transactions = [
        {"Описание": "Кофе", "Категория": "Кафе"},
        {"Описание": "Бензин", "Категория": "Авто"},
    ]
    result = simple_search("кафе", transactions)
    assert "Кофе" in result
    assert "Бензин" not in result


# 11. Поиск без совпадений
def test_simple_search_no_results():
    transactions = [{"Описание": "Кофе", "Категория": "Кафе"}]
    result = simple_search("пицца", transactions)
    assert result == "[]"


# =================== ТЕСТЫ investment_bank ===================

# 12. Успешный расчет инвесткопилки
def test_investment_bank_success():
    transactions = [
        {"Дата операции": "2024-05-15", "Сумма операции": 100.1},
        {"Дата операции": "2024-05-20", "Сумма операции": 50.5},
    ]
    result = investment_bank("2024-05", transactions, 10)
    # 100.1 → 110 → +9.9; 50.5 → 60 → +9.5; total = 19.4
    assert result == 19.4


# 13. Неверный формат месяца
def test_investment_bank_invalid_month():
    with pytest.raises(ValueError, match="month must be in 'YYYY-MM' format"):
        investment_bank("2024/05", [], 10)


# 14. Неверный лимит
def test_investment_bank_invalid_limit():
    with pytest.raises(ValueError, match="limit must be 10, 50 or 100"):
        investment_bank("2024-05", [], 25)


# =================== ТЕСТЫ phone_search ===================

# 15. Поиск по телефону — найдено
def test_phone_search_found():
    transactions = [
        {"Описание": "Перевод +7 999 123-45-67"},
        {"Описание": "Покупка кофе"},
    ]
    result = phone_search(transactions)
    assert "+7 999 123-45-67" in result
    assert "кофе" not in result


# 16. Поиск по телефону — не найдено
def test_phone_search_not_found():
    transactions = [{"Описание": "Покупка кофе"}]
    result = phone_search(transactions)
    assert result == "[]"


# =================== ТЕСТЫ people_transfer_search ===================

# 17. Поиск переводов физлицам — найдено
def test_people_transfer_search_found():
    transactions = [
        {"Описание": "Иванов И.", "Категория": "Переводы"},
        {"Описание": "Сбербанк", "Категория": "Переводы"},
    ]
    result = people_transfer_search(transactions)
    assert "Иванов И." in result
    assert "Сбербанк" not in result


# 18. Поиск переводов — не в категории "Переводы"
def test_people_transfer_search_wrong_category():
    transactions = [{"Описание": "Иванов И.", "Категория": "Еда"}]
    result = people_transfer_search(transactions)
    assert result == "[]"
