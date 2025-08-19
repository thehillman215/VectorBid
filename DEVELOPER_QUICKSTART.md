# Developer Quickstart

Get VectorBid running locally in minutes.

## 1. Clone the repo
```bash
git clone https://github.com/VectorPilot/VectorBid.git
cd VectorBid
```

## 2. Create a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

## 3. Run the FastAPI server
```bash
uvicorn app.main:app --reload
```
Visit http://127.0.0.1:8000/docs to explore the API.

## 4. Run the test suite
```bash
pytest -q
```

## 5. Try an endpoint
With the server running:
```bash
curl http://127.0.0.1:8000/api/personas
```

