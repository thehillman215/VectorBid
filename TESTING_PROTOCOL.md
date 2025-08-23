# VectorBid Testing Protocol
**Established**: August 23, 2025  
**Purpose**: Prevent optimistic assessment bias through systematic functional testing

## 🎯 **Core Principle**
**Never claim a feature works without proving a pilot can complete the workflow end-to-end.**

## 🧪 **Mandatory Testing Before Status Claims**

### **1. Functional Testing (Required for ALL features)**

#### **End-to-End Pilot Workflow Test**
```bash
# Test the full pilot journey
1. Start server: uvicorn app.main:app --reload
2. Navigate to demo: curl http://localhost:8000/demo  
3. Input preferences: "I want weekends off and avoid red-eyes"
4. Process through optimization
5. Generate PBS layers
6. Export usable commands
7. Verify pilot can copy/paste into PBS system

# Success Criteria: Pilot gets working bid commands
# Failure: Any step breaks or returns empty/error results
```

#### **API Integration Testing**
```bash
# Test each API endpoint with realistic data
curl -X POST http://localhost:8000/api/parse_preferences \
  -H "Content-Type: application/json" \
  -d '{"preferences_text": "I want weekends off"}'

curl -X POST http://localhost:8000/api/optimize \
  -H "Content-Type: application/json" \  
  -d '{"feature_bundle": {...}}'

curl -X POST http://localhost:8000/api/generate_layers \
  -H "Content-Type: application/json" \
  -d '{"candidates": [...]}' 

# Success Criteria: All APIs return useful data, no errors
# Failure: Authentication errors, validation failures, empty responses
```

#### **Database Connectivity Test**
```bash
# Verify database actually works
curl http://localhost:8000/health
# Expected: {"db":"ok","storage":"ok","rulepack_version":"X.X"}

# Test data persistence
# Create test record → Retrieve test record → Verify data matches
```

### **2. Component Testing (Before claiming component complete)**

#### **LLM Integration Verification**
```bash
# Test AI parsing actually works
export OPENAI_API_KEY="your_key"
python -c "
from app.services.llm_parser import PreferenceParser
parser = PreferenceParser()
result = parser.parse_preferences('I want weekends off')
print(f'Confidence: {result.confidence}')
print(f'Method: {result.parsing_method}')
assert result.confidence > 0.8
"
```

#### **Admin Portal Verification**
```bash
# Test admin interface exists and works
curl http://localhost:8000/admin
# Expected: Admin login page, NOT 404

# Test admin functions
# User management, system monitoring, content management
```

#### **PBS Generation Verification**
```bash  
# Test actual PBS commands generated
curl -X POST http://localhost:8000/api/generate_layers [...]
# Expected: {"layers": ["PREFER WEEKENDS_OFF", "AVOID REDEYES", ...]}
# NOT: {"layers": []} 
```

## 📊 **Status Assessment Framework**

### **Feature Completion Levels**
- **✅ WORKING**: End-to-end pilot workflow tested successfully
- **🚧 PARTIAL**: Some functionality, but pilot workflow fails at key step  
- **❌ BROKEN**: Doesn't work at all (errors, 404s, empty responses)
- **📋 PLANNED**: Designed/documented but not implemented

### **Overall Completion Calculation**
```
Functional % = (Working Features / Total Required Features) * 100
Architecture % = (Built Components / Total Planned Components) * 100  
Polish % = (UI/UX Ready / Total Interface Elements) * 100

Realistic Completion = (Functional% * 0.5) + (Architecture% * 0.3) + (Polish% * 0.2)
```

### **Required Features for MVP**
1. Preference input and LLM parsing ❌
2. Schedule optimization with candidates ❌
3. PBS layer generation with actual commands ❌
4. Export functionality with usable output 🚧
5. Admin portal for user/system management ❌
6. Database persistence and retrieval 🚧
7. Authentication and user accounts ❌
8. Error handling and monitoring ❌

**Current MVP Status: 2/8 features working = 25% functional**

## 🔄 **Weekly Testing Cadence**

### **Every Monday**: Full System Test
1. Run complete pilot workflow test
2. Test all API endpoints
3. Verify database connectivity  
4. Check admin portal functionality
5. Update status documentation with results

### **Before Any Feature Claims**: Component Test
1. Test the specific feature end-to-end
2. Verify integration with existing system
3. Test error cases and edge conditions
4. Document exactly what works vs what doesn't

### **Before Any Demos**: Pessimistic Testing
1. Assume nothing works
2. Test every claimed feature manually
3. Prepare fallback explanations for broken parts
4. Never demo untested functionality

## 📝 **Documentation Standards**

### **Status Updates Must Include**
- **Test Date**: When was this actually tested?
- **Test Method**: How was functionality verified?
- **Test Results**: Specific API responses, error messages, success metrics
- **Pilot Impact**: Can a real pilot complete their workflow?

### **Banned Phrases in Status Docs**
- ❌ "Should work" - Test it
- ❌ "Mostly complete" - What % actually works?  
- ❌ "Just needs debugging" - Until debugged, it's broken
- ❌ "Almost ready" - Define exactly what's missing

### **Required Phrases**
- ✅ "Tested on [date] with [method]"
- ✅ "X% of pilot workflow functions"
- ✅ "Specific error: [exact error message]"
- ✅ "Pilot can/cannot complete [specific task]"

## 🎯 **Success Metrics**

### **Feature Development**
- Feature marked complete → 100% pilot workflow success
- Feature marked partial → Clear % of workflow working  
- Feature marked broken → Honest about what doesn't work

### **Project Assessment** 
- Realistic % based on actual testing
- No optimistic bias in status reporting
- Clear timeline based on what actually needs to be built

### **Communication**
- Stakeholder expectations aligned with reality
- No surprises when testing reveals issues
- Confidence in claimed functionality

## 🚨 **Red Flags That Require Immediate Testing**

1. **"99% complete"** - Almost nothing is 99% complete until tested
2. **"Just need to..."** - Usually means major work remaining
3. **"Should be working"** - Test it, don't assume
4. **"Everything is functional"** - Test every workflow
5. **Long time since last functional test** - Weekly testing minimum

---

**Bottom Line**: If a pilot can't complete their bidding workflow successfully, the feature doesn't work. Test ruthlessly, report honestly, build systematically.