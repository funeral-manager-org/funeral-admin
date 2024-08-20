import re
from datetime import datetime, timedelta
from enum import Enum
from os import path

from dateutil.relativedelta import relativedelta
from ulid import ULID


# TODO create a class to contain this enum types for the entire project
class PaymentMethod(Enum):
    CREDIT_CARD = "credit_card"
    CASH = "cash"
    DIRECT_DEPOSIT = "direct_deposit"
    BANK_TRANSFER = "bank_transfer"

def is_valid_ulid(value: str):
    ulid_regex = re.compile(r'^[0-9A-HJKMNP-TV-Z]{9,26}$')
    return ulid_regex.match(value)
#
# def is_valid_ulid(value: str) -> bool:
#     ulid_regex = re.compile(r'^[0-9A-HJKMNP-TV-Z]{26}$')  # Fixed regex for ULID (26 characters)
#     return bool(ulid_regex.match(value))

def is_valid_ulid_strict(value):
    ulid_regex = re.compile(r'^[0-9A-HJKMNP-TV-Z]{26}$')
    return ulid_regex.match(value)

def get_payment_methods() -> list[str]:
    """
    Get a list of payment methods.

    :return: A list of payment methods.
    """
    return [method.value for method in PaymentMethod]


def static_folder() -> str:
    return path.join(path.dirname(path.abspath(__file__)), '../../static')


def template_folder() -> str:
    return path.join(path.dirname(path.abspath(__file__)), '../../templates')


def format_with_grouping(number):
    parts = str(number).split(".")
    whole_part = parts[0]

    formatted_whole_part = ""
    while whole_part:
        formatted_whole_part = whole_part[-3:] + formatted_whole_part
        whole_part = whole_part[:-3]
        if whole_part:
            formatted_whole_part = "," + formatted_whole_part

    if len(parts) > 1:
        decimal_part = parts[1]
        formatted_number = f"{formatted_whole_part}.{decimal_part}"
    else:
        formatted_number = formatted_whole_part

    return formatted_number


def days_left(value):
    if value is None:
        return None

    delta = relativedelta(days=value)

    if value < 60:
        return f"{value} days"

    parts = []
    if delta.years:
        parts.append(f"{delta.years} years")
    if delta.months:
        parts.append(f"{delta.months} months")
    if delta.days:
        parts.append(f"{delta.days} days")

    return ', '.join(parts)


def format_square_meters(value):
    return f"{value} m²"


def format_payment_method(value):
    if value in [method.value for method in PaymentMethod]:
        return value.replace("_", " ").title()
    else:
        return "Unknown"


def friendlytimestamp(value):
    # List of possible formats for the timestamp
    formats = [
        '%Y-%m-%d %H:%M:%S.%f',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d'
    ]
    print(f"TIME FORMAT : {value}")
    # Convert the string timestamp to a datetime object using different formats
    timestamp_dt = None
    for fmt in formats:
        try:
            timestamp_dt = datetime.strptime(value, fmt)
            break  # Stop if a valid format is found
        except ValueError:
            continue

    if not timestamp_dt:
        raise ValueError(f"Time data '{value}' does not match any of the formats.")

    # Get the current date and time
    current_dt = datetime.now()

    # Calculate the time difference between now and the given timestamp
    time_difference = current_dt - timestamp_dt
    hour = 60*60
    one_day = 60*60*24
    minute = 60
    # Handle cases based on the time difference
    if time_difference.total_seconds() < minute:
        return "just now"
    elif time_difference.total_seconds() < hour:
        minutes = int(time_difference.total_seconds() / minute)
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    elif time_difference.total_seconds() < one_day:
        hours = int(time_difference.total_seconds() / hour)
        return f"{hours} hour{'s' if hours > 1 else ''} ago"

    # Check if it's the same calendar day
    if current_dt.date() == timestamp_dt.date():
        return "today"
    # Check if it's yesterday
    elif current_dt.date() - timestamp_dt.date() == timedelta(days=1):
        return "yesterday"
    # Check if it's within a week
    elif time_difference.days < 7:
        return f"{time_difference.days} day{'s' if time_difference.days > 1 else ''} ago"
    # Check if it's within a month
    elif time_difference.days < 30:
        weeks = int(time_difference.days / 7)
        return f"{weeks} week{'s' if weeks > 1 else ''} ago"
    # Fallback to the date format for older timestamps
    else:
        return timestamp_dt.strftime("%Y-%m-%d")

def friendly_calendar(value: str):
    """

    :param value:
    :return:
    """

    formats = [
        '%Y-%m-%d %H:%M:%S.%f',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d'
    ]
    print(f"TIME FORMAT : {value}")
    # Convert the string timestamp to a datetime object using different formats
    timestamp_dt = None
    for fmt in formats:
        try:
            timestamp_dt = datetime.strptime(value, fmt)
            break  # Stop if a valid format is found
        except ValueError:
            continue

    if not timestamp_dt:
        raise ValueError(f"Time data '{value}' does not match any of the formats.")

    # Get the current date and time
    current_dt = datetime.now()

    # Calculate the time difference between now and the given timestamp
    time_difference = current_dt - timestamp_dt

    # Check if it's the same calendar day
    if current_dt.date() == timestamp_dt.date():
        return "Today"
    # Check if it's yesterday
    elif current_dt.date() - timestamp_dt.date() == timedelta(days=1):
        return "Yesterday"
    # Check if it's within a week
    elif time_difference.days < 7:
        return f"{time_difference.days} Day{'s' if time_difference.days > 1 else ''} ago"
    # Check if it's within a month
    elif time_difference.days < 30:
        weeks = int(time_difference.days / 7)
        return f"{weeks} Week{'s' if weeks > 1 else ''} ago"
    # Fallback to the date format for older timestamps
    else:
        return timestamp_dt.strftime("%Y-%m-%d")

def create_id() -> str:
    return str(ULID.from_datetime(datetime.now()))

def create_reference() -> str:
    """payment reference"""
    return create_id()[-6:].upper()


def create_plan_number() -> str:
    return create_id()[-9:].upper()  # Extract a random part (9 characters)

def create_claim_number() -> str:
    return create_id()[-12:].upper()  # Extract a random part (12 characters)

def create_policy_number() -> str:
    return create_id()[-9:].upper()  # Extract a random part (9 characters)

def create_employee_id() -> str:
    return create_id()[-9:].upper()  # Extract a random part (9 characters)
def string_today():
    return str(datetime.today().date())


def camel_to_snake(name: str) -> str:
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


if __name__ == "__main__":
    for i in range(10):
        print(create_id())