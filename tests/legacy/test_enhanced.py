import re


def test_table_format():
    """Test the table format that was failing"""

    sample_text = """UNITED AIRLINES PILOT BID PACKAGE - FEBRUARY 2025
Base: DEN  Equipment: 737  Position: FO

Trip   Days  Routing           Credit  Dates
UA123  3DAY  DEN-LAX-DEN     18:30   15FEB-17FEB
UA456  4DAY  DEN-LHR-FRA-DEN 25:12   20FEB-23FEB SAT
UA789  2DAY  DEN-PHX-DEN     12:00   25FEB-26FEB
202 1DAY DEN-ORD-DEN 06:45 10MAR-10MAR"""

    print("🔍 Testing Table Format Parsing...")

    # Enhanced patterns for table format
    patterns = [
        # Table format: UA123  3DAY  DEN-LAX-DEN     18:30   15FEB-17FEB
        re.compile(r'(?P<trip_id>UA\d+)\s+(?P<days>\d+)DAY\s+(?P<routing>[A-Z]{3}(?:-[A-Z]{3})+)\s+(?P<credit>\d+[:\.]?\d+)\s+(?P<dates>\S+)'),
        # Numeric format: 202 1DAY DEN-ORD-DEN 06:45 10MAR-10MAR
        re.compile(r'(?P<trip_id>\d+)\s+(?P<days>\d+)DAY\s+(?P<routing>[A-Z]{3}(?:-[A-Z]{3})+)\s+(?P<credit>\d+[:\.]?\d+)\s+(?P<dates>\S+)'),
    ]

    trips = []
    lines = sample_text.split('\n')

    for line_num, line in enumerate(lines, 1):
        line = line.strip()

        # Skip headers and empty lines
        if not line or len(line) < 8:
            continue
        if any(skip in line.upper() for skip in ['UNITED AIRLINES', 'BASE:', 'TRIP   DAYS', 'PILOT BID']):
            print(f"  Line {line_num}: SKIP - {line[:30]}...")
            continue

        # Try patterns
        for pattern in patterns:
            match = pattern.search(line)
            if match:
                groups = match.groupdict()
                trip_id = groups['trip_id']
                if not trip_id.startswith('UA'):
                    trip_id = f"UA{trip_id}"

                days = int(groups['days'])
                credit = float(groups['credit'].replace(':', '.'))
                routing = groups['routing']
                dates = groups['dates']

                trip = {
                    'trip_id': trip_id,
                    'days': days,
                    'credit_hours': credit,
                    'routing': routing,
                    'dates': dates
                }
                trips.append(trip)
                print(f"  Line {line_num}: ✅ {trip_id} - {days}d, {credit}h, {routing}")
                break
        else:
            if any(c.isdigit() for c in line):
                print(f"  Line {line_num}: ❌ No match - {line}")

    print(f"\n✅ Parsed {len(trips)} trips from table format!")
    return trips

if __name__ == "__main__":
    test_table_format()
