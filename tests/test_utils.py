import datetime as dt

from src.utils import send_greeting


def test_send_greeting_morning():
    d = dt.datetime(2023, 1, 1, 8, 0, 0)
    assert send_greeting(d) == "Доброе утро"
