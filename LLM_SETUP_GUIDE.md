# LLM Integration Setup Guide
## Get AI-Powered Preference Parsing Working

---

## 🚀 **Quick Setup (5 minutes)**

### **Step 1: Install Dependencies**
```bash
# Install new LLM dependencies
pip install openai anthropic tiktoken tenacity

# Or install all dependencies 
pip install -e .
```

### **Step 2: Set Up Environment**
```bash
# Copy environment template
cp .env.example .env

# Edit .env file and add your OpenAI API key
# OPENAI_API_KEY=your_actual_api_key_here
```

### **Step 3: Test LLM Integration**
```bash
# Run the test script
python test_llm_integration.py

# Expected output:
# ✅ LLM parsing successful with confidence 0.95
# 🧠 Model: gpt-4-turbo-preview
# 📝 Reasoning: Parsed pilot preferences focusing on family time...
```

### **Step 4: Test API Integration**
```bash
# Start the server
uvicorn app.main:app --reload

# Test the enhanced API endpoint
curl -X POST "http://localhost:8000/api/parse_preferences" \
  -H "Content-Type: application/json" \
  -d '{
    "preferences_text": "I want weekends off and prefer morning departures",
    "persona": "family_first",
    "airline": "UAL",
    "pilot_context": {
      "base": "SFO",
      "equipment": ["737"],
      "seniority_percentile": 0.65
    }
  }'

# Expected response:
# {
#   "parsed_preferences": {...},
#   "confidence": 0.92,
#   "method": "llm",
#   "reasoning": "...",
#   "suggestions": [...],
#   "warnings": [...]
# }
```

---

## 🎯 **What's Been Implemented**

### **✅ Core LLM Infrastructure**
- **PreferenceParser**: LLM-first parsing with fallback
- **Enhanced Data Models**: Support for AI fields and explanations
- **API Integration**: `/api/parse_preferences` endpoint with LLM
- **Environment Setup**: Configuration for OpenAI and Anthropic
- **Test Suite**: Comprehensive testing framework

### **✅ Smart Fallback System**
```
User Input → LLM Parsing → Success → Enhanced Results
           ↘ Fails → Fallback Model → Success → Good Results
                   ↘ Fails → Rule-Based → Basic Results
```

### **✅ Professional Data Flow**
```python
# Input: Natural language
"I want weekends off and prefer morning departures, avoid red-eyes"

# Output: Structured preferences
{
  "hard_constraints": {
    "no_weekends": true,
    "no_redeyes": true
  },
  "soft_preferences": {
    "weekend_priority": 0.9,
    "departure_time_preference": "morning",
    "departure_time_weight": 0.8
  },
  "confidence": 0.92,
  "suggestions": ["Consider specifying layover preferences"],
  "warnings": []
}
```

---

## 🧪 **Testing Scenarios**

### **Test Case 1: Family-First Pilot**
```python
input = "I want weekends off and prefer morning departures, avoid red-eyes"
expected_confidence = >0.9
expected_constraints = {"no_weekends": true, "no_redeyes": true}
```

### **Test Case 2: Credit Maximizer**
```python  
input = "Maximize my credit hours but keep trips under 4 days"
expected_weights = {"credit_hours_weight": >0.8, "trip_length_weight": >0.7}
```

### **Test Case 3: Commuter Pilot**
```python
input = "Need to commute from Denver, prefer domestic flying"
expected_context = {"commute_friendly_weight": >0.7, "domestic_preference": >0.8}
```

### **Test Case 4: Fallback Handling**
```python
# Simulate LLM failure
no_api_key = True
expected_method = "fallback"
expected_confidence = 0.6
expected_warnings = ["Basic parsing may miss nuanced preferences"]
```

---

## 📊 **Performance Benchmarks**

### **LLM Performance Targets**
- **Parse Success Rate**: >95% for typical pilot input
- **Response Time**: <3 seconds including API call
- **Confidence Score**: >0.85 for clear preferences
- **Fallback Rate**: <5% require rule-based parsing

### **Cost Estimation**
- **Tokens per request**: ~500-1000 tokens
- **Cost per parse**: ~$0.01-0.02 (GPT-4)
- **Monthly cost** (1000 parses): ~$10-20

---

## 🔧 **Troubleshooting**

### **Common Issues**

#### **"OPENAI_API_KEY not set"**
```bash
# Add to .env file
echo "OPENAI_API_KEY=your_key_here" >> .env
```

#### **"Import Error: No module named 'openai'"**
```bash
# Install dependencies
pip install openai anthropic tiktoken tenacity
```

#### **"LLM parsing failed"**
- Check API key is valid
- Check internet connection
- Review quota/billing on OpenAI dashboard
- System falls back to rule-based parsing automatically

#### **"Low confidence scores"**
- Input may be unclear or ambiguous
- Try more specific pilot terminology
- Check suggestions for improvement hints

### **Debug Mode**
```bash
# Enable debug logging
export DEBUG=true
python test_llm_integration.py

# Check detailed error messages
tail -f uvicorn.log
```

---

## 🚀 **Next Steps**

### **Immediate (This Week)**
1. **Test with real pilot input** from your aviation network
2. **Optimize prompts** based on parsing quality
3. **Add conversation interface** for complex questions
4. **Connect to frontend** with live parsing

### **Next Week**
1. **LLM-guided optimization** - AI enhances mathematical results
2. **User personalization** - AI learns from user history  
3. **Professional explanations** - AI explains schedule quality
4. **Advanced chat interface** - Conversational bid assistance

### **Ready for Production**
- ✅ Fallback reliability ensures system always works
- ✅ Cost monitoring and optimization built-in
- ✅ Professional data validation and error handling
- ✅ Comprehensive test coverage

---

## 💡 **Key Innovation**

**VectorBid is now the first pilot bidding tool that truly understands natural language:**

- **Before**: "Select equipment: [737] [757] [767]"
- **After**: "I prefer narrow-body aircraft" → automatically selects 737/757

- **Before**: Complex form with 50+ fields
- **After**: "I want weekends off and good layovers" → structured preferences

- **Before**: Mathematical optimization only
- **After**: AI-guided optimization with explanations

**This transforms pilot experience from "filling out forms" to "having a conversation with an expert."**