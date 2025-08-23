# URGENT: API Path Quick Fix - 15 Minutes Max

## Overview
**Task**: Fix API path mismatches blocking frontend integration  
**Duration**: 15 minutes  
**Priority**: BLOCKING - Everything else depends on this  
**Branch**: `feature/api-path-quick-fix`

## Problem
Frontend expects different API paths than backend provides:

```javascript
// Frontend calls:
fetch('/api/parse_preferences')     // ❌ 404 Error
fetch('/api/validate_constraints')  // ❌ 404 Error

// Backend provides:
/api/parse          // ✅ Works
/api/validate       // ✅ Works
```

## Solution: 2-Line Fix
**File**: `app/api/routes.py`  
**Lines to change**: 43 and 125

### Before:
```python
@router.post("/parse", tags=["Parse"])
def parse_preferences(payload: dict[str, Any]) -> dict[str, Any]:

@router.post("/validate", tags=["Validate"])  
def validate(payload: dict[str, Any]) -> dict[str, Any]:
```

### After:
```python
@router.post("/parse_preferences", tags=["Parse"])
def parse_preferences(payload: dict[str, Any]) -> dict[str, Any]:

@router.post("/validate_constraints", tags=["Validate"])
def validate(payload: dict[str, Any]) -> dict[str, Any]:
```

## Exact Changes Needed

### Change 1: Line 43
```python
# OLD:
@router.post("/parse", tags=["Parse"])

# NEW:
@router.post("/parse_preferences", tags=["Parse"])
```

### Change 2: Line 125  
```python
# OLD:
@router.post("/validate", tags=["Validate"])

# NEW:
@router.post("/validate_constraints", tags=["Validate"])
```

## That's it! Two lines. Done.

## Test Verification
After making changes, test that endpoints work:

```bash
# Start server
uvicorn app.main:app --reload

# Test new paths work
curl -X POST "http://localhost:8000/api/parse_preferences" \
  -H "Content-Type: application/json" \
  -d '{"preferences_text": "test"}'

curl -X POST "http://localhost:8000/api/validate_constraints" \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
```

Should return JSON responses (not 404 errors).

## Commit & Push
```bash
git add app/api/routes.py
git commit -m "fix: align API paths with frontend expectations

- Change /parse to /parse_preferences
- Change /validate to /validate_constraints
- Unblocks frontend integration for Phase 3"

git push origin feature/api-path-quick-fix
```

## Success Criteria
- [ ] Frontend can call `/api/parse_preferences` without 404
- [ ] Frontend can call `/api/validate_constraints` without 404  
- [ ] All existing functionality still works
- [ ] Ready for immediate Cline validation

## Handoff to Cline
**Message**: "API path fix complete. Please test endpoints and merge to staging ASAP. This unblocks Phase 3B parallel development."

---
**GO! This 15-minute fix unlocks everything else!** ⚡