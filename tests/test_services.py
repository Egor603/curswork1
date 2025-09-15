from unittest.mock import patch


@patch("src.services.requests.get")
def test_get_rates(mock_get):
    mock_get.return_value.json.return_value = {"data": {"EUR": {"value": 0.9}}}
    mock_get.return_value.raise_for_status = lambda: None

    # <‑‑‑ ключевой момент: подменяем константу внутри модуля
    with patch("src.services.API_KEY", "dummy_key"):
        from src.services import get_rates

        assert get_rates("USD")["EUR"] == 0.9
