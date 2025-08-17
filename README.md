# VectorBid

## VectorBid FastAPI (v0.3) — Quickstart

Run (dev):
  pip install -r requirements-dev.txt
  scripts/dev_run.sh
  # http://localhost:8000/health
  # http://localhost:8000/docs

Endpoints:
  GET /health, GET /schemas
  POST /parse_preferences, /validate, /optimize, /strategy, /generate_layers, /lint

Tests:
  PYTHONPATH=. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -c pytest.ini

Legacy:
  Mounted at /legacy if WSGI app importable; else shim at /legacy/health

Benchmark helper:
  PYTHONPATH=. python scripts/bench_10k.py

## Optimizer Scoring

### Scoring Factors

The optimizer ranks candidate pairings using a weighted sum of:

- **award_rate** – historical award likelihood for a layover city.
- **layovers** – preference score for layover cities (1.0 prefer, 0.5 neutral, 0.0 avoid).

### Persona Weights

Default weights assign equal importance to all factors. Personas adjust these weights:

| Persona | Adjustments |
| ------- | ----------- |
| family_first | layovers ×1.2 |
| money_maker | award_rate ×1.2 |
| commuter_friendly | layovers ×1.1 |
| quality_of_life | layovers ×1.1 |
| reserve_avoider | (no change) |
| adventure_seeker | layovers ×1.2 |

Weights are normalized so contributions sum to 1.0.

### Seniority Adjustment

Scores are multiplied by:

```
0.9 + 0.2 * seniority_percentile
```

The percentile is clamped between 0 and 1.

### Example Optimize Request

```json
POST /optimize
{
  "feature_bundle": {
    "context": {
      "ctx_id": "ctx-u1",
      "pilot_id": "u1",
      "airline": "UAL",
      "base": "EWR",
      "seat": "FO",
      "equip": ["73G"],
      "seniority_percentile": 0.5,
      "default_weights": {"layovers": 1.0}
    },
    "preference_schema": {
      "pilot_id": "u1",
      "airline": "UAL",
      "base": "EWR",
      "seat": "FO",
      "equip": ["73G"],
      "soft_prefs": {"layovers": {"prefer": ["SAN", "SJU"], "weight": 1.0}}
    },
    "analytics_features": {
      "base_stats": {
        "SAN": {"award_rate": 0.65},
        "SJU": {"award_rate": 0.55}
      }
    },
    "compliance_flags": {},
    "pairing_features": {
      "pairings": [
        {"id": "P1", "layover_city": "SAN"},
        {"id": "P2", "layover_city": "SJU"}
      ]
    }
  },
  "K": 5
}
```

### Example Optimize Response

```json
{
  "candidates": [
    {
      "candidate_id": "P1",
      "score": 0.82,
      "hard_ok": true,
      "soft_breakdown": {"award_rate": 0.33, "layovers": 0.49},
      "pairings": [],
      "rationale": ["layovers contributed 0.49", "award_rate contributed 0.33"]
    }
  ]
}
```

Scores and rationale vary with input data.

### Configuration

Required environment variables for development and optimizer usage:

- `VECTORBID_API_KEY` – protects `/export` and other admin endpoints.
- `OPENAI_API_KEY` – enables GPT-based ranking; without it the fallback model is used.
- `EXPORT_DIR` – directory where `/export` writes files (default `exports`).
- `PORT` – development server port (default `8000`).

## Security

Admin bearer tokens are never written to logs in clear text. Only the first
six characters plus a short hash are recorded, preventing exposure of the full
token while still allowing basic traceability.
