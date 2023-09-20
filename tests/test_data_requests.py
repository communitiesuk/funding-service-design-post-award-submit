import os
from datetime import datetime
from unittest import mock

from app.main.data_requests import calculate_days_remaining
from config import Config


@mock.patch.dict(os.environ, {"SUBMIT_DEADLINE": "15/11/2023"})
def test_valid_date(flask_test_client):
    Config.SUBMIT_DEADLINE = "15/11/2023"

    # Create a fixed date for mocking datetime.now()
    fixed_date = datetime(2023, 9, 20)

    with mock.patch("datetime.datetime") as mock_datetime:
        mock_datetime.datetime.return_value = fixed_date

        days_remaining = calculate_days_remaining()
        assert days_remaining == 56


def test_past_date(flask_test_client):
    # Create a fixed date for mocking datetime.now()
    Config.SUBMIT_DEADLINE = "05/06/2023"
    fixed_date = datetime(2023, 9, 20)

    with mock.patch("datetime.datetime") as mock_datetime:
        mock_datetime.datetime.return_value = fixed_date

        days_remaining = calculate_days_remaining()
        assert days_remaining == -107
