import csv
import io
import re
import logging
from datetime import datetime
from typing import List, Dict, Any

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None
    logging.warning("PyMuPDF not available. PDF parsing will not work.")


def parse_schedule_file(file_path: str, file_extension: str) -> List[Dict[str, Any]]:
    """
    Parse a schedule file and extract trip information.
    
    Args:
        file_path: Path to the uploaded file
        file_extension: File extension (.pdf, .csv, .txt)
    
    Returns:
        List of trip dictionaries with keys: id, duration, dates, routing, credit_hours, includes_weekend
    """
    try:
        if file_extension == '.pdf':
            return parse_pdf_schedule(file_path)
        elif file_extension == '.csv':
            return parse_csv_schedule(file_path)
        elif file_extension == '.txt':
            return parse_text_schedule(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    except Exception as e:
        logging.error(f"Error parsing schedule file: {str(e)}")
        raise


def parse_pdf_schedule(file_path: str) -> List[Dict[str, Any]]:
    """Parse PDF schedule using PyMuPDF"""
    if fitz is None:
        raise ImportError("PyMuPDF is required for PDF parsing")
    
    trips = []
    
    try:
        doc = fitz.open(file_path)
        text = ""
        
        # Extract text from all pages
        for page in doc:
            text += page.get_text() if hasattr(page, 'get_text') else ""
        
        doc.close()
        
        # Parse the extracted text
        trips = parse_schedule_text(text)
        
    except Exception as e:
        raise Exception(f"Failed to parse PDF: {str(e)}")
    
    return trips


def parse_csv_schedule(file_path: str) -> List[Dict[str, Any]]:
    """Parse CSV schedule file"""
    trips = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            # Try to detect delimiter
            sample = file.read(1024)
            file.seek(0)
            
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter
            
            reader = csv.DictReader(file, delimiter=delimiter)
            
            for row in reader:
                trip = extract_trip_from_row(row)
                if trip:
                    trips.append(trip)
                    
    except Exception as e:
        raise Exception(f"Failed to parse CSV: {str(e)}")
    
    return trips


def parse_text_schedule(file_path: str) -> List[Dict[str, Any]]:
    """Parse plain text schedule file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        
        return parse_schedule_text(text)
        
    except Exception as e:
        raise Exception(f"Failed to parse text file: {str(e)}")


def extract_trip_from_row(row: Dict[str, str]) -> Dict[str, Any]:
    """Extract trip information from a CSV row"""
    trip = {}
    
    # Map common CSV column names to our fields
    field_mappings = {
        'id': ['id', 'trip_id', 'tripid', 'trip id', 'number', 'trip_number'],
        'duration': ['duration', 'days', 'length', 'trip_length'],
        'dates': ['dates', 'date', 'period', 'schedule', 'start_date', 'end_date'],
        'routing': ['routing', 'route', 'cities', 'destinations', 'legs'],
        'credit_hours': ['credit_hours', 'credit', 'hours', 'time', 'flying_time', 'flight_time'],
        'includes_weekend': ['weekend', 'includes_weekend', 'weekends', 'sat_sun']
    }
    
    # Normalize row keys (lowercase, strip spaces)
    normalized_row = {k.lower().strip(): v for k, v in row.items()}
    
    for field, possible_keys in field_mappings.items():
        value = None
        for key in possible_keys:
            if key in normalized_row:
                value = normalized_row[key].strip()
                break
        
        if value:
            if field == 'duration':
                trip[field] = extract_duration(value)
            elif field == 'credit_hours':
                trip[field] = extract_credit_hours(value)
            elif field == 'includes_weekend':
                trip[field] = parse_weekend_indicator(value)
            else:
                trip[field] = value
    
    # Determine weekend status from dates if not explicitly provided
    if 'includes_weekend' not in trip and 'dates' in trip:
        trip['includes_weekend'] = check_weekend_from_dates(trip['dates'])
    
    # Only return trip if we have at least an ID
    if 'id' in trip:
        # Set defaults for missing fields
        trip.setdefault('duration', 0)
        trip.setdefault('dates', 'Unknown')
        trip.setdefault('routing', 'Unknown')
        trip.setdefault('credit_hours', 0.0)
        trip.setdefault('includes_weekend', False)
        return trip
    
    return {}


def parse_schedule_text(text: str) -> List[Dict[str, Any]]:
    """Parse schedule from plain text using pattern matching"""
    trips = []
    
    # Split text into lines for processing
    lines = text.split('\n')
    
    # Patterns to match trip information
    trip_patterns = [
        # Pattern for trip lines like "Trip 123: 3 days, Jan 15-17, DFW-LAX-DFW, 12.5 hrs"
        r'(?:trip|pairing|sequence)\s*(\w+)[:;,]?\s*(\d+)\s*days?\s*,?\s*([^,]+?)\s*,?\s*([^,]+?)\s*,?\s*([\d.]+)\s*(?:hrs?|hours?)',
        # Pattern for tabular data
        r'(\w+)\s+(\d+)\s+([^\s]+(?:\s+[^\s]+)*?)\s+([^\s]+(?:\s+[^\s]+)*?)\s+([\d.]+)',
    ]
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        for pattern in trip_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                try:
                    trip_id = match.group(1)
                    duration = int(match.group(2))
                    dates = match.group(3).strip()
                    routing = match.group(4).strip()
                    credit_hours = float(match.group(5))
                    
                    trip = {
                        'id': trip_id,
                        'duration': duration,
                        'dates': dates,
                        'routing': routing,
                        'credit_hours': credit_hours,
                        'includes_weekend': check_weekend_from_dates(dates)
                    }
                    trips.append(trip)
                    break
                except (ValueError, IndexError):
                    continue
    
    # If no patterns matched, try to extract basic information
    if not trips:
        # Look for any numbers that might be trip IDs
        trip_ids = re.findall(r'\b\d{2,4}\b', text)
        for i, trip_id in enumerate(trip_ids[:10]):  # Limit to first 10 potential trips
            trips.append({
                'id': trip_id,
                'duration': 0,
                'dates': 'Unknown',
                'routing': 'Unknown',
                'credit_hours': 0.0,
                'includes_weekend': False
            })
    
    return trips


def extract_duration(value: str) -> int:
    """Extract duration in days from string"""
    # Look for numbers followed by 'day' or 'd'
    match = re.search(r'(\d+)\s*(?:days?|d)', value, re.IGNORECASE)
    if match:
        return int(match.group(1))
    
    # Try to extract any number
    match = re.search(r'(\d+)', value)
    if match:
        return int(match.group(1))
    
    return 0


def extract_credit_hours(value: str) -> float:
    """Extract credit hours from string"""
    # Look for decimal numbers
    match = re.search(r'([\d.]+)', value)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    
    return 0.0


def parse_weekend_indicator(value: str) -> bool:
    """Parse weekend indicator from string"""
    value = value.lower().strip()
    true_indicators = ['yes', 'true', '1', 'y', 'weekend', 'sat', 'sun']
    return any(indicator in value for indicator in true_indicators)


def check_weekend_from_dates(dates_str: str) -> bool:
    """Check if date range includes weekend"""
    # Look for weekend indicators in the date string
    weekend_indicators = ['sat', 'sun', 'saturday', 'sunday', 'weekend']
    dates_lower = dates_str.lower()
    
    if any(indicator in dates_lower for indicator in weekend_indicators):
        return True
    
    # Try to parse date ranges and check if they span weekend
    try:
        # Common date patterns
        date_patterns = [
            r'(\d{1,2})/(\d{1,2})',  # MM/DD
            r'(\d{1,2})-(\d{1,2})',  # MM-DD
            r'(\w{3})\s*(\d{1,2})',  # Jan 15
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, dates_str)
            if matches:
                for match in matches:
                    try:
                        if pattern == r'(\w{3})\s*(\d{1,2})':
                            # Handle month name + day
                            month_names = {
                                'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
                                'may': 5, 'jun': 6, 'jul': 7, 'aug': 8,
                                'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                            }
                            month = month_names.get(match[0].lower(), 1)
                            day = int(match[1])
                        else:
                            month, day = int(match[0]), int(match[1])
                        
                        # Use current year for simplicity
                        date_obj = datetime(2024, month, day)
                        dates.append(date_obj)
                    except (ValueError, KeyError):
                        continue
        
        # If we have dates, check if any fall on weekend
        for date_obj in dates:
            if date_obj.weekday() >= 5:  # Saturday = 5, Sunday = 6
                return True
                
    except Exception:
        pass
    
    return False
