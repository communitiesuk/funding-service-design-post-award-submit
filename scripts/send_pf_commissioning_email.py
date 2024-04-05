import argparse
import io
import os

from notifications_python_client import prepare_upload
from notifications_python_client.notifications import NotificationsAPIClient


def main(args):
    with open(args.email_file, "r") as f:
        emails = [line.strip() for line in f.readlines()]
        print(emails)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send commissioning email for Pathfinders (via Notify)")
    parser.add_argument(
        "-e",
        "--email-file",
        dest="email_file",
        default="emails.txt",
        help="Path to file containing line separated list of users to email",
    )
    main(parser.parse_args())


def send_notify(
    file_buffer: io.BytesIO,
    api_key: str = os.getenv("NOTIFY_API_KEY"),
    template_id: str = "c32ecc1e-0c17-4fef-b159-617948869daf",
    email_address: str = "test@example.com",
):
    if not api_key:
        raise KeyError("Notify API key is required to send email")
    notifications_client = NotificationsAPIClient(api_key)
    notifications_client.send_email_notification(
        email_address=email_address,
        template_id=template_id,
        personalisation={
            "link_to_file": prepare_upload(
                file_buffer,
                filename="Pathfinder Reporting Template v0.2.xslx",
            ),
        },
    )
