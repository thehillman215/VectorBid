# Phase 1 Implementation Brief - PDF Parser Integration

## Overview
**Owner**: Cursor  
**Duration**: 1-2 days  
**Priority**: BLOCKING - Required for MVP demo  
**Branch**: `feature/pdf-parser-integration`

## Current State
- PDF parsing is stubbed with placeholder in `app/services/ingestion.py:206`
- Existing UAL PDF parser exists in `app/parsers/ual_pdf.py`
- Sample PDFs available in `bids/` directory for testing
- Integration tests exist but currently use mock data

## Implementation Requirements

### 1. Replace PDF Parser Placeholder
**File**: `app/services/ingestion.py`
**Current Code** (lines 206-210):
```python
def _parse_pdf(self, file_content: bytes, filename: str) -> list[dict[str, Any]]:
    """Parse PDF format - placeholder for future implementation."""
    # TODO: Integrate with existing PDF parser from src/lib/schedule_parser/
    # For now, return mock data
    return self._create_mock_trips()
```

**Required Change**:
```python
def _parse_pdf(self, file_content: bytes, filename: str) -> list[Pairing]:
    """Parse UAL PDF format using existing parser."""
    try:
        # Use app/parsers/ual_pdf.py parser
        parsed_data = ual_pdf_parser.parse(file_content)
        
        # Convert to Pairing objects
        pairings = self._convert_to_pairings(parsed_data, filename)
        return pairings
        
    except Exception as e:
        raise PDFParsingError(f"Failed to parse PDF {filename}: {str(e)}") from e
```

### 2. Integration Points
**Files to examine**:
- `app/parsers/ual_pdf.py` - Understand existing parser interface
- `app/services/pbs_parser/contracts.py` - Pairing and Trip models
- `app/services/pbs_parser/reader.py` - Reference implementation patterns

### 3. Error Handling
**Add custom exception**:
```python
# app/services/ingestion.py - Add at top
class PDFParsingError(Exception):
    """Raised when PDF parsing fails."""
    pass
```

**Update error handling in ingest method**:
```python
except PDFParsingError as e:
    return IngestionResponse(
        success=False,
        summary={},
        error=str(e)
    )
```

### 4. Data Conversion Helper
**Add new method**:
```python
def _convert_to_pairings(self, pdf_data: Any, filename: str) -> list[Pairing]:
    """Convert PDF parser output to Pairing objects."""
    # Implementation depends on ual_pdf.py output format
    # Should create Pairing objects with associated Trip objects
    # Reference existing _parse_combined_csv for pattern
```

## Success Criteria
- [ ] Can parse `bids/bid_202513.pdf` without errors
- [ ] Returns list of `Pairing` objects with valid `Trip` data
- [ ] Graceful error handling for malformed PDFs
- [ ] Integration test `test_pdf_parsing_e2e` passes
- [ ] Unit tests achieve >90% coverage for new code
- [ ] No ruff linting violations
- [ ] Docker build succeeds

## Test Requirements

### Unit Tests
**Create**: `tests/services/test_ingestion_pdf.py`
```python
def test_parse_pdf_success():
    # Test successful PDF parsing
    
def test_parse_pdf_malformed():
    # Test error handling for bad PDFs
    
def test_convert_to_pairings():
    # Test data conversion logic
```

### Integration Test
**Update**: `fastapi_tests/test_ingest_route.py`
```python
def test_ingest_pdf_real_file():
    # Test with actual PDF from bids/ directory
    with open("bids/bid_202513.pdf", "rb") as f:
        response = client.post("/api/ingest", files={"file": f}, data={...})
    assert response.status_code == 200
    assert "trips" in response.json()["summary"]
```

## Dependencies
- May need additional PDF parsing libraries (add to requirements.txt)
- Ensure compatibility with existing `Pairing` and `Trip` models
- Maintain backward compatibility with CSV/JSONL parsing

## Implementation Notes
1. **Start** by examining `app/parsers/ual_pdf.py` to understand the interface
2. **Test incrementally** with small PDF samples first
3. **Preserve** existing mock fallback for unsupported formats
4. **Follow** existing patterns in `_parse_csv` and `_parse_jsonl` methods

## Handoff to Cline
When implementation is complete:
1. Run full test suite: `pytest tests/ fastapi_tests/ -v`
2. Check code quality: `ruff check . && ruff format .`
3. Verify Docker build: `docker build -t vectorbid-test .`
4. Create PR to `staging` with title: `feat: implement PDF parser integration`
5. Include test results and file change summary in PR description

## Questions/Issues
Tag @claude-code for:
- Strategy questions about data model conflicts
- Architecture decisions about error handling
- Integration issues with existing parsers

---
**Ready to implement!** 🚀