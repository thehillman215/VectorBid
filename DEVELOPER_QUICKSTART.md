# VectorBid Developer Quickstart

This guide helps you get the VectorBid FastAPI + frontend development environment running locally.

## Prerequisites

- Python 3.11+
- Node.js (for potential future frontend builds)
- Git

## Quick Start

### 1. One-Click Development Setup

```bash
./dev.sh
```

This script will:
- Check dependencies and install if needed (FastAPI, uvicorn)
- Start the FastAPI backend on port 8000
- Serve the SPA frontend at the same URL
- Enable hot-reload for development

### 2. Access the Application

- **Frontend SPA**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative API docs**: http://localhost:8000/redoc

### 3. Development Workflow

The application follows a modern SPA + API architecture:

#### Frontend (Single Page Application)
- **Location**: `app/static/`
- **Entry point**: `app/static/index.html`
- **JavaScript**: `app/static/app.js`
- **Styling**: Tailwind CSS (CDN)
- **Icons**: Font Awesome

#### Backend (FastAPI)
- **Location**: `app/fastapi_main.py`
- **Auto-reload**: Enabled by default
- **API Base**: `/api/`

### 4. API Endpoints

The FastAPI backend exposes these endpoints matching the MVP blueprint:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/personas` | GET | Get available pilot personas |
| `/api/parse_preferences` | POST | Parse free-text preferences |
| `/api/validate_constraints` | POST | Validate preference constraints |
| `/api/optimize` | POST | Optimize schedule based on preferences |
| `/api/generate_layers` | POST | Generate PBS-style bid layers |
| `/api/lint` | POST | Lint preference configuration |
| `/api/exports/{id}` | GET | Get exported bid file |
| `/api/explain/{candidate_id}` | GET | Explain candidate ranking |

### 5. Frontend Features

The SPA includes all MVP blueprint components:

#### Step 1: Persona Picker
- Visual cards for each persona (Family First, Money Maker, etc.)
- Custom option for user-defined preferences
- Auto-population of default preferences

#### Step 2: Preferences Input
- **Free-text box**: Natural language preference input
- **Live preview**: Real-time parsing of preferences
- **Weight sliders**: Fine-tune preference weights
- **Hard constraints**: Toggle absolute requirements

#### Step 3: Results
- **Schedule view**: Ranked candidate schedules with rationales
- **Layers view**: PBS-style bid layers with probabilities
- **Violations panel**: Constraint analysis and warnings
- **What-if re-rank**: Explain candidate rankings

### 6. Data Schemas

The application uses Pydantic models defined in `app/models.py`:

- `PreferenceSchema`: User preferences and constraints
- `CandidateSchedule`: Ranked trip candidates
- `BidLayerArtifact`: PBS bid layers output

### 7. Mock Data

For development independence, the FastAPI backend returns deterministic stub data:

- **Personas**: 3 sample personas with realistic preferences
- **Schedules**: Mock candidate schedules with scores and rationales  
- **Layers**: Sample PBS layers with commands and probabilities
- **Explanations**: Detailed score breakdowns

### 8. File Structure

```
app/
├── fastapi_main.py      # FastAPI application
├── models.py            # Pydantic schemas (if available)
├── static/
│   ├── index.html       # SPA entry point
│   └── app.js          # Frontend JavaScript
dev.sh                   # Development startup script
DEVELOPER_QUICKSTART.md  # This file
```

### 9. Development Tips

#### Hot Reload
- Backend changes automatically trigger reload
- Frontend changes require browser refresh
- API docs update automatically

#### Debugging
- Check browser console for frontend errors
- API errors appear in terminal running `dev.sh`
- Use `/docs` endpoint to test API manually

#### Adding Features
1. Update Pydantic models in `app/models.py`
2. Add API endpoints in `app/fastapi_main.py`
3. Update frontend in `app/static/app.js`
4. Test via browser or `/docs` interface

### 10. Testing the MVP

#### Persona Selection
1. Visit http://localhost:8000
2. Click any persona card
3. Verify "Continue to Preferences" button enables

#### Preferences Input
1. Enter text like "I want weekends off, prefer morning departures"
2. Verify live preview shows parsed preferences
3. Adjust weight sliders and constraint toggles

#### Results Generation
1. Click "Compile My Bid"
2. Verify loading overlay appears
3. Check schedule results show ranked candidates
4. Switch to layers view for PBS commands
5. Test "Explain ranking" buttons

#### Export
1. Click "Export Bid" on results page
2. Verify PBS file downloads

### 11. Production Considerations

This development setup uses:
- Stub data for independent frontend development
- CORS enabled for all origins
- No authentication
- Hot reload enabled

For production deployment:
- Replace stub data with real optimization logic
- Configure proper CORS origins
- Add authentication middleware
- Disable debug/reload modes

### 12. Troubleshooting

#### Port conflicts
If port 8000 is in use, modify `dev.sh` to use a different port.

#### Missing dependencies
Run: `pip install fastapi uvicorn pydantic`

#### Frontend not loading
Verify `app/static/index.html` exists and FastAPI static mounting is working.

#### API errors
Check terminal output where `dev.sh` is running for error details.

---

## Next Steps

1. Run `./dev.sh`
2. Open http://localhost:8000
3. Test the full persona → preferences → results flow
4. Check API documentation at http://localhost:8000/docs

The application should now provide a complete MVP experience with mock data, allowing frontend development to proceed independently while backend logic is implemented.