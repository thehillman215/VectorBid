from schedule_parser import parse_schedule


def test_csv_happy_path():
    sample = b"TripID,Days,Credit\n1234,3,18.50\n5678,2,12.25\n"
    result = parse_schedule(sample, "sample.csv")
    ids = [t["id"] for t in result]
    assert ids == ["1234", "5678"]
