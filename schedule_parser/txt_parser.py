import re, io

_LINE = re.compile(
    r"^(?P<id>\d{3,4})\s+(?P<days>\d)-Day.*?(?P<credit>\d+\.\d{2})")


def parse_txt(blob: bytes) -> list[dict]:
    trips = []
    for line in io.StringIO(blob.decode("utf-8", "ignore")):
        m = _LINE.match(line)
        if m:
            trips.append({
                "id": m["id"],
                "days": int(m["days"]),
                "credit": float(m["credit"]),
                "raw": line.rstrip(),
            })
    if not trips:
        raise RuntimeError("TXT parse produced zero trips")
    return trips
