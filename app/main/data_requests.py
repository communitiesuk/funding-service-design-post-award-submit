from datetime import datetime

import requests
from flask import abort, current_app
from requests import Response
from werkzeug.datastructures import FileStorage

from app.const import MIMETYPE
from config import Config


def post_ingest(file: FileStorage, data: dict = None) -> Response:
    """Send an HTTP POST request to ingest into the data store
     server and return the response.

    This function sends an HTTP POST request including the given
    Excel file and request body and handles any bad responses.


    :param file: Excel workbook uploaded to the front end
    :param data: optional dictionary to send in the body of the request.
    :return: The requests Response object containing the response
    from the remote server.
    """
    request_url = Config.DATA_STORE_API_HOST + "/ingest"
    files = {"excel_file": (file.name, file, MIMETYPE.XLSX)}

    response = requests.post(request_url, files=files, data=data)

    if response.status_code in [200, 400, 500]:
        return response

    else:
        current_app.logger.error(f"Bad response: {request_url} returned {response.status_code}")
        return abort(500)


def calculate_days_remaining(current_date=datetime.date(datetime.now())):
    """Calculate the number of days remaining until a specified submission deadline.
    The due_date is a str representation of submission deadline in format dd/mm/yyyy.
    It is set in main/config/envs/default.py

    :param current_date: datetime object representing today's date without timestamp
    Returns:
    int: The number of days remaining until the submission deadline.
    """

    due_date = Config.SUBMIT_DEADLINE
    delta = datetime.strptime(due_date, "%d/%m/%Y").date() - current_date
    return delta.days
