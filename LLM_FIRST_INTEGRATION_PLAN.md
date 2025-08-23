# VectorBid LLM-First Integration Plan
## AI-Powered Pilot Bidding Assistant - The Real Architecture

---

## Critical Insight: LLM-First, Algorithm Fallback

### **Current State**: ❌ Backwards Implementation
```
User Input → Basic String Matching → Mathematical Optimization → Results
            ↑ Primitive parsing      ↑ Primary method
```

### **Correct Architecture**: ✅ LLM-First Design
```
User Input → LLM Intelligence → Mathematical Optimization → LLM Explanation → Results
            ↑ Primary method    ↑ Fallback/validation     ↑ User-friendly results
```

**The mathematical optimization should VALIDATE and ENHANCE LLM recommendations, not replace them.**

---

## LLM Integration Architecture

### **Phase 1: Natural Language Understanding (Primary MVP Need)**
**LLM handles the core value proposition**: Understanding pilot preferences in natural language

#### 1.1 Preference Parsing Engine
**File**: `app/services/llm_parser.py`

```python
from typing import Optional, List, Dict, Any
from openai import AsyncOpenAI
import json
from app.models import PreferenceSchema

class PreferenceParser:
    def __init__(self):
        self.client = AsyncOpenAI()
        self.aviation_context = self._load_aviation_context()
    
    async def parse_preferences(
        self, 
        text: str, 
        persona: Optional[str] = None,
        airline: str = "UAL",
        pilot_context: Optional[Dict] = None
    ) -> PreferenceSchema:
        """
        Primary method: LLM parses natural language into structured preferences
        Fallback: Rule-based parsing if LLM fails
        """
        try:
            # Primary: LLM parsing
            return await self._llm_parse(text, persona, airline, pilot_context)
        except Exception as e:
            # Fallback: Rule-based parsing
            print(f"LLM parsing failed: {e}, falling back to rule-based parsing")
            return self._fallback_parse(text)
    
    async def _llm_parse(self, text: str, persona: str, airline: str, context: Dict) -> PreferenceSchema:
        """Primary LLM-based preference parsing"""
        
        system_prompt = f"""You are an expert airline pilot and PBS bidding specialist for {airline}. 
        
        Your job is to parse pilot preferences from natural language into structured bidding data.
        
        AVIATION CONTEXT:
        - PBS (Preferential Bidding System) uses layers of preferences
        - Hard constraints are non-negotiable (e.g., no weekends, max duty time)
        - Soft preferences have weights 0.0-1.0 (e.g., prefer morning departures)
        - Airline: {airline}
        - Contract rules: {self.aviation_context.get(airline, {})}
        
        PILOT CONTEXT:
        - Base: {context.get('base', 'Unknown')}
        - Equipment: {context.get('equipment', 'Unknown')}
        - Seniority: {context.get('seniority_percentile', 'Unknown')}
        - Persona: {persona}
        
        Parse the following preferences into valid JSON matching PreferenceSchema:
        - Extract hard constraints (boolean rules)
        - Extract soft preferences with appropriate weights
        - Consider airline-specific terminology
        - Factor in pilot's seniority and base limitations
        - Provide confidence score 0.0-1.0
        - Suggest improvements based on pilot's context
        
        Return ONLY valid JSON, no explanations."""
        
        user_prompt = f"""Pilot preferences to parse:
        
        "{text}"
        
        Parse into structured bidding preferences considering {airline} contract rules and PBS system."""
        
        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,  # Low temperature for consistency
            max_tokens=2000
        )
        
        parsed_json = json.loads(response.choices[0].message.content)
        
        # Validate and return PreferenceSchema
        return PreferenceSchema(**parsed_json)
    
    def _fallback_parse(self, text: str) -> PreferenceSchema:
        """Fallback rule-based parsing when LLM fails"""
        # Current basic string matching logic
        return PreferenceSchema(
            hard_constraints={
                "no_weekends": "weekend" in text.lower(),
                "no_redeyes": "red-eye" in text.lower() or "redeye" in text.lower(),
                "domestic_only": "domestic" in text.lower()
            },
            soft_preferences={
                "weekend_priority": 0.8 if "weekend" in text.lower() else 0.3,
                "credit_hours_weight": 0.7 if "credit" in text.lower() or "hours" in text.lower() else 0.5
            },
            confidence=0.6,  # Lower confidence for fallback
            source="fallback_parsing"
        )
```

#### 1.2 Enhanced Data Models
**File**: `app/models/enhanced.py`

```python
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class LLMParseResult(BaseModel):
    """Result from LLM preference parsing"""
    preferences: PreferenceSchema
    confidence: float
    reasoning: str
    suggestions: List[str]
    warnings: List[str]
    parsing_method: str  # "llm" or "fallback"

class EnhancedPreferenceSchema(PreferenceSchema):
    """Extended PreferenceSchema with LLM fields"""
    
    # Original input
    natural_language_input: Optional[str] = None
    persona_context: Optional[str] = None
    
    # LLM processing
    parsing_confidence: Optional[float] = None
    llm_reasoning: Optional[str] = None
    llm_suggestions: Optional[List[str]] = None
    llm_warnings: Optional[List[str]] = None
    
    # Processing metadata
    parsed_at: Optional[datetime] = None
    parsing_method: str = "unknown"  # "llm", "fallback", "manual"
    model_version: Optional[str] = None

class EnhancedCandidateSchedule(CandidateSchedule):
    """Extended CandidateSchedule with LLM explanations"""
    
    # LLM-generated insights
    quality_explanation: Optional[str] = None
    pros_and_cons: Optional[Dict[str, List[str]]] = None
    improvement_suggestions: Optional[List[str]] = None
    risk_assessment: Optional[List[str]] = None
    
    # Comparative analysis
    vs_preferences_analysis: Optional[str] = None
    market_context: Optional[str] = None
    
    # User-friendly metrics
    quality_summary: Optional[str] = None  # "Excellent for family time"
    confidence_level: Optional[str] = None  # "High", "Medium", "Low"
```

### **Phase 2: Intelligent Bid Optimization (LLM-Enhanced)**
**LLM guides the mathematical optimization with contextual intelligence**

#### 2.1 LLM-Guided Optimization Engine
**File**: `app/services/llm_optimizer.py`

```python
class LLMOptimizer:
    def __init__(self):
        self.client = AsyncOpenAI()
        self.math_optimizer = MathematicalOptimizer()  # Existing system
    
    async def optimize_with_llm(
        self,
        preferences: EnhancedPreferenceSchema,
        available_trips: List[Trip],
        pilot_context: Dict[str, Any]
    ) -> List[EnhancedCandidateSchedule]:
        """
        Primary: LLM analyzes context and guides mathematical optimization
        Fallback: Pure mathematical optimization
        """
        
        try:
            # Step 1: LLM analyzes the bidding context
            market_analysis = await self._analyze_market_context(
                available_trips, pilot_context
            )
            
            # Step 2: LLM suggests optimization strategy
            optimization_strategy = await self._suggest_optimization_strategy(
                preferences, market_analysis, pilot_context
            )
            
            # Step 3: Mathematical optimization with LLM guidance
            math_candidates = self.math_optimizer.optimize(
                preferences, available_trips, optimization_strategy
            )
            
            # Step 4: LLM enhances results with explanations
            enhanced_candidates = await self._enhance_candidates_with_llm(
                math_candidates, preferences, market_analysis
            )
            
            return enhanced_candidates
            
        except Exception as e:
            print(f"LLM optimization failed: {e}, using fallback math optimization")
            return self._fallback_optimize(preferences, available_trips)
    
    async def _analyze_market_context(self, trips: List[Trip], context: Dict) -> str:
        """LLM analyzes current bidding environment"""
        
        system_prompt = """You are an expert airline operations analyst and pilot advisor.
        
        Analyze the current trip offerings and market conditions to provide strategic bidding advice.
        
        Consider:
        - Trip availability patterns
        - Seasonal factors
        - Route popularity
        - Competition likelihood
        - Seniority implications
        
        Provide concise strategic insights for optimization."""
        
        trip_summary = self._summarize_trips_for_llm(trips)
        
        user_prompt = f"""Current bidding context:
        
        PILOT CONTEXT:
        {json.dumps(context, indent=2)}
        
        AVAILABLE TRIPS:
        {trip_summary}
        
        Provide strategic analysis for optimal bidding approach."""
        
        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )
        
        return response.choices[0].message.content
    
    async def _enhance_candidates_with_llm(
        self, 
        candidates: List[CandidateSchedule],
        preferences: EnhancedPreferenceSchema,
        market_analysis: str
    ) -> List[EnhancedCandidateSchedule]:
        """LLM provides user-friendly explanations for each candidate"""
        
        enhanced = []
        
        for candidate in candidates:
            try:
                explanation = await self._explain_candidate_quality(
                    candidate, preferences, market_analysis
                )
                
                enhanced_candidate = EnhancedCandidateSchedule(
                    **candidate.model_dump(),
                    quality_explanation=explanation["explanation"],
                    pros_and_cons=explanation["pros_and_cons"],
                    improvement_suggestions=explanation["suggestions"],
                    quality_summary=explanation["summary"],
                    confidence_level=explanation["confidence"]
                )
                
                enhanced.append(enhanced_candidate)
                
            except Exception as e:
                # Fallback: use original candidate without enhancement
                enhanced.append(EnhancedCandidateSchedule(**candidate.model_dump()))
        
        return enhanced
```

### **Phase 3: Conversational Bid Assistant (Advanced)**
**LLM provides ongoing guidance and explanations**

#### 3.1 Conversational Interface
**File**: `app/services/llm_assistant.py`

```python
class BidAssistant:
    """Conversational AI assistant for bid optimization"""
    
    def __init__(self):
        self.client = AsyncOpenAI()
        self.conversation_history: List[Dict] = []
    
    async def chat_about_bid(
        self,
        user_message: str,
        current_bid: Optional[EnhancedCandidateSchedule] = None,
        preferences: Optional[EnhancedPreferenceSchema] = None,
        context: Optional[Dict] = None
    ) -> str:
        """Conversational interface for bid guidance"""
        
        system_prompt = f"""You are an expert airline pilot and bidding advisor.
        
        You help pilots understand and improve their PBS bids through conversation.
        
        CURRENT BID CONTEXT:
        {json.dumps(current_bid.model_dump() if current_bid else {}, indent=2)}
        
        PILOT PREFERENCES:
        {json.dumps(preferences.model_dump() if preferences else {}, indent=2)}
        
        PILOT CONTEXT:
        {json.dumps(context or {}, indent=2)}
        
        Guidelines:
        - Be conversational and helpful
        - Use pilot terminology correctly
        - Explain complex concepts simply
        - Provide actionable advice
        - Ask clarifying questions when needed
        - Reference specific trips, routes, and constraints
        """
        
        self.conversation_history.append({
            "role": "user", 
            "content": user_message
        })
        
        messages = [{"role": "system", "content": system_prompt}] + self.conversation_history
        
        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        assistant_response = response.choices[0].message.content
        
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_response
        })
        
        return assistant_response
    
    async def explain_why_schedule_works(
        self,
        schedule: EnhancedCandidateSchedule,
        preferences: EnhancedPreferenceSchema
    ) -> str:
        """Explain why a particular schedule is good or bad"""
        
        prompt = f"""Explain why this schedule does or doesn't work for this pilot:

        PILOT WANTS:
        {preferences.natural_language_input}
        
        SCHEDULE DETAILS:
        {json.dumps(schedule.model_dump(), indent=2)}
        
        Provide a clear, conversational explanation of:
        1. How well the schedule meets their preferences
        2. What trade-offs were made
        3. Potential concerns or benefits
        4. Suggestions for improvement
        
        Write like you're talking to a colleague, not a computer."""
        
        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        
        return response.choices[0].message.content
```

---

## API Integration Points

### **Enhanced API Routes**
**File**: `app/api/routes.py` (Updated)

```python
from app.services.llm_parser import PreferenceParser
from app.services.llm_optimizer import LLMOptimizer
from app.services.llm_assistant import BidAssistant

parser = PreferenceParser()
optimizer = LLMOptimizer()
assistant = BidAssistant()

@router.post("/parse_preferences", tags=["Parse"])
async def parse_preferences(payload: dict[str, Any]) -> dict[str, Any]:
    """
    PRIMARY: LLM parses natural language preferences
    FALLBACK: Rule-based parsing if LLM fails
    """
    try:
        text = payload.get("preferences_text", "")
        persona = payload.get("persona")
        pilot_context = payload.get("pilot_context", {})
        
        # LLM-first parsing with fallback
        result = await parser.parse_preferences(
            text=text,
            persona=persona,
            pilot_context=pilot_context
        )
        
        return {
            "parsed_preferences": result.model_dump(),
            "confidence": result.parsing_confidence,
            "method": result.parsing_method,
            "suggestions": result.llm_suggestions or []
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

@router.post("/optimize", tags=["Optimize"])
async def optimize_with_llm(payload: dict[str, Any]) -> dict[str, Any]:
    """
    PRIMARY: LLM-guided optimization with mathematical validation
    FALLBACK: Pure mathematical optimization
    """
    try:
        preferences = EnhancedPreferenceSchema(**payload["preferences"])
        trips_data = payload.get("available_trips", [])
        pilot_context = payload.get("pilot_context", {})
        
        # LLM-enhanced optimization
        candidates = await optimizer.optimize_with_llm(
            preferences=preferences,
            available_trips=trips_data,
            pilot_context=pilot_context
        )
        
        return {
            "candidates": [c.model_dump() for c in candidates],
            "optimization_method": "llm_enhanced",
            "total_candidates": len(candidates)
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

@router.post("/chat", tags=["Assistant"])
async def chat_with_assistant(payload: dict[str, Any]) -> dict[str, Any]:
    """Conversational bid assistance"""
    try:
        message = payload.get("message", "")
        current_bid = payload.get("current_bid")
        preferences = payload.get("preferences")
        context = payload.get("context", {})
        
        response = await assistant.chat_about_bid(
            user_message=message,
            current_bid=EnhancedCandidateSchedule(**current_bid) if current_bid else None,
            preferences=EnhancedPreferenceSchema(**preferences) if preferences else None,
            context=context
        )
        
        return {"response": response}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

@router.post("/explain", tags=["Assistant"])
async def explain_schedule(payload: dict[str, Any]) -> dict[str, Any]:
    """Explain why a schedule works or doesn't work"""
    try:
        schedule = EnhancedCandidateSchedule(**payload["schedule"])
        preferences = EnhancedPreferenceSchema(**payload["preferences"])
        
        explanation = await assistant.explain_why_schedule_works(
            schedule=schedule,
            preferences=preferences
        )
        
        return {"explanation": explanation}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
```

---

## Implementation Priority (REVISED)

### **Critical Path: LLM Integration BEFORE Website Polish**

#### **Immediate (This Week)**
1. **LLM Preference Parser** - Core value proposition
2. **Enhanced Data Models** - Support LLM fields
3. **Basic LLM Optimization** - AI-guided math optimization
4. **API Integration** - Connect LLM services to existing routes

#### **Next (Following Week)**  
5. **Frontend Integration** - Update UI to use LLM features
6. **Conversational Assistant** - Chat interface for bid guidance
7. **Quality Explanations** - User-friendly result explanations

#### **Then (Website Polish)**
8. **Marketing Pages** - Now with real AI features to showcase
9. **User Dashboard** - Enhanced with AI insights
10. **Professional Polish** - Complete the transformation

### **Why This Order Matters**
- **LLM IS the core value proposition** - "AI that understands pilot language"
- **Marketing pages need real features** to demonstrate
- **User experience depends on** intelligent assistance, not just pretty UI
- **MVP credibility requires** working AI, not just professional appearance

---

## Success Metrics

### **Technical Metrics**
- **LLM Parse Success Rate**: >95% successful parsing
- **Fallback Rate**: <5% require rule-based parsing
- **Response Time**: <3 seconds for preference parsing
- **Optimization Quality**: LLM-guided results score >20% higher than pure math

### **User Experience Metrics**
- **Natural Language Success**: >90% of pilot input correctly understood
- **Explanation Quality**: >8.5/10 user rating for AI explanations
- **Guidance Helpfulness**: >80% find conversational assistant helpful
- **Time to Understanding**: <30 seconds to understand why schedule works

### **Business Metrics**
- **Feature Differentiation**: Clear competitive advantage over rule-based tools
- **User Adoption**: >70% use natural language input vs forms
- **Retention**: >85% return because of AI insights
- **Word of Mouth**: "This actually understands what pilots want"

---

## Environment Setup

### **Required Dependencies**
```python
# Add to pyproject.toml
dependencies = [
    "openai>=1.0.0",           # Primary LLM provider
    "anthropic>=0.8.0",        # Alternative LLM provider  
    "tiktoken>=0.5.0",         # Token counting
    "tenacity>=8.0.0",         # Retry logic for API calls
    "pydantic>=2.0.0",         # Enhanced data models
    "asyncio",                 # Async LLM calls
]
```

### **Environment Variables**
```bash
# .env
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key  # Backup provider
LLM_MODEL_PRIMARY=gpt-4-turbo-preview
LLM_MODEL_FALLBACK=gpt-3.5-turbo
LLM_MAX_TOKENS=2000
LLM_TEMPERATURE=0.1
```

**Result**: VectorBid becomes the first **truly intelligent** pilot bidding assistant that understands natural language and provides AI-powered guidance, with mathematical optimization as validation rather than the primary method.