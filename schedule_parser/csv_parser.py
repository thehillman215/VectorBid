import csv, io


def parse_csv(blob: bytes) -> list[dict]:
    trips = []
    reader = csv.DictReader(io.StringIO(blob.decode("utf-8", "ignore")))
    for row in reader:
        trips.append({
            "id": row.get("TripID") or row.get("Trip") or row.get("ID"),
            "days": int(row.get("Days") or 0),
            "credit": float(row.get("Credit", 0)),
            "raw": row,
        })
    if not trips:
        raise RuntimeError("CSV contained no trips / header mismatch")
    return trips
