# VectorBid Architecture

VectorBid is an AI-powered bidding assistant for airline pilots. It converts natural language pilot preferences into optimized PBS 2.0 bid layers, validated against FAR 117 and union agreements.

## System Overview
- **Backend**: FastAPI monolith (Python 3.11), containerized via Docker.
- **Frontend**: Single-page app (React).
- **Pipeline**:
  1. **Input Enrichment** — pilot profile (aircraft, base, seniority) fused with contract and FAR data.
  2. **Parallel Processing** — NLP parsing, rule compliance, and analytics in parallel.
  3. **Data Fusion Layer** — combines signals into structured artifacts.
  4. **LLM Strategy Layer** — GPT-4 generates bid strategy and rationales.
  5. **Output** — PBS 2.0 compatible bid layers and filters.

## Deployment
- Hosted via GHCR-built Docker images.
- CI/CD through GitHub Actions (lint, tests, security scan, build, push).