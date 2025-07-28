
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
    
    # Handle different field formats
    trip_id = groups.get('trip_id', '').strip()
    
    # Parse days - could be "3" or "3-Day"
    days_raw = groups.get('days', '0')
    try:
        days = int(re.search(r'(\d+)', days_raw).group(1))
    except (AttributeError, ValueError):
        days = 0
    
    routing = groups.get('routing', '').strip()
    
    # Parse credit hours - handle various formats
    credit_raw = groups.get('credit', '0')
    try:
        credit = float(re.search(r'([\d\.]+)', credit_raw).group(1))
    except (AttributeError, ValueError):
        credit = 0.0
    
    dates = groups.get('dates', '').strip()
    includes_weekend = any(_includes_weekend(token) for token in re.findall(r'\d{1,2}[A-Z]{3}', dates))
    
    return {
        'trip_id': trip_id,
        'days': days,
        'routing': routing,
        'credit_hours': credit,
        'dates': dates,
        'includes_weekend': includes_weekend,
    }


# Multiple patterns for different airline formats
PATTERNS = [
    # United Airlines style: "1234 3-Day Trip 12NOV-15NOV Credit 18.5 IAH-SFO-IAH"
    re.compile(
        r'(?P<trip_id>\d{3,4})\s+'
        r'(?P<days>[12-9])-Day\s+Trip.*?'
        r'(?P<dates>\d{2}[A-Z]{3}.*?\d{2}[A-Z]{3}).*?'
        r'Credit\s+(?P<credit>[\d\.]+).*?'
        r'(?P<routing>[A-Z]{3}-.+)',
        re.IGNORECASE
    ),
    # Generic format: "Trip 1234: 3 days, 18.5 hrs, IAH-SFO-IAH, 12NOV-15NOV"
    re.compile(
        r'Trip\s+(?P<trip_id>\d{3,4}).*?'
        r'(?P<days>\d+)\s+days.*?'
        r'(?P<credit>[\d\.]+)\s+hrs.*?'
        r'(?P<routing>[A-Z]{3}[- ][A-Z]{3}.*?)(?:,|\s)'
        r'(?P<dates>\d{2}[A-Z]{3}.*?\d{2}[A-Z]{3})',
        re.IGNORECASE
    ),
    # Block format: Trip ID on separate line from details
    re.compile(
        r'(?P<trip_id>\d{3,4})\s*\n.*?'
        r'(?P<dates>\d{1,2}[A-Z]{3}-\d{1,2}[A-Z]{3}).*?'
        r'(?P<days>\d+)\s*day.*?'
        r'(?P<credit>[\d\.]+).*?'
        r'(?P<routing>[A-Z]{3}.*?[A-Z]{3})',
        re.IGNORECASE | re.DOTALL
    ),
    # Simple pattern: Look for basic trip components
    re.compile(
        r'(?P<trip_id>\d{3,4}).*?'
        r'(?P<routing>[A-Z]{3}[^a-z]*[A-Z]{3}).*?'
        r'(?P<days>\d+).*?'
        r'(?P<credit>\d+\.?\d*).*?'
        r'(?P<dates>\d{1,2}[A-Z]{3})',
        re.IGNORECASE
    )
]


def parse_pdf_schedule(data: bytes) -> list[dict]:
    if not fitz:
        raise RuntimeError('PDF parsing unavailable – install PyMuPDF.')
    trips = []
    all_text = ""
    
    with fitz.open(stream=data, filetype='pdf') as doc:
        for page in doc:
            text = page.get_text('text')
            all_text += text + "\n"
            
            # Try each pattern
            for pattern in PATTERNS:
                for match in pattern.finditer(text):
                    try:
                        trip = _trip_dict_from_match(match)
                        if trip['trip_id'] and trip['days']:  # Basic validation
                            trips.append(trip)
                    except Exception as e:
                        logging.debug(f"Failed to parse match: {e}")
                        continue
    
    # Log debugging info if no trips found
    if not trips:
        logging.error(f"No trips found in PDF. Text sample (first 500 chars): {all_text[:500]}")
        # Try to find any numbers that might be trip IDs
        potential_trips = re.findall(r'\b\d{3,4}\b', all_text)
        logging.error(f"Potential trip IDs found: {potential_trips[:10]}")
        
        # Try fallback parsing for any structured data
        trips = _fallback_parse(all_text)
    
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
    
    # Try each pattern
    for pattern in PATTERNS:
        for match in pattern.finditer(text):
            try:
                trip = _trip_dict_from_match(match)
                if trip['trip_id'] and trip['days']:  # Basic validation
                    trips.append(trip)
            except Exception as e:
                logging.debug(f"Failed to parse match: {e}")
                continue
    
    # Log debugging info if no trips found
    if not trips:
        logging.error(f"No trips found in text. Sample (first 500 chars): {text[:500]}")
        # Try fallback parsing
        trips = _fallback_parse(text)
    
    return trips


def _fallback_parse(text: str) -> list[dict]:
    """Fallback parser for when regex patterns fail."""
    trips = []
    lines = text.split('\n')
    
    # Look for lines with trip-like patterns
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Look for numbers that could be trip IDs
        trip_ids = re.findall(r'\b\d{3,4}\b', line)
        if not trip_ids:
            continue
            
        # Look for routing patterns (3-letter codes)
        airports = re.findall(r'\b[A-Z]{3}\b', line)
        if len(airports) < 2:
            continue
            
        # Look for numbers that could be days/hours
        numbers = re.findall(r'\b\d+\.?\d*\b', line)
        
        for trip_id in trip_ids:
            routing = '-'.join(airports[:4])  # Take first 4 airports max
            days = 3  # Default
            credit = 15.0  # Default
            
            # Try to extract actual numbers
            if len(numbers) >= 2:
                try:
                    days = int(float(numbers[1]))
                    if len(numbers) >= 3:
                        credit = float(numbers[2])
                except ValueError:
                    pass
            
            trip = {
                'trip_id': trip_id,
                'days': days,
                'routing': routing,
                'credit_hours': credit,
                'dates': 'TBD',
                'includes_weekend': False,
            }
            trips.append(trip)
            
            # Limit fallback results
            if len(trips) >= 10:
                break
                
        if len(trips) >= 10:
            break
    
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
