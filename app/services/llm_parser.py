"""
LLM-First Preference Parser
Primary method for converting natural language to structured preferences
Mathematical parsing as fallback for reliability
"""

import json
import os
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
import tiktoken

from app.models import PreferenceSchema
from app.models.enhanced import (
    LLMParseResult, 
    EnhancedPreferenceSchema, 
    ParsingMethod,
    to_enhanced_preference
)


class PreferenceParser:
    """LLM-first preference parser with fallback to rule-based parsing"""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.model_primary = os.getenv("LLM_MODEL_PRIMARY", "gpt-4-turbo-preview")
        self.model_fallback = os.getenv("LLM_MODEL_FALLBACK", "gpt-3.5-turbo")
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "2000"))
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.1"))
        
        # Load aviation context for better parsing
        self.aviation_context = self._load_aviation_context()
        
        # Token encoder for cost estimation
        self.encoder = tiktoken.encoding_for_model("gpt-4")
    
    def _load_aviation_context(self) -> Dict[str, Any]:
        """Load airline-specific context and terminology"""
        return {
            "UAL": {
                "contract_rules": [
                    "No more than 4 legs per day",
                    "Minimum 9 hours rest between duty periods",
                    "Weekend includes Saturday and Sunday",
                    "Red-eye defined as departure after 9 PM or arrival before 6 AM"
                ],
                "equipment_types": ["737", "757", "767", "777", "787"],
                "major_bases": ["SFO", "ORD", "EWR", "LAX", "DEN", "IAH", "IAD"],
                "terminology": {
                    "trip": "sequence of flights",
                    "pairing": "trip assignment",
                    "credit": "pay credit hours",
                    "block": "actual flight time",
                    "duty": "total on-duty time",
                    "layover": "rest period between flights"
                }
            },
            "DAL": {
                "contract_rules": [
                    "Maximum 14 hour duty day",
                    "Minimum 10 hours rest",
                    "Weekend protection available",
                    "International requires additional rest"
                ],
                "equipment_types": ["717", "737", "757", "767", "A220", "A320", "A330", "A350"],
                "major_bases": ["ATL", "DTW", "MSP", "SLC", "SEA", "LAX", "BOS", "JFK"]
            }
        }
    
    async def parse_preferences(
        self, 
        text: str, 
        persona: Optional[str] = None,
        airline: str = "UAL",
        pilot_context: Optional[Dict[str, Any]] = None
    ) -> LLMParseResult:
        """
        Primary method: Parse natural language preferences using LLM
        Fallback: Rule-based parsing if LLM fails
        
        Args:
            text: Natural language preference text
            persona: Selected persona for context
            airline: Airline code for context
            pilot_context: Additional pilot information
            
        Returns:
            LLMParseResult with parsed preferences and metadata
        """
        
        # Validate inputs
        if not text or not text.strip():
            raise ValueError("Preference text cannot be empty")
        
        # Default pilot context
        if pilot_context is None:
            pilot_context = {}
        
        try:
            # Primary: LLM parsing
            print(f"🤖 Attempting LLM parsing with {self.model_primary}")
            result = await self._llm_parse(text, persona, airline, pilot_context)
            print(f"✅ LLM parsing successful with confidence {result.confidence:.2f}")
            return result
            
        except Exception as llm_error:
            print(f"❌ LLM parsing failed: {llm_error}")
            
            try:
                # Fallback: Try secondary model
                print(f"🔄 Trying fallback model {self.model_fallback}")
                result = await self._llm_parse(
                    text, persona, airline, pilot_context, 
                    model=self.model_fallback
                )
                print(f"✅ Fallback LLM parsing successful")
                return result
                
            except Exception as fallback_error:
                print(f"❌ Fallback LLM also failed: {fallback_error}")
                
                # Last resort: Rule-based parsing
                print("🔧 Using rule-based fallback parsing")
                result = self._fallback_parse(text, persona, airline, pilot_context)
                print(f"✅ Rule-based parsing complete")
                return result
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _llm_parse(
        self, 
        text: str, 
        persona: Optional[str], 
        airline: str, 
        pilot_context: Dict[str, Any],
        model: Optional[str] = None
    ) -> LLMParseResult:
        """Primary LLM-based preference parsing with retry logic"""
        
        model_to_use = model or self.model_primary
        system_prompt = self._build_system_prompt(airline, pilot_context)
        user_prompt = self._build_user_prompt(text, persona, pilot_context)
        
        # Count tokens for cost estimation
        total_tokens = len(self.encoder.encode(system_prompt + user_prompt))
        
        response = await self.client.chat.completions.create(
            model=model_to_use,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            response_format={"type": "json_object"}
        )
        
        # Parse JSON response
        response_text = response.choices[0].message.content
        tokens_used = response.usage.total_tokens if response.usage else total_tokens
        
        try:
            parsed_json = json.loads(response_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from LLM: {e}")
        
        # Validate and create result
        return self._create_llm_result(
            parsed_json, text, model_to_use, tokens_used, ParsingMethod.LLM
        )
    
    def _build_system_prompt(self, airline: str, pilot_context: Dict[str, Any]) -> str:
        """Build system prompt with aviation context"""
        
        airline_info = self.aviation_context.get(airline, {})
        base = pilot_context.get('base', 'Unknown')
        equipment = pilot_context.get('equipment', [])
        seniority = pilot_context.get('seniority_percentile', 'Unknown')
        
        return f"""You are an expert airline pilot and PBS (Preferential Bidding System) specialist for {airline}.

Your job is to parse pilot preferences from natural language into structured bidding data that works with PBS systems.

AVIATION CONTEXT:
- Airline: {airline}
- Contract Rules: {airline_info.get('contract_rules', [])}
- Equipment Types: {airline_info.get('equipment_types', [])}
- Major Bases: {airline_info.get('major_bases', [])}
- Terminology: {airline_info.get('terminology', {})}

PILOT CONTEXT:
- Base: {base}
- Equipment: {equipment}
- Seniority: {seniority}

PARSING GUIDELINES:
1. Extract hard constraints (boolean rules that cannot be violated)
2. Extract soft preferences with weights 0.0-1.0 (higher = more important)
3. Consider airline-specific terminology and rules
4. Factor in pilot's seniority and base limitations
5. Provide confidence score 0.0-1.0 based on clarity of input
6. Suggest improvements based on pilot's context and industry best practices
7. Warn about potential conflicts or unrealistic expectations

RESPONSE FORMAT:
Return ONLY valid JSON matching this exact structure:
{{
    "hard_constraints": {{
        "no_weekends": boolean,
        "no_redeyes": boolean,
        "domestic_only": boolean,
        "max_duty_hours_per_day": number or null,
        "min_rest_hours": number or null,
        "specific_equipment": [list] or null,
        "avoid_bases": [list] or null
    }},
    "soft_preferences": {{
        "weekend_priority": number 0.0-1.0,
        "departure_time_preference": "morning|afternoon|evening|any",
        "departure_time_weight": number 0.0-1.0,
        "credit_hours_weight": number 0.0-1.0,
        "trip_length_preference": "short|medium|long|any",
        "trip_length_weight": number 0.0-1.0,
        "layover_quality_weight": number 0.0-1.0,
        "international_preference": number 0.0-1.0,
        "commute_friendly_weight": number 0.0-1.0
    }},
    "confidence": number 0.0-1.0,
    "reasoning": "string explaining parsing decisions",
    "suggestions": ["list of improvement suggestions"],
    "warnings": ["list of potential issues or conflicts"]
}}

Be precise with weights - use the full 0.0-1.0 range meaningfully."""
    
    def _build_user_prompt(
        self, 
        text: str, 
        persona: Optional[str], 
        pilot_context: Dict[str, Any]
    ) -> str:
        """Build user prompt with preference text and context"""
        
        prompt = f"""Parse these pilot preferences into structured PBS bidding data:

PREFERENCE TEXT:
"{text}"
"""
        
        if persona:
            prompt += f"\nPILOT PERSONA: {persona}"
        
        if pilot_context:
            prompt += f"\nADDITIONAL CONTEXT: {json.dumps(pilot_context)}"
        
        prompt += """

Parse into the exact JSON structure specified in the system prompt. 
Focus on extracting the pilot's true intent and providing actionable, realistic preferences."""
        
        return prompt
    
    def _create_llm_result(
        self, 
        parsed_json: Dict[str, Any], 
        original_text: str,
        model_version: str,
        tokens_used: int,
        method: ParsingMethod
    ) -> LLMParseResult:
        """Create LLMParseResult from parsed JSON"""
        
        # Extract required fields
        hard_constraints = parsed_json.get('hard_constraints', {})
        soft_preferences = parsed_json.get('soft_preferences', {})
        confidence = parsed_json.get('confidence', 0.5)
        reasoning = parsed_json.get('reasoning', 'No reasoning provided')
        suggestions = parsed_json.get('suggestions', [])
        warnings = parsed_json.get('warnings', [])
        
        # Create PreferenceSchema
        preference_schema = PreferenceSchema(
            hard_constraints=hard_constraints,
            soft_prefs=soft_preferences,
            confidence=confidence,
            source={"method": method.value, "model": model_version}
        )
        
        # Create and return LLMParseResult
        return LLMParseResult(
            preferences=preference_schema,
            confidence=confidence,
            reasoning=reasoning,
            suggestions=suggestions,
            warnings=warnings,
            parsing_method=method,
            model_version=model_version,
            tokens_used=tokens_used
        )
    
    def _fallback_parse(
        self, 
        text: str, 
        persona: Optional[str], 
        airline: str,
        pilot_context: Dict[str, Any]
    ) -> LLMParseResult:
        """Fallback rule-based parsing when LLM fails"""
        
        text_lower = text.lower()
        
        # Basic keyword detection
        hard_constraints = {
            "no_weekends": any(keyword in text_lower for keyword in [
                "weekend", "weekends", "saturday", "sunday", "no weekend"
            ]),
            "no_redeyes": any(keyword in text_lower for keyword in [
                "red-eye", "redeye", "red eye", "overnight", "late night"
            ]),
            "domestic_only": any(keyword in text_lower for keyword in [
                "domestic", "no international", "stay domestic", "continental"
            ])
        }
        
        # Basic weight inference
        soft_preferences = {
            "weekend_priority": 0.8 if hard_constraints["no_weekends"] else 0.3,
            "departure_time_preference": self._infer_departure_preference(text_lower),
            "departure_time_weight": 0.6 if any(time in text_lower for time in [
                "morning", "afternoon", "evening", "early", "late"
            ]) else 0.3,
            "credit_hours_weight": 0.7 if any(keyword in text_lower for keyword in [
                "credit", "hours", "pay", "money", "maximum"
            ]) else 0.5,
            "trip_length_weight": 0.6,
            "layover_quality_weight": 0.5,
            "international_preference": 0.2 if hard_constraints["domestic_only"] else 0.5,
            "commute_friendly_weight": 0.7 if any(keyword in text_lower for keyword in [
                "commute", "travel", "home", "base"
            ]) else 0.3
        }
        
        # Create preferences
        preference_schema = PreferenceSchema(
            hard_constraints=hard_constraints,
            soft_prefs=soft_preferences,
            confidence=0.6,  # Lower confidence for fallback
            source={"method": "fallback", "original_text": text}
        )
        
        return LLMParseResult(
            preferences=preference_schema,
            confidence=0.6,
            reasoning=f"Fallback parsing using keyword detection. Identified {len([k for k, v in hard_constraints.items() if v])} hard constraints.",
            suggestions=[
                "Consider being more specific about your preferences",
                "Use industry terminology for better parsing",
                "Try rephrasing with concrete examples"
            ],
            warnings=[
                "Fallback parsing may miss nuanced preferences",
                "Manual review recommended for complex requirements"
            ],
            parsing_method=ParsingMethod.FALLBACK,
            model_version="rule_based_v1"
        )
    
    def _infer_departure_preference(self, text: str) -> str:
        """Infer departure time preference from text"""
        if any(word in text for word in ["morning", "early", "am", "dawn"]):
            return "morning"
        elif any(word in text for word in ["afternoon", "midday", "lunch"]):
            return "afternoon"
        elif any(word in text for word in ["evening", "night", "pm", "late"]):
            return "evening"
        else:
            return "any"
    
    async def parse_preferences_to_enhanced(
        self,
        text: str,
        persona: Optional[str] = None,
        airline: str = "UAL",
        pilot_context: Optional[Dict[str, Any]] = None
    ) -> EnhancedPreferenceSchema:
        """Parse preferences and return enhanced schema"""
        
        llm_result = await self.parse_preferences(text, persona, airline, pilot_context)
        
        # Convert to enhanced schema
        enhanced = to_enhanced_preference(llm_result.preferences, llm_result)
        enhanced.natural_language_input = text
        enhanced.persona_context = persona
        enhanced.pilot_context = pilot_context or {}
        
        return enhanced


# Usage example and testing
async def test_parser():
    """Test the preference parser with example inputs"""
    parser = PreferenceParser()
    
    test_cases = [
        "I want weekends off and prefer morning departures, avoid red-eyes",
        "Maximize my credit hours but keep trips under 4 days",
        "Need to commute from Denver, prefer domestic flying",
        "Family first - weekends and holidays off, short trips preferred"
    ]
    
    for test_input in test_cases:
        print(f"\n🧪 Testing: '{test_input}'")
        try:
            result = await parser.parse_preferences(
                text=test_input,
                pilot_context={"base": "SFO", "equipment": ["737", "757"], "seniority_percentile": 0.65}
            )
            print(f"✅ Success: {result.parsing_method.value} (confidence: {result.confidence:.2f})")
            print(f"📝 Reasoning: {result.reasoning}")
            if result.suggestions:
                print(f"💡 Suggestions: {result.suggestions}")
        except Exception as e:
            print(f"❌ Failed: {e}")


if __name__ == "__main__":
    # Run test if module executed directly
    asyncio.run(test_parser())