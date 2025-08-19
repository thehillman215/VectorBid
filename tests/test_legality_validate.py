from app.legality import validate


def test_min_days_off_rule() -> None:
    trips: list[dict] = []
    context_ok = {"days_off": 10}
    report_ok = validate(trips, context_ok)
    assert not any(hit.id == "MIN_DAYS_OFF" for hit in report_ok.rule_hits)

    context_bad = {"days_off": 4}
    report_bad = validate(trips, context_bad)
    assert any(hit.id == "MIN_DAYS_OFF" for hit in report_bad.rule_hits)


def test_max_duty_hours_rule() -> None:
    trips = [
        {
            "id": "T1",
            "duty_hours": 10,
            "flight_time": 5,
            "rest_hours": 11,
            "break_minutes": 40,
        },
        {
            "id": "T2",
            "duty_hours": 13,
            "flight_time": 5,
            "rest_hours": 11,
            "break_minutes": 40,
        },
    ]
    context = {
        "max_duty_hours": 12,
        "max_flight_time": 8,
        "min_rest_hours": 10,
        "days_off": 10,
    }
    report = validate(trips, context)
    assert {t["id"] for t in report.valid_trips} == {"T1"}
    assert any(hit.id == "MAX_DUTY_HOURS" and hit.trip_id == "T2" for hit in report.rule_hits)


def test_max_flight_time_rule() -> None:
    trips = [
        {
            "id": "T1",
            "duty_hours": 10,
            "flight_time": 7,
            "rest_hours": 11,
            "break_minutes": 40,
        },
        {
            "id": "T2",
            "duty_hours": 10,
            "flight_time": 9,
            "rest_hours": 11,
            "break_minutes": 40,
        },
    ]
    context = {
        "max_duty_hours": 12,
        "max_flight_time": 8,
        "min_rest_hours": 10,
        "days_off": 10,
    }
    report = validate(trips, context)
    assert {t["id"] for t in report.valid_trips} == {"T1"}
    assert any(hit.id == "MAX_FLIGHT_TIME" and hit.trip_id == "T2" for hit in report.rule_hits)


def test_min_rest_hours_rule() -> None:
    trips = [
        {
            "id": "T1",
            "duty_hours": 10,
            "flight_time": 5,
            "rest_hours": 11,
            "break_minutes": 40,
        },
        {
            "id": "T2",
            "duty_hours": 10,
            "flight_time": 5,
            "rest_hours": 8,
            "break_minutes": 40,
        },
    ]
    context = {
        "max_duty_hours": 12,
        "max_flight_time": 8,
        "min_rest_hours": 10,
        "days_off": 10,
    }
    report = validate(trips, context)
    assert {t["id"] for t in report.valid_trips} == {"T1"}
    assert any(hit.id == "MIN_REST_HOURS" and hit.trip_id == "T2" for hit in report.rule_hits)


def test_min_break_minutes_rule() -> None:
    trips = [
        {
            "id": "T1",
            "duty_hours": 10,
            "flight_time": 5,
            "rest_hours": 11,
            "break_minutes": 40,
        },
        {
            "id": "T2",
            "duty_hours": 10,
            "flight_time": 5,
            "rest_hours": 11,
            "break_minutes": 20,
        },
    ]
    context = {
        "max_duty_hours": 12,
        "max_flight_time": 8,
        "min_rest_hours": 10,
        "days_off": 10,
    }
    report = validate(trips, context)
    assert {t["id"] for t in report.valid_trips} == {"T1"}
    assert any(hit.id == "MIN_BREAK_MINUTES" and hit.trip_id == "T2" for hit in report.rule_hits)
