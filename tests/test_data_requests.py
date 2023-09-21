from datetime import datetime

from app.main.data_requests import calculate_days_remaining
from config import Config


def test_calculate_future_date(flask_test_client):
    mock_current_date = datetime.strptime("01/09/2023", "%d/%m/%Y").date()

    Config.SUBMIT_DEADLINE = "15/11/2023"
    days_remaining = calculate_days_remaining(mock_current_date)
    assert days_remaining == 75


# TODO consider desired behaviour if deadline date is in the past
def test_calculate_past_date(flask_test_client, mocker):
    mock_current_date = datetime.strptime("10/09/2023", "%d/%m/%Y").date()

    Config.SUBMIT_DEADLINE = "05/06/2023"
    days_remaining = calculate_days_remaining(mock_current_date)
    assert days_remaining == -97
