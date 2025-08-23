"""
LLM-Guided Optimization Engine
Enhances mathematical optimization with AI context analysis and explanations
"""

import json
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import asyncio

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
import tiktoken

from app.models import CandidateSchedule, PreferenceSchema, FeatureBundle
from app.models import EnhancedCandidateSchedule, LLMOptimizationResult, OptimizationMethod
from app.models import PBSStrategy, PilotWisdom


class LLMOptimizer:
    """AI-guided optimization engine that enhances mathematical results with context analysis"""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.model_primary = os.getenv("LLM_MODEL_PRIMARY", "gpt-4-turbo-preview")
        self.model_fallback = os.getenv("LLM_MODEL_FALLBACK", "gpt-3.5-turbo")
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "2000"))
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.1"))
        
        # Token encoder for cost estimation
        self.encoder = tiktoken.encoding_for_model("gpt-4")
    
    async def optimize_candidates(
        self,
        candidates: List[CandidateSchedule],
        preferences: PreferenceSchema,
        pilot_context: Optional[Dict[str, Any]] = None,
        feature_bundle: Optional[FeatureBundle] = None
    ) -> LLMOptimizationResult:
        """
        Enhance mathematical optimization results with AI guidance
        
        Args:
            candidates: List of candidate schedules from mathematical optimization
            preferences: Pilot preferences (potentially from LLM parsing)
            pilot_context: Additional pilot information
            feature_bundle: Full context bundle if available
            
        Returns:
            LLMOptimizationResult with enhanced candidates and explanations
        """
        
        if not candidates:
            raise ValueError("No candidates provided for optimization")
        
        # Default pilot context
        if pilot_context is None:
            pilot_context = {}
        
        try:
            # Primary: LLM-guided optimization
            print(f"🧠 Enhancing optimization with AI analysis...")
            result = await self._llm_optimize(candidates, preferences, pilot_context, feature_bundle)
            print(f"✅ AI optimization successful with {len(result.enhanced_candidates)} candidates")
            return result
            
        except Exception as llm_error:
            print(f"❌ LLM optimization failed: {llm_error}")
            
            try:
                # Fallback: Try secondary model
                print(f"🔄 Trying fallback model {self.model_fallback}")
                result = await self._llm_optimize(
                    candidates, preferences, pilot_context, feature_bundle,
                    model=self.model_fallback
                )
                print(f"✅ Fallback AI optimization successful")
                return result
                
            except Exception as fallback_error:
                print(f"❌ Fallback AI also failed: {fallback_error}")
                
                # Last resort: Return original candidates with basic analysis
                print("🔧 Using basic optimization fallback")
                result = self._fallback_optimize(candidates, preferences, pilot_context)
                print(f"✅ Basic optimization complete")
                return result
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _llm_optimize(
        self,
        candidates: List[CandidateSchedule],
        preferences: PreferenceSchema,
        pilot_context: Dict[str, Any],
        feature_bundle: Optional[FeatureBundle],
        model: Optional[str] = None
    ) -> LLMOptimizationResult:
        """Primary LLM-based optimization enhancement with retry logic"""
        
        model_to_use = model or self.model_primary
        system_prompt = self._build_optimization_system_prompt()
        user_prompt = self._build_optimization_user_prompt(
            candidates, preferences, pilot_context, feature_bundle
        )
        
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
        
        # Create enhanced result
        return self._create_optimization_result(
            parsed_json, candidates, preferences, model_to_use, tokens_used, OptimizationMethod.LLM_ENHANCED
        )
    
    def _build_optimization_system_prompt(self) -> str:
        """Build system prompt for optimization enhancement with PBS syntax generation focus"""
        
        return """You are Captain Sarah, an expert airline pilot with 25 years of experience, schedule optimizer, and PBS (Preferential Bidding System) specialist.

You have access to the entire schedule from the uploaded trip sheet and deep knowledge of:
- Contract rules and FAR117 regulations for duty time, rest requirements
- PBS 2.0 syntax for creating effective bid layers, groups, and filters
- Pilot lifestyle optimization strategies across different career stages
- Award probabilities and bidding psychology at different seniority levels

Your job is to:
1. Analyze mathematically optimized schedule candidates with pilot expertise
2. Generate at least 3 different PBS bidding strategy options
3. Create actual PBS 2.0 syntax that pilots can use in their bids
4. Provide contract-compliant and regulation-aware recommendations
5. Include optional pilot wisdom insights (can be toggled off)

OPTIMIZATION PROCESS:
1. Review candidates against contract rules and FAR117 compliance
2. Assess pilot lifestyle fit and career progression implications
3. Identify hidden patterns in trip sequences and layover combinations
4. Generate multiple bidding strategies for different award scenarios
5. Create PBS syntax layers with proper filters and preferences
6. Provide pilot-to-pilot wisdom and real-world insights
7. Output forward-strategy PBS syntax for immediate use

PBS SYNTAX EXPERTISE:
- Layer construction: preference order, filters, and award logic
- Filter types: equipment, base, layover cities, duty patterns, credit ranges
- Award probability optimization based on seniority and historical data
- Fallback strategies and contingency planning
- Integration with pilot lifestyle and career goals

RESPONSE FORMAT:
Return ONLY valid JSON with PBS syntax generation focus:
{
    "reranked_candidates": [
        {
            "candidate_id": "string",
            "enhanced_score": number 0.0-1.0,
            "ai_reasoning": "detailed pilot expertise explanation",
            "strengths": ["contract and lifestyle advantages"],
            "weaknesses": ["potential compliance or lifestyle issues"],
            "pilot_fit_score": number 0.0-1.0,
            "lifestyle_impact": "work-life balance and career implications",
            "improvement_suggestions": ["specific PBS bidding improvements"]
        }
    ],
    "overall_analysis": {
        "optimization_quality": number 0.0-1.0,
        "preference_alignment": number 0.0-1.0,
        "trade_off_analysis": "key trade-offs in schedule optimization",
        "missing_opportunities": ["better alternatives from trip sheet"],
        "risk_assessment": ["contract and regulation compliance risks"]
    },
    "pilot_guidance": {
        "recommended_candidate": "candidate_id of best choice",
        "explanation": "pilot-to-pilot reasoning for this choice",
        "alternative_choices": [
            {
                "candidate_id": "string",
                "scenario": "when this strategy works better",
                "reasoning": "pilot expertise explanation"
            }
        ],
        "bidding_strategy": "comprehensive PBS strategy advice"
    },
    "pbs_syntax_strategies": [
        {
            "strategy_name": "Primary Strategy",
            "description": "Main bidding approach for this pilot",
            "pbs_layers": [
                {
                    "layer_number": 1,
                    "preference": "YES",
                    "filters": ["EQUIP 737", "BASE SFO", "CREDIT 85-95"],
                    "rationale": "Target optimal credit with home base preference"
                }
            ],
            "award_probability": number 0.0-1.0,
            "fallback_plan": "what to do if this doesn't award"
        }
    ],
    "pilot_wisdom": {
        "enabled": true,
        "insights": ["real-world pilot tips and warnings"],
        "career_advice": "long-term strategy recommendations",
        "contract_notes": ["important contract considerations"]
    },
    "confidence": number 0.0-1.0,
    "model_insights": ["unique AI analysis only Captain Sarah could provide"]
}

Provide actionable PBS syntax that pilots can immediately use in their bidding systems."""
    
    def _build_optimization_user_prompt(
        self,
        candidates: List[CandidateSchedule],
        preferences: PreferenceSchema,
        pilot_context: Dict[str, Any],
        feature_bundle: Optional[FeatureBundle]
    ) -> str:
        """Build user prompt with optimization data"""
        
        # Summarize candidates for analysis
        candidate_summaries = []
        for i, candidate in enumerate(candidates[:10]):  # Limit to top 10 for token efficiency
            summary = {
                "candidate_id": candidate.candidate_id,
                "mathematical_score": candidate.score,
                "hard_ok": candidate.hard_ok,
                "soft_breakdown": candidate.soft_breakdown,
                "pairings": candidate.pairings,
                "rationale_summary": candidate.rationale.summary if candidate.rationale and hasattr(candidate.rationale, 'summary') else "No rationale"
            }
            candidate_summaries.append(summary)
        
        prompt = f"""Captain Sarah, analyze these mathematically optimized schedule candidates using your complete knowledge of the trip sheet and 25 years of pilot experience:

PILOT PROFILE AND PREFERENCES:
{json.dumps(preferences.model_dump(), indent=2)}

PILOT CONTEXT AND LIFESTYLE:
{json.dumps(pilot_context, indent=2)}

MATHEMATICAL OPTIMIZATION CANDIDATES:
{json.dumps(candidate_summaries, indent=2)}

CAPTAIN SARAH'S ANALYSIS TASKS:
1. Review all candidates against contract rules and FAR117 compliance
2. Apply your complete trip sheet knowledge to identify better combinations
3. Generate at least 3 different PBS bidding strategy options
4. Create actual PBS 2.0 syntax layers with proper filters and preferences
5. Provide pilot-to-pilot wisdom and real-world insights
6. Include contract considerations and regulation compliance notes
7. Output forward-strategy PBS syntax for immediate pilot use

IMPORTANT: Your Step 7 response must include actual PBS syntax that this pilot can copy and paste into their bidding system. Focus on creating multiple strategic approaches with proper layer construction, filter combinations, and award probability optimization.

Apply your expertise in: schedule sustainability, commuting logistics, career progression, family considerations, contract interpretation, and PBS bidding psychology at this pilot's seniority level.

Generate practical, actionable PBS bidding strategies with syntax-ready output."""
        
        if feature_bundle:
            prompt += f"\n\nADDITIONAL CONTEXT:\n{json.dumps(feature_bundle.model_dump(), indent=2)}"
        
        return prompt
    
    def _create_optimization_result(
        self,
        parsed_json: Dict[str, Any],
        original_candidates: List[CandidateSchedule],
        preferences: PreferenceSchema,
        model_version: str,
        tokens_used: int,
        method: OptimizationMethod
    ) -> LLMOptimizationResult:
        """Create LLMOptimizationResult from parsed JSON"""
        
        # Extract fields including new PBS syntax and pilot wisdom
        reranked_data = parsed_json.get('reranked_candidates', [])
        overall_analysis = parsed_json.get('overall_analysis', {})
        pilot_guidance = parsed_json.get('pilot_guidance', {})
        pbs_syntax_strategies = parsed_json.get('pbs_syntax_strategies', [])
        pilot_wisdom = parsed_json.get('pilot_wisdom', {})
        confidence = parsed_json.get('confidence', 0.7)
        model_insights = parsed_json.get('model_insights', [])
        
        # Create enhanced candidates by matching with original data
        enhanced_candidates = []
        candidate_map = {c.candidate_id: c for c in original_candidates}
        
        for rank_data in reranked_data:
            candidate_id = rank_data.get('candidate_id')
            original_candidate = candidate_map.get(candidate_id)
            
            if original_candidate:
                enhanced = EnhancedCandidateSchedule(
                    **original_candidate.model_dump(),
                    enhanced_score=rank_data.get('enhanced_score', original_candidate.score),
                    ai_reasoning=rank_data.get('ai_reasoning', ''),
                    strengths=rank_data.get('strengths', []),
                    weaknesses=rank_data.get('weaknesses', []),
                    pilot_fit_score=rank_data.get('pilot_fit_score', 0.5),
                    lifestyle_impact=rank_data.get('lifestyle_impact', ''),
                    improvement_suggestions=rank_data.get('improvement_suggestions', []),
                    optimization_method=method,
                    ai_analysis_version=model_version
                )
                enhanced_candidates.append(enhanced)
        
        # Fill in any missing candidates from original list
        processed_ids = {c.candidate_id for c in enhanced_candidates}
        for original in original_candidates:
            if original.candidate_id not in processed_ids:
                enhanced = EnhancedCandidateSchedule(
                    **original.model_dump(),
                    enhanced_score=original.score,
                    ai_reasoning="Not analyzed by AI - outside top candidates",
                    optimization_method=OptimizationMethod.MATHEMATICAL_ONLY,
                    ai_analysis_version=model_version
                )
                enhanced_candidates.append(enhanced)
        
        # Parse PBS strategies
        pbs_strategies = []
        for strategy_data in pbs_syntax_strategies:
            from app.models import PBSStrategy
            pbs_strategies.append(PBSStrategy(
                strategy_name=strategy_data.get('strategy_name', ''),
                description=strategy_data.get('description', ''),
                pbs_layers=strategy_data.get('pbs_layers', []),
                award_probability=strategy_data.get('award_probability', 0.5),
                fallback_plan=strategy_data.get('fallback_plan', '')
            ))
        
        # Parse pilot wisdom
        wisdom_data = None
        if pilot_wisdom:
            from app.models import PilotWisdom
            wisdom_data = PilotWisdom(
                enabled=pilot_wisdom.get('enabled', True),
                insights=pilot_wisdom.get('insights', []),
                career_advice=pilot_wisdom.get('career_advice', ''),
                contract_notes=pilot_wisdom.get('contract_notes', [])
            )
        
        return LLMOptimizationResult(
            enhanced_candidates=enhanced_candidates,
            original_candidates=original_candidates,
            optimization_quality=overall_analysis.get('optimization_quality', 0.7),
            preference_alignment=overall_analysis.get('preference_alignment', 0.7),
            trade_off_analysis=overall_analysis.get('trade_off_analysis', ''),
            missing_opportunities=overall_analysis.get('missing_opportunities', []),
            risk_assessment=overall_analysis.get('risk_assessment', []),
            recommended_candidate_id=pilot_guidance.get('recommended_candidate', ''),
            explanation=pilot_guidance.get('explanation', ''),
            alternative_choices=pilot_guidance.get('alternative_choices', []),
            bidding_strategy=pilot_guidance.get('bidding_strategy', ''),
            pbs_syntax_strategies=pbs_strategies,
            pilot_wisdom=wisdom_data,
            confidence=confidence,
            model_insights=model_insights,
            optimization_method=method,
            model_version=model_version,
            tokens_used=tokens_used,
            analysis_timestamp=datetime.utcnow()
        )
    
    def _fallback_optimize(
        self,
        candidates: List[CandidateSchedule],
        preferences: PreferenceSchema,
        pilot_context: Dict[str, Any]
    ) -> LLMOptimizationResult:
        """Fallback optimization when LLM fails"""
        
        # Simple rule-based re-ranking
        enhanced_candidates = []
        
        for i, candidate in enumerate(candidates):
            # Basic scoring adjustments based on preferences
            enhanced_score = candidate.score
            strengths = ["Mathematical optimization"]
            weaknesses = []
            
            # Adjust score based on simple preference matching
            if hasattr(preferences, 'hard_constraints'):
                if getattr(preferences.hard_constraints, 'no_weekends', False):
                    # Would need schedule analysis - simplified for fallback
                    enhanced_score *= 0.95
                    weaknesses.append("Weekend constraint not verified")
            
            enhanced = EnhancedCandidateSchedule(
                **candidate.model_dump(),
                enhanced_score=enhanced_score,
                ai_reasoning=f"Fallback analysis: Rank {i+1} from mathematical optimization",
                strengths=strengths,
                weaknesses=weaknesses,
                pilot_fit_score=0.6,
                lifestyle_impact="Unknown - AI analysis unavailable",
                improvement_suggestions=["Enable AI analysis for better insights"],
                optimization_method=OptimizationMethod.MATHEMATICAL_ONLY,
                ai_analysis_version="fallback_v1"
            )
            enhanced_candidates.append(enhanced)
        
        return LLMOptimizationResult(
            enhanced_candidates=enhanced_candidates,
            original_candidates=candidates,
            optimization_quality=0.6,
            preference_alignment=0.5,
            trade_off_analysis="AI analysis unavailable - using mathematical optimization only",
            missing_opportunities=["AI-guided insights not available"],
            risk_assessment=["Manual review recommended without AI analysis"],
            recommended_candidate_id=candidates[0].candidate_id if candidates else "",
            explanation="Top mathematical candidate recommended - AI analysis unavailable",
            alternative_choices=[],
            bidding_strategy="Enable AI features for personalized bidding strategy",
            confidence=0.5,
            model_insights=["AI analysis unavailable"],
            optimization_method=OptimizationMethod.MATHEMATICAL_ONLY,
            model_version="fallback_v1",
            analysis_timestamp=datetime.utcnow()
        )
    
    async def explain_schedule_choice(
        self,
        chosen_candidate: CandidateSchedule,
        alternatives: List[CandidateSchedule],
        preferences: PreferenceSchema,
        pilot_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate detailed explanation of why a specific schedule was chosen
        
        Args:
            chosen_candidate: The selected schedule
            alternatives: Other candidates that were considered
            preferences: Pilot preferences
            pilot_context: Additional pilot context
            
        Returns:
            Detailed explanation dictionary
        """
        
        try:
            system_prompt = """You are an expert airline pilot and career advisor. 
            
            Explain why a specific schedule choice is optimal for this pilot, comparing it to alternatives.
            Focus on practical implications for the pilot's career, lifestyle, and satisfaction.
            
            Return a JSON object with:
            - choice_explanation: detailed reasoning for the selection
            - comparison_analysis: how it compares to key alternatives
            - lifestyle_impact: what this choice means for work-life balance
            - career_implications: long-term career considerations
            - potential_concerns: any drawbacks or risks
            - optimization_tips: advice for future bidding"""
            
            user_prompt = f"""Explain why this schedule is the best choice:

CHOSEN SCHEDULE:
{json.dumps(chosen_candidate.model_dump(), indent=2)}

PILOT PREFERENCES:
{json.dumps(preferences.model_dump(), indent=2)}

PILOT CONTEXT:
{json.dumps(pilot_context or {}, indent=2)}

ALTERNATIVE SCHEDULES (top 3):
{json.dumps([alt.model_dump() for alt in alternatives[:3]], indent=2)}

Provide a clear, practical explanation that helps the pilot understand the reasoning behind this choice."""
            
            response = await self.client.chat.completions.create(
                model=self.model_primary,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"❌ Schedule explanation failed: {e}")
            return {
                "choice_explanation": "Selected based on mathematical optimization score",
                "comparison_analysis": "AI analysis unavailable",
                "lifestyle_impact": "Unknown - manual review recommended",
                "career_implications": "Standard schedule implications apply",
                "potential_concerns": ["AI explanation unavailable"],
                "optimization_tips": "Enable AI features for detailed guidance"
            }


# Usage example and testing
async def test_optimizer():
    """Test the LLM optimizer with example data"""
    
    # Mock candidate data for testing
    mock_candidates = [
        CandidateSchedule(
            candidate_id="cand_001",
            score=0.85,
            total_credit=85.5,
            total_duty=78.2,
            trips=[],
            rationale=None
        ),
        CandidateSchedule(
            candidate_id="cand_002", 
            score=0.82,
            total_credit=92.1,
            total_duty=85.7,
            trips=[],
            rationale=None
        )
    ]
    
    mock_preferences = PreferenceSchema(
        hard_constraints={"no_weekends": True, "no_redeyes": True},
        soft_prefs={"weekend_priority": 0.9, "credit_hours_weight": 0.7}
    )
    
    optimizer = LLMOptimizer()
    
    print("🧪 Testing LLM Optimizer")
    print("=" * 50)
    
    try:
        result = await optimizer.optimize_candidates(
            candidates=mock_candidates,
            preferences=mock_preferences,
            pilot_context={"base": "SFO", "seniority_percentile": 0.65}
        )
        
        print(f"✅ Optimization successful!")
        print(f"🎯 Confidence: {result.confidence:.2f}")
        print(f"🏆 Recommended: {result.recommended_candidate_id}")
        print(f"📊 Quality: {result.optimization_quality:.2f}")
        print(f"💡 Insights: {len(result.model_insights)} generated")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    # Run test if module executed directly
    asyncio.run(test_optimizer())