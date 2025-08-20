# Phase 3B Implementation Brief - File Upload + Live Integration

## Overview
**Owner**: Cursor  
**Duration**: 2-3 hours  
**Priority**: HIGH - Complete MVP demo capability  
**Branch**: `feature/file-upload-live-integration`

## Status Check
✅ **Phase 1**: PDF parser working  
✅ **Phase 2**: Rule pack integration complete  
✅ **API Path Fix**: Frontend can now call backend APIs  
🎯 **Phase 3B**: Connect frontend upload to live optimization

## Implementation Plan

### **Track 1: File Upload Integration (1-2 hours)**

#### Problem
Frontend has upload UI but no connection to backend:
- Upload form exists in `app/static/index.html` (implied)
- `/api/ingest` endpoint works (from Phase 1)
- **Missing**: Route to serve upload page + form integration

#### Solution
**1. Add Upload Page Route**
```python
# app/routes/ui.py - Add this route
@router.get("/upload")
async def upload_page():
    """Serve the file upload page."""
    upload_path = Path(__file__).parent.parent / "static" / "upload.html"
    if upload_path.exists():
        return FileResponse(upload_path)
    else:
        # Fall back to main SPA with upload functionality
        return FileResponse(Path(__file__).parent.parent / "static" / "index.html")
```

**2. Enhance Frontend Upload Handler**
```javascript
// app/static/app.js - Add or enhance upload functionality
async function uploadBidPackage(file, metadata) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('airline', metadata.airline || 'UAL');
    formData.append('month', metadata.month || '2025.09');
    formData.append('base', metadata.base || 'SFO');
    formData.append('fleet', metadata.fleet || '737');
    formData.append('seat', metadata.seat || 'FO');
    formData.append('pilot_id', metadata.pilot_id || 'demo_pilot');
    
    try {
        const response = await fetch('/api/ingest', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Upload failed: ${response.status}`);
        }
        
        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Upload error:', error);
        throw error;
    }
}

// Add upload button handler
document.addEventListener('DOMContentLoaded', function() {
    const uploadButton = document.getElementById('upload-file-btn');
    const fileInput = document.getElementById('file-input');
    
    if (uploadButton && fileInput) {
        uploadButton.addEventListener('click', async function() {
            const file = fileInput.files[0];
            if (!file) {
                alert('Please select a file');
                return;
            }
            
            try {
                const result = await uploadBidPackage(file, {
                    airline: 'UAL',
                    month: '2025.09',
                    base: 'SFO',
                    fleet: '737',
                    seat: 'FO',
                    pilot_id: 'demo_pilot'
                });
                
                alert(`Upload successful! Parsed ${result.summary.trips} trips`);
            } catch (error) {
                alert(`Upload failed: ${error.message}`);
            }
        });
    }
});
```

### **Track 2: Live Optimization Integration (1 hour)**

#### Problem
Frontend optimization button doesn't connect to real backend results.

#### Solution
**Connect real optimization flow:**
```javascript
// app/static/app.js - Update compileBid function
async function compileBid() {
    try {
        showLoading(true);
        
        // 1. Create feature bundle from current state
        const featureBundle = {
            context: {
                ctx_id: generateContextId(),
                pilot_id: "demo_pilot",
                airline: "UAL", 
                month: "2025.09",
                base: "SFO",
                seat: "FO",
                equip: ["737"],
                seniority_percentile: 0.5,
                commuting_profile: {},
                default_weights: {}
            },
            preference_schema: {
                pilot_id: "demo_pilot",
                airline: "UAL",
                base: "SFO", 
                seat: "FO",
                equip: ["737"],
                hard_constraints: this.getHardConstraints(),
                soft_prefs: this.getSoftPreferences(),
                source: {
                    persona: this.selectedPersona,
                    text: this.preferences.text
                }
            },
            analytics_features: {},
            compliance_flags: {},
            pairing_features: {
                pairings: this.getMockPairings() // Use uploaded data when available
            }
        };
        
        // 2. Call real optimization endpoint
        const optimizeResponse = await fetch('/api/optimize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ feature_bundle: featureBundle, K: 10 })
        });
        
        if (!optimizeResponse.ok) {
            throw new Error(`Optimization failed: ${optimizeResponse.status}`);
        }
        
        const optimizeResult = await optimizeResponse.json();
        
        // 3. Display real candidates with rationale
        this.displayOptimizationResults(optimizeResult.candidates);
        
        // 4. Generate bid layers
        const layersResponse = await fetch('/api/generate_layers', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                feature_bundle: featureBundle,
                candidates: optimizeResult.candidates
            })
        });
        
        if (layersResponse.ok) {
            const layersResult = await layersResponse.json();
            this.displayBidLayers(layersResult.artifact);
        }
        
        showLoading(false);
        this.showStep(3); // Show results
        
    } catch (error) {
        showLoading(false);
        alert(`Optimization failed: ${error.message}`);
        console.error('Optimization error:', error);
    }
}

function generateContextId() {
    return 'demo_' + Date.now().toString(36) + Math.random().toString(36).substr(2);
}
```

### **Track 3: Error Handling & UX (30 minutes)**

#### Add Production-Ready Error Handling
```javascript
// app/static/app.js - Add error handling utilities
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'alert alert-error';
    errorDiv.textContent = message;
    document.body.prepend(errorDiv);
    
    setTimeout(() => errorDiv.remove(), 5000);
}

function showLoading(show) {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.classList.toggle('hidden', !show);
    }
}

function showSuccess(message) {
    const successDiv = document.createElement('div');
    successDiv.className = 'alert alert-success';
    successDiv.textContent = message;
    document.body.prepend(successDiv);
    
    setTimeout(() => successDiv.remove(), 3000);
}
```

## Success Criteria
- [ ] File upload works with real PDF files from `bids/` directory
- [ ] Upload displays parsing results (trip count, etc.)
- [ ] Optimization button connects to live `/api/optimize` endpoint
- [ ] Results show real candidate schedules with rationale
- [ ] Bid layers generation works end-to-end
- [ ] Error handling prevents crashes and shows user feedback
- [ ] Loading states provide visual feedback

## Testing Plan
1. **Upload Test**: Use `bids/bid_202513.pdf` 
2. **Optimization Test**: Complete workflow from upload to results
3. **Error Test**: Try invalid files, network failures
4. **Integration Test**: Full end-to-end demo capability

## Dependencies
- ✅ **Phase 1**: PDF parsing works
- ✅ **Phase 2**: Rule pack integration
- ✅ **API Path Fix**: Frontend can call backend
- ✅ **Server running**: `uvicorn app.main:app --reload`

## Files to Modify
- `app/routes/ui.py` - Add upload page route
- `app/static/app.js` - Upload handler + live optimization
- `app/static/index.html` - Ensure upload UI elements exist

## Timeline
- **Hour 1**: File upload integration
- **Hour 2**: Live optimization connection  
- **Hour 3**: Error handling + testing

## Handoff Requirements
When complete:
- Demonstrate end-to-end workflow: Upload → Optimize → Results
- Show error handling with invalid inputs
- Verify all API endpoints work from frontend
- Ready for full MVP demo

---
**This connects all the pieces for a complete MVP demo!** 🎯