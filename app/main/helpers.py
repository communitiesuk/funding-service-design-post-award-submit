from datetime import datetime


def get_current_date() -> datetime.date:
    """
    Returns the current date, without a timestamp.
    Separated from the original function for ease of testing/mocking
    Returns: date object
    """
    return datetime.date(datetime.now())
