from app.main.data_requests import calculate_days_remaining
from config import Config


def test_future_date(flask_test_client, mocker):
    mocker.patch("app.main.helpers.get_current_date", return_value="2023-09-01")
    Config.SUBMIT_DEADLINE = "15/11/2023"
    days_remaining = calculate_days_remaining()
    assert days_remaining == 75


# def test_past_date(flask_test_client, mocker):
#     mocker.patch('app.main.helpers.get_current_date', return_value="2023-09-10")
#     Config.SUBMIT_DEADLINE = "05/06/2023"
#     days_remaining = calculate_days_remaining()
#     assert days_remaining == -97
