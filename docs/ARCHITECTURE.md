# VectorBid Architecture

VectorBid is an AI-powered bidding assistant for airline pilots. It converts natural language pilot preferences into optimized bid layers, validated against FAR 117 and union agreements.

## System Overview
- **Backend**: FastAPI monolith (Python 3.11), containerized via Docker.
- **Frontend**: Single-page app (React).
- **Pipeline**:
  1. **Input Enrichment** — pilot profile (aircraft, base, seniority) fused with contract and FAR data.
  2. **Parallel Processing** — NLP parsing, rule compliance, and analytics in parallel.
  3. **Data Fusion Layer** — combines signals into structured artifacts.
  4. **LLM Strategy Layer** — GPT-4 generates bid strategy and rationales.
  5. **Output** — PBS compatible bid layers and filters.

## Data Flow Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Frontend  │───▶│     API     │───▶│   NLP/      │───▶│ Optimizer   │
│  (React)   │    │  (FastAPI)  │    │   Rules     │    │  Engine     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                           │                   │                   │
                           ▼                   ▼                   ▼
                    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
                    │   Context   │    │  Rule       │    │  Strategy   │
                    │ Enrichment  │    │  Packs      │    │  Generation │
                    └─────────────┘    └─────────────┘    └─────────────┘
                           │                   │                   │
                           ▼                   ▼                   ▼
                    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
                    │   Data      │    │  Validation │    │   Bid       │
                    │  Fusion     │    │  Engine     │    │  Layers     │
                    └─────────────┘    └─────────────┘    └─────────────┘
                           │                   │                   │
                           ▼                   ▼                   ▼
                    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
                    │   LLM       │    │  Analytics  │    │   Export    │
                    │  Service    │    │  & Scoring  │    │   Storage   │
                    └─────────────┘    └─────────────┘    └─────────────┘
```

## Core Components

### 1. Input Layer
- **Pilot Profile**: Aircraft type, base, seniority, preferences
- **Contract Data**: Airline-specific rules, pay scales, work rules
- **FAR 117 Compliance**: Federal Aviation Regulations validation

### 2. Processing Pipeline
- **Parse**: Natural language preference parsing via LLM
- **Validate**: Rule compliance checking against contract + FAR
- **Optimize**: Multi-objective optimization for bid layers
- **Generate**: PBS compatible bid layer creation
- **Lint**: Quality assurance and validation

### 3. Data Models
- **PreferenceSchema**: Structured pilot preferences
- **ContextSnapshot**: Current operational context
- **BidLayerArtifact**: Generated bid layer with metadata
- **StrategyDirectives**: Optimization strategy parameters

### 4. Rule Engine
- **Rule Packs**: YAML-based rule definitions (e.g., UAL/2025.08.yml)
- **Validation Logic**: Hard constraints (must-have) and soft preferences (nice-to-have)
- **Scoring System**: Weighted preference scoring for optimization

### 5. Export & Storage
- **Bid Layer Export**: PBS format generation
- **Metadata Storage**: JSON-based artifact tracking
- **Version Control**: Rule pack versioning and schema evolution

## Deployment
- Hosted via GHCR-built Docker images.
- CI/CD through GitHub Actions (lint, tests, security scan, build, push).

## Performance Characteristics
- **Latency**: <2s for preference parsing, <5s for optimization
- **Throughput**: 100+ concurrent pilot sessions
- **Scalability**: Horizontal scaling via container orchestration
- **Reliability**: 99.9% uptime with graceful degradation