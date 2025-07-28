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
        List of trip dictionaries with keys: trip_id, days, dates, routing, credit_hours, includes_weekend
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
    """Parse PDF schedule using PyMuPDF with improved airline format detection"""
    if fitz is None:
        raise ImportError("PyMuPDF is required for PDF parsing")
    
    trips = []
    
    try:
        doc = fitz.open(file_path)
        all_text = ""
        
        # Extract text from all pages
        for page_num in range(len(doc)):
            page = doc[page_num]
            try:
                # Try the standard PyMuPDF method
                page_text = page.get_text()
            except (AttributeError, TypeError):
                try:
                    # Fallback for different PyMuPDF versions
                    page_text = page.getText() if hasattr(page, 'getText') else ""
                except:
                    page_text = ""
            all_text += page_text + "\n"
        
        doc.close()
        
        # Parse the extracted text with enhanced airline format detection
        trips = parse_airline_schedule_text(all_text)
        
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
        
        return parse_airline_schedule_text(text)
        
    except Exception as e:
        raise Exception(f"Failed to parse text file: {str(e)}")


def extract_trip_from_row(row: Dict[str, str]) -> Dict[str, Any]:
    """Extract trip information from a CSV row"""
    trip = {}
    
    # Map common CSV column names to our fields
    field_mappings = {
        'trip_id': ['id', 'trip_id', 'tripid', 'trip id', 'number', 'trip_number'],
        'days': ['duration', 'days', 'length', 'trip_length'],
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
            if field == 'days':
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
    if 'trip_id' in trip:
        # Set defaults for missing fields
        trip.setdefault('days', 0)
        trip.setdefault('dates', 'Unknown')
        trip.setdefault('routing', 'Unknown')
        trip.setdefault('credit_hours', 0.0)
        trip.setdefault('includes_weekend', False)
        return trip
    
    return {}


def parse_airline_schedule_text(text: str) -> List[Dict[str, Any]]:
    """Parse airline schedule text with enhanced pattern recognition for real bid packages"""
    trips = []
    
    # Keep original text for block extraction (preserve line structure)
    original_text = text
    lines = text.split('\n')
    
    # Enhanced patterns for airline bid packages
    trip_patterns = [
        # United Airlines style: "Trip 105" "4-Day Trip" "IAH-SFO-IAH" "18:30"
        r'(?:trip|pairing|sequence)\s*(\d+).*?(\d+)[-\s]*day.*?([A-Z]{3}(?:[-\s]*[A-Z]{3})+).*?(\d{1,2}:\d{2})',
        
        # Alternative format: "105" "4 Day" "12NOV-15NOV" "IAH-SFO-IAH" "18:30"
        r'(\d{2,4})\s+(\d+)\s*day.*?(\d{1,2}[A-Z]{3}[-\s]*\d{1,2}[A-Z]{3}).*?([A-Z]{3}(?:[-\s]*[A-Z]{3})+).*?(\d{1,2}:\d{2})',
        
        # Compact format: "105 4D IAH-SFO-IAH 18:30"
        r'(\d{2,4})\s+(\d+)D?\s+([A-Z]{3}(?:[-\s]*[A-Z]{3})+)\s+(\d{1,2}:\d{2})',
        
        # Date range format: "Trip 105: 12NOV - 15NOV, IAH-SFO-IAH, 18:30"
        r'(?:trip|pairing)\s*(\d+).*?(\d{1,2}[A-Z]{3}\s*[-\s]+\s*\d{1,2}[A-Z]{3}).*?([A-Z]{3}(?:[-\s]*[A-Z]{3})+).*?(\d{1,2}:\d{2})',
        
        # Tabular format with possible multi-line breaks
        r'(\d{2,4})\s+.*?(\d+)[-\s]*(?:day|d)\s+.*?([A-Z]{3}(?:[-\s]*[A-Z]{3})+).*?(\d{1,2}:\d{2})',
    ]
    
    # Try to find trip blocks in the text (use original text with line structure)
    trip_blocks = extract_trip_blocks(original_text)
    
    for block in trip_blocks:
        trip = parse_trip_block(block)
        if trip and trip.get('trip_id') and trip.get('trip_id') != 'Unknown':
            trips.append(trip)
    
    # If no trips found from blocks, try line-by-line parsing with patterns
    if not trips:
        # For pattern matching, use normalized text
        normalized_text = re.sub(r'\s+', ' ', text)
        trips = parse_lines_with_patterns([normalized_text], trip_patterns)
    
    # Final fallback: extract basic trip IDs and try to find associated data
    if not trips:
        trips = extract_basic_trips(original_text)
    
    return trips


def extract_trip_blocks(text: str) -> List[str]:
    """Extract individual trip blocks from the text"""
    blocks = []
    
    # Look for trip separators or headers
    trip_separators = [
        r'(?:^|\n)\s*(?:trip|pairing|sequence)\s*\d+',
        r'(?:^|\n)\s*\d{2,4}\s+(?:\d+[-\s]*day|\d+D)',
        r'(?:^|\n)\s*\d{2,4}\s+.*?[A-Z]{3}',
    ]
    
    # Try to split text by trip indicators
    for separator_pattern in trip_separators:
        matches = list(re.finditer(separator_pattern, text, re.IGNORECASE | re.MULTILINE))
        if len(matches) >= 1:  # Changed from > 1 to >= 1
            for i, match in enumerate(matches):
                start = match.start()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                block = text[start:end].strip()
                if len(block) > 10:  # Minimum block size
                    blocks.append(block)
            break
    
    # If no blocks found with separators, try to extract based on "Trip XXX" patterns
    if not blocks:
        lines = text.split('\n')
        current_block = []
        in_trip = False
        
        for line in lines:
            line = line.strip()
            # Check if this line starts a new trip
            if re.match(r'trip\s+\d+', line, re.IGNORECASE):
                # Save previous block if exists
                if current_block:
                    blocks.append('\n'.join(current_block))
                # Start new block
                current_block = [line]
                in_trip = True
            elif in_trip and line:
                # Add line to current trip block
                current_block.append(line)
            elif in_trip and not line:
                # Empty line might signal end of trip, but continue for now
                current_block.append(line)
        
        # Don't forget the last block
        if current_block:
            blocks.append('\n'.join(current_block))
    
    return blocks


def parse_trip_block(block: str) -> Dict[str, Any]:
    """Parse an individual trip block to extract trip information"""
    trip = {}
    
    # Extract trip ID
    trip_id_match = re.search(r'(?:trip|pairing|sequence)\s*(\d+)|^(\d{2,4})', block, re.IGNORECASE)
    if trip_id_match:
        trip['trip_id'] = trip_id_match.group(1) or trip_id_match.group(2)
    
    # Extract duration/days - look for patterns like "4-Day Trip" or date ranges
    duration_patterns = [
        r'(\d+)[-\s]*day',
        r'(\d+)D\b',
        r'(\d{1,2}[A-Z]{3})\s*[-–\s]+\s*(\d{1,2}[A-Z]{3})',  # Date range like 12NOV - 15NOV
    ]
    
    for pattern in duration_patterns:
        duration_match = re.search(pattern, block, re.IGNORECASE)
        if duration_match:
            if len(duration_match.groups()) == 1:
                trip['days'] = int(duration_match.group(1))
            else:
                # Calculate duration from date range
                start_date, end_date = duration_match.groups()
                trip['days'] = calculate_duration_from_dates(start_date, end_date)
                trip['dates'] = f"{start_date} – {end_date}"
            break
    
    # Extract routing (airport codes) - look for patterns like IAH-SFO-IAH
    # Need to be careful not to match date patterns like "12NOV"
    routing_patterns = [
        r'\b([A-Z]{3}(?:[-\s]*[A-Z]{3}){1,4})\b',  # Standard format like IAH-SFO-IAH (1-5 airports)
    ]
    
    for pattern in routing_patterns:
        # Find all potential routing matches
        routing_matches = re.findall(pattern, block)
        for potential_routing in routing_matches:
            # Filter out matches that contain date patterns
            if not re.search(r'\d+[A-Z]{3}', potential_routing):
                routing = potential_routing
                # Clean up routing format
                routing = re.sub(r'[-\s]+', '-', routing)
                trip['routing'] = routing
                break
        if 'routing' in trip:
            break
    
    # Extract credit hours - look for patterns like 18:30, "Credit 18:30", etc.
    credit_patterns = [
        r'(?:credit\s*)?(\d{1,2}):(\d{2})',  # "Credit 18:30" or just "18:30"
        r'credit\s*hours?\s*(\d{1,2}):(\d{2})',  # "Credit Hours 18:30"
        r'(\d{1,2}):(\d{2})\s*(?:credit|hrs?)',  # "18:30 credit"
    ]
    
    for pattern in credit_patterns:
        credit_match = re.search(pattern, block, re.IGNORECASE)
        if credit_match:
            hours = int(credit_match.group(1))
            minutes = int(credit_match.group(2))
            trip['credit_hours'] = hours + (minutes / 60.0)
            break
    
    # Extract dates if not already found - also handle en-dash and other variations
    if 'dates' not in trip:
        date_patterns = [
            r'(\d{1,2}[A-Z]{3})\s*[-–\s]+\s*(\d{1,2}[A-Z]{3})',  # Standard date range
            r'(\d{1,2}[A-Z]{3})\s*-\s*(\d{1,2}[A-Z]{3})',  # Hyphen separated
            r'(\d{1,2}[A-Z]{3})\s+(\d{1,2}[A-Z]{3})',  # Space separated
        ]
        
        for pattern in date_patterns:
            date_match = re.search(pattern, block)
            if date_match:
                start_date, end_date = date_match.groups()
                trip['dates'] = f"{start_date} – {end_date}"
                # Also calculate duration if not already set
                if 'days' not in trip:
                    trip['days'] = calculate_duration_from_dates(start_date, end_date)
                break
    
    # Check for weekend inclusion
    if 'dates' in trip:
        trip['includes_weekend'] = check_weekend_from_dates(trip['dates'])
    else:
        # Look for weekend indicators in the block
        weekend_indicators = ['sat', 'sun', 'weekend', 'sat/sun']
        trip['includes_weekend'] = any(indicator in block.lower() for indicator in weekend_indicators)
    
    # Set defaults for missing fields using the correct field names
    trip.setdefault('trip_id', 'Unknown')
    trip.setdefault('days', 0)
    trip.setdefault('dates', 'Unknown')
    trip.setdefault('routing', 'Unknown')
    trip.setdefault('credit_hours', 0.0)
    trip.setdefault('includes_weekend', False)
    
    return trip


def parse_lines_with_patterns(lines: List[str], patterns: List[str]) -> List[Dict[str, Any]]:
    """Parse lines using regex patterns"""
    trips = []
    
    for line in lines:
        line = line.strip()
        if len(line) < 10:  # Skip very short lines
            continue
            
        for pattern in patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                try:
                    groups = match.groups()
                    
                    dates = 'Unknown'  # Default value
                    
                    if len(groups) == 4:  # trip_id, duration, routing, credit_hours
                        trip_id, duration_str, routing, credit_time = groups
                        duration = extract_duration_from_string(duration_str)
                    elif len(groups) == 5:  # trip_id, duration, dates, routing, credit_hours
                        trip_id, duration_str, dates, routing, credit_time = groups
                        duration = extract_duration_from_string(duration_str)
                    else:
                        continue
                    
                    # Parse credit hours
                    credit_hours = parse_credit_time(credit_time)
                    
                    trip = {
                        'trip_id': trip_id,
                        'days': duration,
                        'dates': dates,
                        'routing': routing.strip(),
                        'credit_hours': credit_hours,
                        'includes_weekend': check_weekend_from_dates(dates)
                    }
                    trips.append(trip)
                    break
                    
                except (ValueError, IndexError):
                    continue
    
    return trips


def extract_basic_trips(text: str) -> List[Dict[str, Any]]:
    """Extract basic trip information as fallback"""
    trips = []
    
    # Look for potential trip IDs (2-4 digit numbers)
    trip_ids = re.findall(r'\b(\d{2,4})\b', text)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_trip_ids = []
    for trip_id in trip_ids:
        if trip_id not in seen:
            seen.add(trip_id)
            unique_trip_ids.append(trip_id)
    
    # Limit to reasonable number of trips
    for trip_id in unique_trip_ids[:20]:
        trips.append({
            'trip_id': trip_id,
            'days': 0,
            'dates': 'Unknown',
            'routing': 'Unknown',
            'credit_hours': 0.0,
            'includes_weekend': False
        })
    
    return trips


def calculate_duration_from_dates(start_date: str, end_date: str) -> int:
    """Calculate trip duration from date strings like '12NOV' and '15NOV'"""
    try:
        # Extract day numbers
        start_match = re.search(r'(\d+)', start_date)
        end_match = re.search(r'(\d+)', end_date)
        
        if start_match and end_match:
            start_day = int(start_match.group(1))
            end_day = int(end_match.group(1))
            
            # Simple calculation assuming same month
            duration = end_day - start_day + 1
            return max(1, duration)
    except:
        pass
    return 1


def extract_duration_from_string(duration_str: str) -> int:
    """Extract duration from various string formats"""
    # Look for numbers followed by 'day' or 'd'
    match = re.search(r'(\d+)', duration_str)
    if match:
        return int(match.group(1))
    return 0


def parse_credit_time(credit_time: str) -> float:
    """Parse credit time in HH:MM format to decimal hours"""
    try:
        if ':' in credit_time:
            hours, minutes = credit_time.split(':')
            return int(hours) + (int(minutes) / 60.0)
        else:
            return float(credit_time)
    except:
        return 0.0


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
