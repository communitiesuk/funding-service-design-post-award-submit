from datetime import datetime, timedelta

from app.main.utils import calculate_days_to_deadline
from config import Config


def test_default_behaviour(flask_test_client):
    days_remaining = calculate_days_to_deadline()

    assert isinstance(days_remaining, int)


def test_calculate_future_date(flask_test_client):
    mock_current_date = datetime.strptime("01/09/2023", "%d/%m/%Y").date()

    Config.SUBMIT_DEADLINE = "15/11/2023"
    days_remaining = calculate_days_to_deadline(mock_current_date)
    assert days_remaining == 75


def test_calculate_past_date(flask_test_client):
    mock_current_date = datetime.strptime("10/09/2023", "%d/%m/%Y").date()

    Config.SUBMIT_DEADLINE = "05/06/2023"
    days_remaining = calculate_days_to_deadline(mock_current_date)
    assert days_remaining == -97


def test_future_deadline_view(flask_test_client):
    # Set submit deadline to 10 days in the future
    submit_deadline = datetime.now() + timedelta(days=10)
    Config.SUBMIT_DEADLINE = submit_deadline.strftime("%d/%m/%Y")

    response = flask_test_client.get("/upload")

    # The normal banner should be displayed if submission is not overdue
    assert b"overdue-notification-banner" not in response.data
    assert b"You have 10 days left to submit your April to September 2023 return" in response.data


def test_overdue_deadline_view(flask_test_client):
    # Set submit deadline to 10 days in the past
    submit_deadline = datetime.now() - timedelta(days=10)
    Config.SUBMIT_DEADLINE = submit_deadline.strftime("%d/%m/%Y")

    response = flask_test_client.get("/upload")

    # The red version of the banner should be displayed if submission is overdue
    assert b"overdue-notification-banner" in response.data

    assert b"Your data return is 10 late." in response.data
    assert b"Submit your return as soon as possible to avoid delays in your funding." in response.data
