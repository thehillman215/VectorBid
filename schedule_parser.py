
"""Parse airline bid packages (PDF, CSV, TXT) into structured trip dictionaries."""
import io
import csv
import re
import logging
from datetime import datetime

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None
    logging.warning('PyMuPDF not installed – PDF parsing disabled.')


WEEKEND_DAYS = {5, 6}  # Saturday=5, Sunday=6


def _includes_weekend(date_str: str) -> bool:
    """Return True if any date string in DDMMM (e.g. 12DEC) falls on a weekend."""
    try:
        date = datetime.strptime(date_str.strip(), '%d%b')
        return date.weekday() in WEEKEND_DAYS
    except Exception:
        return False


def _trip_dict_from_match(match: re.Match) -> dict:
    groups = match.groupdict()
    trip_id = groups['trip_id']
    length = int(groups['days'])
    routing = groups.get('routing', '').strip()
    credit = float(groups.get('credit', 0.0))
    dates = groups.get('dates', '')
    includes_weekend = any(_includes_weekend(token) for token in re.findall(r'\d{1,2}[A-Z]{3}', dates))
    return {
        'trip_id': trip_id,
        'days': length,
        'routing': routing,
        'credit_hours': credit,
        'dates': dates,
        'includes_weekend': includes_weekend,
    }


# Simple regex pattern for United-style line (adapt as needed)
TRIP_PATTERN = re.compile(
    r'(?P<trip_id>\d{3,4})\s+'
    r'(?P<days>[12-9])-Day\s+Trip.*?'
    r'(?P<dates>\d{2}[A-Z]{3}.*?\d{2}[A-Z]{3}).*?'
    r'Credit\s+(?P<credit>[\d\.]+).*?'
    r'(?P<routing>[A-Z]{3}-.+)',
    re.IGNORECASE
)


def parse_pdf_schedule(data: bytes) -> list[dict]:
    if not fitz:
        raise RuntimeError('PDF parsing unavailable – install PyMuPDF.')
    trips = []
    with fitz.open(stream=data, filetype='pdf') as doc:
        for page in doc:
            text = page.get_text('text')
            for match in TRIP_PATTERN.finditer(text):
                trips.append(_trip_dict_from_match(match))
    return trips


def parse_csv_schedule(data: bytes) -> list[dict]:
    trips = []
    reader = csv.DictReader(io.StringIO(data.decode()))
    for row in reader:
        try:
            trip = {
                'trip_id': row['TripID'],
                'days': int(row['Days']),
                'routing': row['Routing'],
                'credit_hours': float(row['CreditHours']),
                'dates': row['Dates'],
                'includes_weekend': any(_includes_weekend(tok) for tok in re.findall(r'\d{1,2}[A-Z]{3}', row['Dates'])),
            }
            trips.append(trip)
        except KeyError:
            continue
    return trips


def parse_txt_schedule(data: bytes) -> list[dict]:
    trips = []
    text = data.decode(errors='ignore')
    for match in TRIP_PATTERN.finditer(text):
        trips.append(_trip_dict_from_match(match))
    return trips


def parse_schedule_file(file_storage) -> list[dict]:
    """Detect file type and return list of trips."""
    filename = file_storage.filename.lower()
    data = file_storage.read()
    if filename.endswith('.pdf'):
        return parse_pdf_schedule(data)
    elif filename.endswith('.csv'):
        return parse_csv_schedule(data)
    elif filename.endswith('.txt'):
        return parse_txt_schedule(data)
    else:
        raise ValueError('Unsupported file type.')
