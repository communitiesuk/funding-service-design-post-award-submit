import json
from datetime import datetime

import requests
from flask import current_app, g, redirect, render_template, request, url_for
from fsd_utils.authentication.config import SupportedApp
from fsd_utils.authentication.decorators import login_requested, login_required
from werkzeug.datastructures import FileStorage
from werkzeug.exceptions import HTTPException, abort

from app.const import MIMETYPE
from app.main import bp
from app.main.data_requests import post_ingest
from app.main.decorators import set_user_access
from app.main.notify import send_confirmation_emails
from app.utils import days_between_dates, is_load_enabled
from config import Config


@bp.route("/", methods=["GET"])
@login_requested
def index():
    if not g.is_authenticated:
        return redirect(url_for("main.login"))
    else:
        return redirect(url_for("main.dashboard"))


@bp.route("/login", methods=["GET"])
def login():
    return render_template("login.html")


@bp.route("/dashboard", methods=["GET"])
@login_required(return_app=SupportedApp.POST_AWARD_SUBMIT)
@set_user_access
def dashboard():
    return render_template("dashboard.html", authorised_funds=g.access.items())


@bp.route("/upload/<fund_code>/<round>", methods=["GET", "POST"])
@login_required(return_app=SupportedApp.POST_AWARD_SUBMIT)
@set_user_access
def upload(fund_code, round):
    if fund_code not in g.access:
        abort(401)

    fund = g.access[fund_code].fund
    auth = g.access[fund_code].auth
    submitting_account_id = g.account_id
    submitting_user_email = g.user.email

    if request.method == "GET":
        return render_template(
            "upload.html",
            days_to_deadline=days_between_dates(datetime.now().date(), fund.current_deadline),
            reporting_period=fund.current_reporting_period,
            fund_name=fund.fund_name,
            fund_code=fund.fund_code,
            current_reporting_round=fund.current_reporting_round,
            local_authorities=auth.get_organisations(),
        )

    if request.method == "POST":
        excel_file = request.files.get("ingest_spreadsheet")

        if pre_errors := check_file(excel_file):
            validation_errors, metadata = None, None
        else:
            pre_errors, validation_errors, metadata = post_ingest(
                excel_file,
                {
                    "fund_name": fund.fund_name,
                    "reporting_round": fund.current_reporting_round,
                    "auth": json.dumps(auth.get_auth_dict()),
                    "do_load": is_load_enabled(),
                    "submitting_account_id": submitting_account_id,
                    "submitting_user_email": submitting_user_email,
                },
            )

        if pre_errors:
            # Pre-validation failure
            if Config.ENABLE_VALIDATION_LOGGING:
                for pre_err in pre_errors:
                    current_app.logger.info("Pre-validation error: {error}", extra=dict(error=pre_err))
            else:
                current_app.logger.info(
                    "{num_errors} pre-validation error(s) found during upload", extra=dict(num_errors=len(pre_errors))
                )

            return render_template(
                "upload.html",
                pre_error=pre_errors,
                days_to_deadline=days_between_dates(datetime.now().date(), fund.current_deadline),
                reporting_period=fund.current_reporting_period,
                fund_name=fund.fund_name,
                fund_code=fund.fund_code,
                current_reporting_round=fund.current_reporting_round,
                local_authorities=auth.get_organisations(),
            )
        elif validation_errors:
            # Validation failure
            if Config.ENABLE_VALIDATION_LOGGING:
                for validation_err in validation_errors:
                    current_app.logger.info("Validation error: {error}", extra=dict(error=validation_err))
            else:
                current_app.logger.info(
                    "{num_errors} validation error(s) found during upload",
                    extra=dict(num_errors=len(validation_errors)),
                )

            return render_template("validation-errors.html", validation_errors=validation_errors, fund=fund)
        else:
            # Success

            if Config.SEND_CONFIRMATION_EMAILS:
                send_confirmation_emails(
                    excel_file,
                    fund=fund.fund_name,
                    reporting_period=fund.current_reporting_period,
                    fund_email=fund.email,
                    user_email=g.user.email,
                    metadata=metadata,
                )
            metadata["User"] = g.user.email
            current_app.logger.info(
                "Upload successful for {fund} round {round}: {metadata}",
                extra=dict(metadata=metadata, fund=fund_code, round=round),
            )

            return render_template("success.html", file_name=excel_file.filename)


def check_file(excel_file: FileStorage) -> list[str] | None:
    """Basic checks on an uploaded file.

    Checks:
        - A file has been uploaded
        - If a file has been uploaded, that it's an Excel file

    :param excel_file: a file to check
    :return: an error message if any errors, else None
    """
    error = None
    if not excel_file:
        error = ["Select your returns template."]
    elif excel_file.content_type != MIMETYPE.XLSX:
        error = ["The selected file must be an XLSX."]
    return error


@bp.app_errorhandler(HTTPException)
def http_exception(error):
    """
    Returns the correct page template for specified HTTP errors, and the
    500 (generic) template for any others.

    :param error: object containing attributes related to the error
    :return: HTML template describing user-facing error, and error code
    """
    error_templates = [401, 404, 429, 500, 503]

    if error.code in error_templates:
        return render_template(f"{error.code}.html"), error.code
    else:
        current_app.logger.info("Unhandled HTTP error {error_code} found.", extra=dict(error_code=error.code))
        return render_template("500.html"), error.code

@bp.route("/tasklist/<fund_name>", methods=["GET"])
@login_required(return_app=SupportedApp.POST_AWARD_SUBMIT)
@set_user_access
def tasklist(fund_name: str):
    tasks_by_fund = {
        "Pathfinders": [
            {
                "title": "Admin",
                "href": "http://localhost:4003/run-form/admin-rfp"
            }
        ]
    }
    return render_template("tasklist.html", tasks=tasks_by_fund[fund_name])

@bp.route("/run-form/<form_name>", methods=["GET"])
@login_required(return_app=SupportedApp.POST_AWARD_SUBMIT)
@set_user_access
def run_form(form_name: str):
    rehydrate_payload = {
        "options": {
            "callbackUrl": f"http://data-store:8080/upload?task={form_name}",
            "returnUrl": "http://localhost:4003/tasklist/Pathfinders",
        },
        "questions": [],
        "metadata": {
            "form_name": form_name,
        }
    }
    rehydrate_token_url = "http://form-runner:3009/session/" + form_name
    rehydrate_token_response = requests.post(
        rehydrate_token_url,
        json=rehydrate_payload,
        timeout=10
    )
    rehydrate_token = rehydrate_token_response.json()["token"]
    return redirect("http://localhost:3009/session/" + rehydrate_token)
