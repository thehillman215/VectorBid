import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.models import FAQItem
from app.routes.faq import router as faq_router

app = FastAPI()
app.include_router(faq_router)
client = TestClient(app)


def test_faq_model_validation() -> None:
    item = FAQItem(id="x", question="q", answer="a")
    assert item.model_dump()["id"] == "x"
    with pytest.raises(ValidationError):
        FAQItem(question="q", answer="a")


def test_faq_no_query_returns_all() -> None:
    resp = client.get("/faq")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3


def test_faq_query_filters() -> None:
    resp = client.get("/faq", params={"query": "VectorBid"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == "bidding"
