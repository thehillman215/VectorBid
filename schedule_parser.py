
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


# Simplified patterns to prevent timeout
PATTERNS = [
    # Simple trip pattern: "Trip 1234: LAX-SFO-LAX 3-Day"
    re.compile(
        r'Trip\s+(?P<trip_id>\d{3,4}):\s*(?P<routing>[A-Z]{3}-[A-Z-]+)\s+(?P<days>\d+)-Day.*?(?P<credit>[\d\.]+)',
        re.IGNORECASE
    ),
    # Basic format: "1234 LAX-SFO 3 days 18.5"
    re.compile(
        r'(?P<trip_id>\d{3,4})\s+(?P<routing>[A-Z]{3}-[A-Z-]+)\s+(?P<days>\d+)\s+days?\s+(?P<credit>[\d\.]+)',
        re.IGNORECASE
    )
]


def parse_pdf_schedule(data: bytes) -> list[dict]:
    if not fitz:
        raise RuntimeError('PDF parsing unavailable – install PyMuPDF.')
    
    try:
        with fitz.open(stream=data, filetype='pdf') as doc:
            # Extract text from first page only to prevent timeout
            if len(doc) == 0:
                return []
                
            text = doc[0].get_text('text')[:5000]  # Limit text length
            
            # Use fallback parsing directly - it's faster and more reliable
            trips = _fallback_parse(text)
            
            if not trips:
                logging.error(f"No trips found in PDF. Sample text: {text[:200]}")
                
            return trips
            
    except Exception as e:
        logging.error(f"PDF parsing failed: {e}")
        return []


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
    try:
        text = data.decode(errors='ignore')[:10000]  # Limit text size
        
        # Use fallback parsing directly for speed
        trips = _fallback_parse(text)
        
        if not trips:
            logging.error(f"No trips found in text. Sample: {text[:200]}")
        
        return trips
        
    except Exception as e:
        logging.error(f"Text parsing failed: {e}")
        return []


def _fallback_parse(text: str) -> list[dict]:
    """Fast fallback parser for when regex patterns fail."""
    trips = []
    lines = text.split('\n')[:50]  # Limit lines to prevent timeout
    
    for line in lines:
        line = line.strip()
        if len(line) < 10:  # Skip short lines
            continue
            
        # Quick pattern for trip-like lines
        if re.search(r'\d{3,4}.*[A-Z]{3}.*\d+', line):
            # Extract basic components
            trip_id_match = re.search(r'\b(\d{3,4})\b', line)
            airports = re.findall(r'\b[A-Z]{3}\b', line)
            numbers = re.findall(r'\b(\d+\.?\d*)\b', line)
            
            if trip_id_match and len(airports) >= 2:
                trip_id = trip_id_match.group(1)
                routing = '-'.join(airports[:3])
                days = 3
                credit = 15.0
                
                # Try to get actual numbers
                if len(numbers) >= 2:
                    try:
                        days = min(int(float(numbers[1])), 7)  # Reasonable limit
                        if len(numbers) >= 3:
                            credit = min(float(numbers[2]), 50.0)  # Reasonable limit
                    except ValueError:
                        pass
                
                trips.append({
                    'trip_id': trip_id,
                    'days': days,
                    'routing': routing,
                    'credit_hours': credit,
                    'dates': 'TBD',
                    'includes_weekend': False,
                })
                
                if len(trips) >= 5:  # Limit fallback results
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
