import re, io

_TRIP_RE = re.compile(
    r"(?P<id>\d{3,4})\s+"
    r"(?P<days>\d)-Day.*?"
    r"(?P<credit>\d{1,2}\.\d{2})\s+Cred", re.S)


def parse_pdf(blob: bytes) -> list[dict]:
    import fitz  # PyMuPDF imported only when needed
    trips: list[dict] = []
    with fitz.open(stream=blob, filetype="pdf") as pdf:
        text = "\n".join(page.get_text() for page in pdf)  # type: ignore
    for m in _TRIP_RE.finditer(text):
        trips.append({
            "id": m["id"],
            "days": int(m["days"]),
            "credit": float(m["credit"]),
            "raw": m.group(0).strip(),
        })
    if not trips:
        raise RuntimeError("No trips parsed from PDF")
    return trips
