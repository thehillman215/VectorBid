import json
from pathlib import Path

from fastapi import APIRouter

from app.models import FAQItem

router = APIRouter()

FAQ_PATH = Path(__file__).resolve().parent.parent / "content" / "faq.en.json"
with FAQ_PATH.open("r", encoding="utf-8") as f:
    _FAQ_ITEMS: list[FAQItem] = [FAQItem(**item) for item in json.load(f)]


@router.get("/faq", response_model=list[FAQItem])
def get_faq(query: str | None = None) -> list[FAQItem]:
    items = _FAQ_ITEMS
    if query:
        q = query.lower()
        items = [
            item
            for item in _FAQ_ITEMS
            if q in item.question.lower() or q in item.answer.lower()
        ]
    return items
