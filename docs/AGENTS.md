# Agents

## DataSynth Agent
- Owns `tools/pbs_synth/`.
- Generates deterministic synthetic PBS datasets.

## Parser Agent
- Owns `app/services/pbs_parser/`.
- Parses synthetic datasets into normalized contracts.

## Cursor Integrator
- **Role**: Wire Codex's parser into the FastAPI service and minimal UI touchpoints
- **Scope**: Backend integration + minimal UI hooks (no Codex internals modification)
- **Owns**: `app/routes/ingestion.py`, `app/services/ingestion.py`, `app/services/store.py`

### Routes Implemented
- `POST /api/ingest` - Accept multipart file uploads with metadata
- `GET /api/meta/health` - Service health with version and Python info
- `GET /api/meta/parsers` - Supported formats and required fields

### Contracts Used
- **IngestionRequest**: `{airline, month, base, fleet, seat, pilot_id}`
- **IngestionResponse**: `{success, summary, message, error}`
- **BidPackage**: `{id, pilot_id, airline, month, meta, created_at, hash}`
- **PBS Parser Contracts**: `Pairing`, `Trip` from `app/services/pbs_parser/contracts.py`

### Storage Layer
- **File-backed storage**: Binary files stored in `uploads/` directory
- **SQLite metadata**: `bid_packages` table with package information
- **Hash-based IDs**: SHA256 file hashes for deduplication

### Integration Points
- **PBS Parser**: Calls `app/services/pbs_parser/reader.py` for CSV/JSONL
- **Schedule Parser**: Placeholder for PDF/TXT (future: integrate `src/lib/schedule_parser/`)
- **UI Hook**: Minimal upload form at `/upload` with HTMX integration

### How to Extend
1. **Add new file formats**: Extend `IngestionService.supported_formats` dict
2. **Enhance parsing**: Implement new `_parse_*` methods in `IngestionService`
3. **Add storage backends**: Extend `BidPackageStore` with new storage providers
4. **UI improvements**: Modify `app/templates/upload.html` for better UX
5. **Validation**: Add Pydantic validators to models for business rules

### Testing
- **Unit tests**: `fastapi_tests/test_ingest_route.py` - Happy path + error cases
- **Integration tests**: `fastapi_tests/test_meta_routes.py` - Health + parsers
- **Golden data**: Uses existing `data/goldens/` for CSV/JSONL testing

## Extension Rules
- Prefer pure functions and deterministic behavior.
- Keep I/O at the edges; models stay side-effect free.

## Developer Checklist
- Run `pre-commit run --files <changed>`.
- Execute `pytest -q` before committing.
- Update docs and tests alongside code.

## Self-Tasking
Agents may propose follow-up improvements here before implementing them.
