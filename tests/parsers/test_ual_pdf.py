import pytest

from app.parsers.ual_pdf import parse_bid_pdf, _parse_trip_block

FIXTURES = [
    "tests/fixtures/bid_packages/202508_first.txt",
    "tests/fixtures/bid_packages/bid_package1_first.txt",
    "tests/fixtures/bid_packages/fuzzy.txt",
]


@pytest.mark.parametrize("path", FIXTURES)
def test_parse_bid_pdf(path):
    trips = parse_bid_pdf(path)
    assert trips, "expected trips from %s" % path
    first = trips[0]
    assert first.trip_id == "H5001"
    assert pytest.approx(first.credit, rel=1e-2) == 5.38
    assert first.legs[0].departure_airport == "IAH"
    assert first.legs[0].arrival_airport == "ORD"


def test_month_rollover_and_timezone():
    block = (
        "EFF 12/31/24 THRU 01/01/25 ID H9999\n"
        "73G 100 IAH LAX 2300 0050\n"
        "73G 101 LAX IAH 0130 0700\n"
        "CRD- 10.00"
    )
    trip = _parse_trip_block(block)
    assert trip.trip_id == "H9999"
    leg1, leg2 = trip.legs
    assert leg1.arrival.day == 1
    assert leg2.departure.day == 1
    assert leg2.arrival.day == 1
    # timezone awareness
    assert leg1.departure.tzinfo is not None
    assert leg1.arrival.tzinfo is not None
