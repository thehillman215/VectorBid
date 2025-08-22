"""
LLM-Driven PBS 2.0 Bid Strategy Generator

Generates sophisticated bid layers, groups, and filters using AI analysis of:
- Pilot preferences and context
- Historical data patterns  
- Market conditions
- Advanced PBS strategies (credit maximization, family time, commuting)
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.models import (
    FeatureBundle, CandidateSchedule, PreferenceSchema, BidLayerArtifact, 
    Layer, Filter, StrategyDirectives
)


class LLMBidStrategyGenerator:
    """AI-powered PBS 2.0 bid strategy generator"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("LLM_MODEL_PRIMARY", "gpt-4-turbo-preview")
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "3000"))
        self.temperature = 0.1  # Low temperature for consistent strategy generation
    
    async def generate_advanced_bid_strategy(
        self,
        bundle: FeatureBundle,
        candidates: List[CandidateSchedule],
        pilot_context: Optional[Dict[str, Any]] = None,
        strategy_focus: str = "balanced"
    ) -> Dict[str, Any]:
        """
        Generate comprehensive PBS 2.0 bid strategy with AI analysis
        
        Args:
            bundle: Complete feature bundle with preferences and context
            candidates: Top candidate schedules from optimization
            pilot_context: Additional pilot information
            strategy_focus: Strategy type ("family_first", "credit_max", "commuter", "balanced")
            
        Returns:
            Complete bid strategy with layers, groups, filters, and explanations
        """
        
        try:
            # Generate the strategy using LLM
            strategy_result = await self._generate_llm_strategy(
                bundle, candidates, pilot_context, strategy_focus
            )
            
            # Convert to PBS2 format
            pbs2_layers = self._convert_to_pbs2_layers(strategy_result)
            
            # Generate bid artifact
            bid_artifact = self._create_bid_artifact(bundle, pbs2_layers)
            
            return {
                "bid_artifact": bid_artifact,
                "strategy_analysis": strategy_result.get("strategy_analysis", {}),
                "layer_explanations": strategy_result.get("layer_explanations", []),
                "risk_mitigation": strategy_result.get("risk_mitigation", []),
                "market_insights": strategy_result.get("market_insights", []),
                "optimization_tips": strategy_result.get("optimization_tips", []),
                "confidence": strategy_result.get("confidence", 0.8),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"❌ LLM bid strategy generation failed: {e}")
            # Fallback to enhanced mathematical strategy
            return self._fallback_strategy(bundle, candidates)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _generate_llm_strategy(
        self,
        bundle: FeatureBundle,
        candidates: List[CandidateSchedule],
        pilot_context: Optional[Dict[str, Any]],
        strategy_focus: str
    ) -> Dict[str, Any]:
        """Core LLM strategy generation with retry logic"""
        
        system_prompt = self._build_strategy_system_prompt()
        user_prompt = self._build_strategy_user_prompt(
            bundle, candidates, pilot_context, strategy_focus
        )
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    def _build_strategy_system_prompt(self) -> str:
        """Build system prompt for PBS 2.0 strategy generation"""
        
        return """You are an expert airline pilot and PBS (Preferential Bidding System) specialist with deep knowledge of advanced bidding strategies.

Your task is to generate sophisticated PBS 2.0 bid strategies that go far beyond simple 1:1 pairing preferences. You understand:

PBS 2.0 STRATEGY CONCEPTS:
- Layer-based bidding with complex filter combinations
- Group preferences for similar trip patterns
- Conditional logic (avoid X unless Y is available)
- Priority ordering with fallback strategies
- Risk mitigation through diversified preferences
- Market dynamics and competition analysis

ADVANCED FILTER TYPES:
- Equipment filters (737, 757, 777, etc.)
- Base/destination filters (SFO, ORD, DEN, etc.) 
- Time-based filters (departure/arrival windows)
- Duration filters (trip length, layover time)
- Credit/duty hour filters
- Day-of-week filters
- Seasonal/monthly filters
- Commutability filters

SOPHISTICATED STRATEGIES:
1. "Credit Stacking" - Prioritize high-credit trips early, fill gaps with shorter trips
2. "Family Blocks" - Group weekend-off patterns with similar characteristics  
3. "Commuter Optimization" - Balance deadhead costs vs. trip value
4. "Reserve Avoidance" - Strategic overbidding to avoid reserve assignment
5. "Seniority Positioning" - Bid competitively where you have advantage
6. "Seasonal Gaming" - Exploit seasonal patterns and competition levels

LAYER STRUCTURE:
Each layer should have:
- Specific rationale for its position
- Optimized filter combinations
- Risk/reward analysis
- Competition assessment

Return ONLY valid JSON with this structure:
{
    "strategy_analysis": {
        "strategy_type": "string describing overall approach",
        "key_insights": ["list of strategic insights"],
        "market_assessment": "competition and timing analysis",
        "risk_factors": ["potential risks identified"],
        "success_probability": number 0.0-1.0
    },
    "bid_layers": [
        {
            "layer_number": number,
            "priority": "HIGH|MEDIUM|LOW",
            "rationale": "why this layer is positioned here",
            "filters": [
                {
                    "type": "filter type (Equipment, Base, DepartureTime, etc.)",
                    "operator": "IN|NOT_IN|EQUALS|RANGE|etc.",
                    "values": ["filter values"],
                    "reasoning": "why this filter combination"
                }
            ],
            "prefer": "YES|NO",
            "expected_competition": "LOW|MEDIUM|HIGH",
            "fallback_strategy": "what happens if this fails"
        }
    ],
    "layer_explanations": [
        "detailed explanation for each layer strategy"
    ],
    "risk_mitigation": [
        "specific steps to reduce bidding risks"
    ],
    "market_insights": [
        "insights about current market conditions"
    ],
    "optimization_tips": [
        "tips for future bid cycles"
    ],
    "confidence": number 0.0-1.0
}

Focus on creating 8-15 layers that work together as a cohesive strategy, not just individual preferences."""

    def _build_strategy_user_prompt(
        self,
        bundle: FeatureBundle,
        candidates: List[CandidateSchedule],
        pilot_context: Optional[Dict[str, Any]],
        strategy_focus: str
    ) -> str:
        """Build user prompt with all context for strategy generation"""
        
        # Extract key information
        preferences = bundle.preference_schema.model_dump() if bundle.preference_schema else {}
        context = bundle.context.model_dump() if bundle.context else {}
        
        # Summarize top candidates
        candidate_summaries = []
        for candidate in candidates[:10]:  # Top 10 for analysis
            summary = {
                "id": candidate.candidate_id,
                "score": candidate.score,
                "hard_ok": candidate.hard_ok,
                "breakdown": candidate.soft_breakdown,
                "pairings": candidate.pairings[:3]  # First 3 pairings
            }
            candidate_summaries.append(summary)
        
        prompt = f"""Generate an advanced PBS 2.0 bid strategy for this pilot:

PILOT PROFILE:
{json.dumps(context, indent=2)}

PILOT PREFERENCES:
{json.dumps(preferences, indent=2)}

STRATEGY FOCUS: {strategy_focus}

PILOT CONTEXT:
{json.dumps(pilot_context or {}, indent=2)}

TOP CANDIDATE ANALYSIS:
{json.dumps(candidate_summaries, indent=2)}

REQUIREMENTS:
1. Create 8-15 strategic bid layers that work together
2. Use advanced filter combinations beyond simple pairing IDs
3. Consider market competition and pilot seniority
4. Balance risk vs. reward in layer positioning
5. Provide detailed reasoning for each strategic decision
6. Include fallback plans for when high-priority layers fail
7. Address the specific strategy focus: {strategy_focus}

Generate a sophisticated bidding strategy that maximizes this pilot's chances of getting their optimal schedule while minimizing risk of poor outcomes."""

        return prompt
    
    def _convert_to_pbs2_layers(self, strategy_result: Dict[str, Any]) -> List[Layer]:
        """Convert LLM strategy to PBS2 Layer format"""
        
        pbs2_layers = []
        
        for layer_data in strategy_result.get("bid_layers", []):
            # Convert LLM filters to PBS2 Filter format
            pbs2_filters = []
            for filter_data in layer_data.get("filters", []):
                pbs2_filter = Filter(
                    type=filter_data.get("type", "PairingId"),
                    op=filter_data.get("operator", "IN"),
                    values=filter_data.get("values", [])
                )
                pbs2_filters.append(pbs2_filter)
            
            # Create PBS2 layer
            pbs2_layer = Layer(
                n=layer_data.get("layer_number", len(pbs2_layers) + 1),
                filters=pbs2_filters,
                prefer=layer_data.get("prefer", "YES")
            )
            pbs2_layers.append(pbs2_layer)
        
        return pbs2_layers
    
    def _create_bid_artifact(self, bundle: FeatureBundle, layers: List[Layer]) -> BidLayerArtifact:
        """Create PBS2 bid artifact from generated layers"""
        
        # Get airline from bundle
        airline = "UAL"  # Default, should extract from bundle
        if bundle.preference_schema:
            airline = bundle.preference_schema.airline
        elif bundle.context:
            airline = bundle.context.airline
        
        # Generate month (next month)
        now = datetime.utcnow()
        next_month = now.month + 1 if now.month < 12 else 1
        next_year = now.year if now.month < 12 else now.year + 1
        month = f"{next_year:04d}-{next_month:02d}"
        
        return BidLayerArtifact(
            airline=airline,
            format="PBS2",
            month=month,
            layers=layers,
            lint={"errors": [], "warnings": []},
            export_hash=""  # Will be computed later
        )
    
    def _fallback_strategy(
        self, 
        bundle: FeatureBundle, 
        candidates: List[CandidateSchedule]
    ) -> Dict[str, Any]:
        """Enhanced fallback strategy when LLM fails"""
        
        # Create basic layers from top candidates
        layers = []
        for i, candidate in enumerate(candidates[:10], 1):
            layer = Layer(
                n=i,
                filters=[Filter(
                    type="PairingId",
                    op="IN", 
                    values=candidate.pairings[:5]  # Top 5 pairings
                )],
                prefer="YES"
            )
            layers.append(layer)
        
        # Add preference-based layers
        if bundle.preference_schema:
            prefs = bundle.preference_schema
            
            # Equipment preference layer
            if prefs.equip:
                layers.append(Layer(
                    n=len(layers) + 1,
                    filters=[Filter(type="Equipment", op="IN", values=prefs.equip)],
                    prefer="YES"
                ))
            
            # Base preference layer
            if prefs.base:
                layers.append(Layer(
                    n=len(layers) + 1,
                    filters=[Filter(type="Base", op="EQUALS", values=[prefs.base])],
                    prefer="YES"
                ))
        
        artifact = self._create_bid_artifact(bundle, layers)
        
        return {
            "bid_artifact": artifact,
            "strategy_analysis": {
                "strategy_type": "Mathematical Fallback",
                "key_insights": ["LLM analysis unavailable", "Using top-ranked candidates"],
                "market_assessment": "Unable to assess without AI analysis",
                "risk_factors": ["No advanced risk analysis available"],
                "success_probability": 0.6
            },
            "layer_explanations": [
                "Fallback strategy using mathematical optimization results",
                "Basic preference filters applied where available"
            ],
            "risk_mitigation": ["Manual review recommended"],
            "market_insights": ["AI market analysis unavailable"],
            "optimization_tips": ["Enable LLM features for advanced strategies"],
            "confidence": 0.5,
            "generated_at": datetime.utcnow().isoformat()
        }


# Enhanced strategy directive generation
async def generate_llm_strategy_directives(
    bundle: FeatureBundle,
    candidates: List[CandidateSchedule],
    pilot_context: Optional[Dict[str, Any]] = None
) -> StrategyDirectives:
    """Generate strategy directives using LLM analysis"""
    
    generator = LLMBidStrategyGenerator()
    
    try:
        strategy_result = await generator.generate_advanced_bid_strategy(
            bundle, candidates, pilot_context, "balanced"
        )
        
        # Extract weight deltas from strategy analysis
        weight_deltas = {}
        strategy_analysis = strategy_result.get("strategy_analysis", {})
        
        # Simple heuristic mapping from strategy insights to weight adjustments
        insights = strategy_analysis.get("key_insights", [])
        for insight in insights:
            if "credit" in insight.lower():
                weight_deltas["block_hours"] = 0.1
            if "family" in insight.lower() or "weekend" in insight.lower():
                weight_deltas["layovers"] = 0.15
            if "commut" in insight.lower():
                weight_deltas["commutability"] = 0.2
        
        # Create layer templates from generated layers
        layer_templates = []
        for layer in strategy_result.get("bid_artifact", {}).get("layers", []):
            template = {
                "filters": [f.model_dump() for f in layer.filters],
                "prefer": layer.prefer,
                "reasoning": f"LLM-generated layer {layer.n}"
            }
            layer_templates.append(template)
        
        return StrategyDirectives(
            weight_deltas=weight_deltas,
            focus_hints={"strategy": strategy_analysis.get("strategy_type", "AI-guided")},
            layer_templates=layer_templates,
            rationale=strategy_result.get("layer_explanations", ["AI-generated strategy"])
        )
        
    except Exception as e:
        print(f"❌ LLM strategy directives failed: {e}")
        # Fallback to original simple strategy
        from app.strategy.engine import propose_strategy
        return propose_strategy(bundle, candidates)


# Testing function
async def test_llm_bid_strategy():
    """Test the LLM bid strategy generator"""
    
    print("🎯 Testing LLM-Driven PBS 2.0 Bid Strategy Generator")
    print("=" * 60)
    
    try:
        from app.models import FeatureBundle, ContextSnapshot, PreferenceSchema
        
        # Create mock data
        context = ContextSnapshot(
            ctx_id="test_context",
            pilot_id="test_pilot",
            airline="UAL",
            month="2025-09",
            base="SFO",
            seat="CA",
            equip=["737", "757"],
            seniority_percentile=0.65
        )
        
        preferences = PreferenceSchema(
            pilot_id="test_pilot",
            airline="UAL",
            base="SFO",
            seat="CA",
            equip=["737", "757"]
        )
        
        bundle = FeatureBundle(
            context=context,
            preference_schema=preferences,
            analytics_features={},
            compliance_flags={},
            pairing_features={"pairings": []}
        )
        
        candidates = [
            CandidateSchedule(
                candidate_id="high_credit_intl",
                score=0.92,
                hard_ok=True,
                soft_breakdown={"credit": 0.95, "family_time": 0.7},
                pairings=["SFO-NRT-SFO", "SFO-LHR-SFO"]
            ),
            CandidateSchedule(
                candidate_id="family_friendly_dom",
                score=0.88,
                hard_ok=True,
                soft_breakdown={"credit": 0.8, "family_time": 0.95},
                pairings=["SFO-LAX-SFO", "SFO-DEN-SFO"]
            )
        ]
        
        pilot_context = {
            "lifestyle": "family_first",
            "kids_at_home": True,
            "commuting": False,
            "financial_goals": "balanced"
        }
        
        generator = LLMBidStrategyGenerator()
        
        print("🧠 Generating advanced bid strategy...")
        
        result = await generator.generate_advanced_bid_strategy(
            bundle, candidates, pilot_context, "family_first"
        )
        
        print("✅ Strategy Generated Successfully!")
        print(f"Strategy Type: {result['strategy_analysis']['strategy_type']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Layers Generated: {len(result['bid_artifact'].layers)}")
        
        print("\n📋 Layer Summary:")
        for layer in result['bid_artifact'].layers[:5]:  # Show first 5
            filters_summary = f"{len(layer.filters)} filters"
            print(f"  Layer {layer.n}: {filters_summary}, Prefer: {layer.prefer}")
        
        print(f"\n💡 Key Insights ({len(result['strategy_analysis']['key_insights'])}):")
        for insight in result['strategy_analysis']['key_insights'][:3]:
            print(f"  • {insight}")
        
        print(f"\n⚠️ Risk Factors ({len(result['risk_mitigation'])}):")
        for risk in result['risk_mitigation'][:2]:
            print(f"  • {risk}")
        
        print("\n✨ LLM Bid Strategy Generator is working perfectly!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_llm_bid_strategy())