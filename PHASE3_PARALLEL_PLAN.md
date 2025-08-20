# Phase 3 Parallel Development Plan - Frontend-API Integration

## Overview
**Approach**: Multi-track parallel development  
**Duration**: 2-3 days (overlaps with Phase 2)  
**Goal**: Connect static frontend to live API for full end-to-end demo

## Current State Analysis

### ✅ What Works:
- **Frontend SPA**: Complete 3-step workflow (persona → preferences → results)
- **Backend APIs**: Full optimization pipeline endpoints
- **Basic Integration**: Frontend calls some endpoints

### ❌ Critical Gaps:
- **Path mismatches**: Frontend expects `/api/parse_preferences`, API provides `/parse`
- **Missing file upload**: No connection between upload UI and `/api/ingest`
- **Mock data**: Frontend uses hardcoded personas, not live `/api/personas`
- **Error handling**: No graceful failure handling
- **State management**: Frontend state not synchronized with backend

## Parallel Development Tracks

### **Track A: API Path Alignment** 
**Owner**: Agent A (2-3 hours)  
**Branch**: `feature/api-path-alignment`

**Problem**: Frontend expects different paths than API provides
```javascript
// Frontend calls:
'/api/parse_preferences'  →  Should be '/api/parse'
'/api/validate_constraints' →  Should be '/api/validate'  
'/api/optimize'          →  ✅ Already matches
```

**Solution**: Update API routes to match frontend expectations
```python
# app/api/routes.py - Update route decorators:
@router.post("/parse_preferences", tags=["Parse"])  # Was: "/parse"
@router.post("/validate_constraints", tags=["Validate"])  # Was: "/validate"
```

### **Track B: File Upload Integration**
**Owner**: Agent B (1 day)  
**Branch**: `feature/upload-integration`

**Scope**: Connect frontend upload UI to backend ingestion
- Add upload route to serve the upload page
- Integrate file upload form with `/api/ingest` endpoint  
- Add progress indicators and error handling
- Test with real PDF files

**Key Files**:
- `app/routes/ui.py` - Add upload page route
- `app/static/upload.html` - Upload form (may need creation)
- `app/static/app.js` - Add upload handlers

### **Track C: Live Data Integration**
**Owner**: Agent C (1-2 days)  
**Branch**: `feature/live-data-integration`

**Replace mock data with live API calls**:
- ✅ Personas: Frontend already calls `/api/personas` 
- ❌ Optimization: Connect real optimization results
- ❌ Export: Connect export functionality
- ❌ Rule packs: Add rule pack selection UI (depends on Phase 2)

### **Track D: Error Handling & UX**
**Owner**: Agent D (1 day)  
**Branch**: `feature/error-handling-ux`

**Add production-ready error handling**:
- API error response handling
- Loading states for all operations
- File upload validation (size, type)
- Network failure recovery
- User feedback for all operations

## Implementation Priority

### **Day 1 (Immediate)**:
1. **Track A**: Fix API path mismatches (blocking)
2. **Track B**: Start file upload integration

### **Day 2**: 
3. **Track C**: Live data integration
4. **Track D**: Error handling

### **Day 3**:
5. **Integration testing**: All tracks merge
6. **End-to-end demo**: Complete workflow test

## Detailed Implementation Specs

### Track A: API Path Alignment
**Files to modify**:
```python
# app/api/routes.py
@router.post("/parse_preferences", tags=["Parse"])  # Line 43: was "/parse"
def parse_preferences(payload: dict[str, Any]) -> dict[str, Any]:

@router.post("/validate_constraints", tags=["Validate"])  # Line 125: was "/validate"  
def validate(payload: dict[str, Any]) -> dict[str, Any]:
```

**Alternative approach**: Update frontend paths instead
```javascript
// app/static/app.js - Update fetch calls:
const response = await fetch('/api/parse', {  // Remove '_preferences'
```

### Track B: File Upload Integration
**Missing route needed**:
```python
# app/routes/ui.py - Add upload page
@router.get("/upload")
async def upload_page():
    return FileResponse("app/static/upload.html")
```

**Frontend integration**:
```javascript
// app/static/app.js - Add upload handler
async function uploadBidPackage(file, metadata) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('airline', metadata.airline);
    // ... other metadata
    
    const response = await fetch('/api/ingest', {
        method: 'POST',
        body: formData
    });
    return response.json();
}
```

### Track C: Live Data Integration
**Current mock data to replace**:
```javascript
// app/main.py:124 - Mock personas
MOCK_PERSONAS = {
    "family_first": {...},
    "money_maker": {...}
}

// Replace with dynamic rule pack personas from Phase 2
```

**Connect optimization results**:
```javascript
// Frontend expects candidates array with rationale
// Backend provides exactly this format - just need to connect
```

## Success Criteria
- [ ] All frontend paths match API endpoints
- [ ] File upload works with real PDF files
- [ ] Optimization returns live results with rationale
- [ ] Export generates downloadable bid layers
- [ ] Error handling prevents crashes
- [ ] Loading states provide user feedback
- [ ] End-to-end demo: Upload → Preferences → Optimization → Export

## Coordination Points
1. **API contract stability**: Track A changes affect all other tracks
2. **Rule pack dependency**: Track C depends on Phase 2 completion
3. **Error format consistency**: All tracks use same error response format
4. **State management**: Frontend state synchronized across all operations

## Merge Strategy
1. **Track A merges first** (enables other tracks)
2. **Daily integration** to catch conflicts early  
3. **Track B & C can develop in parallel** after Track A
4. **Track D integrates last** (adds polish to working features)

## Testing Requirements
- **Unit tests**: Each track adds tests for new functionality
- **Integration tests**: End-to-end workflow testing
- **Error scenario testing**: Network failures, invalid files, etc.
- **Cross-browser testing**: Ensure upload works across browsers

---
**This parallel approach maximizes development velocity while Phase 2 rule pack integration completes!** 🚀