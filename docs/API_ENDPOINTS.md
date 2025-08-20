# VectorBid API Endpoints

This document lists all API endpoints implemented in the FastAPI application, organized by their purpose and file location.

## Core Pipeline Endpoints (`/api/*`)

All core pipeline endpoints are implemented in `app/api/routes.py` and mounted with the `/api` prefix.

### 1. Parse Preferences
- **Endpoint**: `POST /api/parse`
- **Purpose**: Parse free-text preferences into structured format using NLP/LLM
- **File**: `app/api/routes.py`
- **Tags**: Parse

### 2. Validate Constraints
- **Endpoint**: `POST /api/validate`
- **Purpose**: Validate preference constraints against FAR 117 and union rules
- **File**: `app/api/routes.py`
- **Tags**: Validate

### 3. Optimize Schedule
- **Endpoint**: `POST /api/optimize`
- **Purpose**: Generate top-K candidate schedules based on preferences
- **File**: `app/api/routes.py`
- **Tags**: Optimize

### 4. Strategy Generation
- **Endpoint**: `POST /api/strategy`
- **Purpose**: Generate strategic directives for bid optimization
- **File**: `app/api/routes.py`
- **Tags**: Strategy

### 5. Generate Bid Layers
- **Endpoint**: `POST /api/generate_layers`
- **Purpose**: Convert candidate schedules to PBS bid layers
- **File**: `app/api/routes.py`
- **Tags**: Generate

### 6. Lint Layers
- **Endpoint**: `POST /api/lint`
- **Purpose**: Check bid layers for errors, warnings, and improvements
- **File**: `app/api/routes.py`
- **Tags**: Generate

### 7. Export Artifacts
- **Endpoint**: `POST /api/export`
- **Purpose**: Export bid layers to filesystem (API key protected)
- **File**: `app/api/routes.py`
- **Tags**: Export

## Operational Endpoints

### Health Checks
- **Endpoint**: `GET /health`
- **Purpose**: Main application health check
- **File**: `app/fastapi_main.py`
- **Tags**: Health

- **Endpoint**: `GET /ping`
- **Purpose**: Simple ping for CI smoke tests
- **File**: `app/routes/ops.py`
- **Tags**: Ops

- **Endpoint**: `GET /api/meta/health`
- **Purpose**: API/meta service health check
- **File**: `app/routes/meta.py`
- **Tags**: Meta

## UI Endpoints

### Frontend Routes
- **Endpoint**: `GET /`
- **Purpose**: Serve the single-page application
- **File**: `app/fastapi_main.py`
- **Tags**: UI

- **Endpoint**: `GET /api/personas`
- **Purpose**: Get available pilot personas for preference selection
- **File**: `app/fastapi_main.py`
- **Tags**: UI

## Router Organization

The application uses a modular router structure:

- **`app/api/routes.py`**: Core pipeline endpoints (`/api/*`)
- **`app/routes/ops.py`**: Operational endpoints (`/health`, `/ping`)
- **`app/routes/meta.py`**: Meta/API health endpoints (`/api/meta/health`)
- **`app/routes/ui.py`**: UI template routes
- **`app/fastapi_main.py`**: Main app configuration and SPA serving

## Pipeline Flow

The endpoints follow the architecture's proposed pipeline:

1. **Parse** → `POST /api/parse`
2. **Validate** → `POST /api/validate`
3. **Optimize** → `POST /api/optimize`
4. **Generate** → `POST /api/generate_layers`
5. **Lint** → `POST /api/lint`
6. **Export** → `POST /api/export`

## Security

- Export endpoint is protected by API key when `VECTORBID_API_KEY` is set
- All endpoints include proper error handling and HTTP status codes
- CORS is configured for cross-origin requests

## Testing

- `/ping` endpoint is specifically designed for CI smoke tests
- `/health` endpoints provide service status for monitoring
- All endpoints return structured JSON responses with proper error handling
