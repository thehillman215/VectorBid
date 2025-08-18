import csv
import io


def parse_csv(blob: bytes) -> list[dict]:
    trips = []
    text = blob.decode("utf-8", "ignore")

    try:
        reader = csv.DictReader(io.StringIO(text))

        for row in reader:
            # Try multiple column name variations
            trip_id = _get_field(
                row,
                ["TripID", "Trip", "ID", "trip_id", "trip", "id", "Trip ID", "Pairing"],
            )
            days = _get_field(row, ["Days", "days", "Duration", "duration", "Length", "Trip Days"])
            credit = _get_field(
                row,
                ["Credit", "credit", "Hours", "hours", "Credit Hours", "Flight Hours"],
            )

            if trip_id:
                try:
                    trip = {
                        "trip_id": str(trip_id).strip(),
                        "days": int(float(days)) if days else 1,
                        "credit_hours": float(credit) if credit else 0.0,
                        "includes_weekend": _detect_weekend_csv(row),
                        "routing": _get_field(
                            row, ["Routing", "routing", "Route", "route", "Cities"]
                        )
                        or "",
                        "raw": dict(row),
                    }
                    trips.append(trip)
                except (ValueError, TypeError):
                    continue

    except Exception as e:
        raise RuntimeError(f"CSV parsing failed: {e}") from e

    if not trips:
        raise RuntimeError("CSV contained no trips / header mismatch")

    return trips


def _get_field(row, field_names):
    """Get field value trying multiple possible column names."""
    for field in field_names:
        if field in row and row[field] and str(row[field]).strip():
            return str(row[field]).strip()
    return None


def _detect_weekend_csv(row):
    """Detect weekend from CSV row data."""
    weekend_fields = ["Weekend", "weekend", "includes_weekend", "Weekend Work"]

    for field in weekend_fields:
        if field in row and row[field]:
            val = str(row[field]).lower().strip()
            if val in ["true", "1", "yes", "y"]:
                return True
            elif val in ["false", "0", "no", "n"]:
                return False

    # Check for weekend indicators in other fields
    for value in row.values():
        if value and isinstance(value, str):
            if any(day in value.lower() for day in ["sat", "sun", "weekend"]):
                return True

    return False
