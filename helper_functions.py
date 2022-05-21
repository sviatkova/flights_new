import sys
from datetime import datetime

USAGE = f"Usage: python {sys.argv[0]} [--help] | dataset origin " \
    "destination --bags --return --returnarrival --arival --departure"

# flight categories in order they should be at output
FLIGHT_INFORMATION = [
    "flight_no", "origin", "destination", "departure",
    "arrival", "base_price", "bag_price", "bags_allowed"
]


def valid_airport_code(code: str) -> bool:
    if len(code) == 3:
        if code.isalpha():
            if code.isupper():
                return True
    return False


def end_searching(reason: str):
    print(f"Error: {reason}")
    raise SystemExit(USAGE)



def str_to_datetime(time: str) -> datetime:
    try:
        return datetime.strptime(time, "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        # can not format into datetime object
        end_searching(
            "Invalid time - was suppossed to be as YYYY-MM-DDTHH:MM:SS")

