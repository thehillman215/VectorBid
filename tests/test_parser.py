from schedule_parser import parse_schedule


def test_csv_happy_path():
    sample = b"TripID,Days,Credit\n1234,3,18.50\n5678,2,12.25\n"
    result = parse_schedule(sample, "sample.csv")

    assert len(result) == 2
    assert result[0]["days"] == 3
    assert result[0]["credit"] == 18.50
    assert result[1]["days"] == 2
    assert result[1]["credit"] == 12.25

    ids = [t["id"] for t in result]
    assert ids == ["1234", "5678"]
