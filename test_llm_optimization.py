#!/usr/bin/env python3
"""
Test script for LLM-guided optimization engine
Run this to verify the AI optimization enhancement is working
"""

import asyncio
import json
import os
from pathlib import Path

# Add the app directory to the path
import sys
sys.path.append(str(Path(__file__).parent))

async def test_llm_optimizer():
    """Test the LLM optimization engine"""
    
    print("🧠 Testing LLM-Guided Optimization Engine")
    print("=" * 60)
    
    # Check if API key is set
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set - will test fallback only")
        print("   Set your OpenAI API key to test full LLM functionality")
        print("   export OPENAI_API_KEY='your-key-here'")
    else:
        print(f"✅ OpenAI API key found: {api_key[:10]}...")
    
    try:
        from app.services.llm_optimizer import LLMOptimizer
        from app.models import CandidateSchedule, PreferenceSchema
        from app.models.enhanced import OptimizationMethod
        
        print("✅ LLM optimizer imported successfully")
        
        optimizer = LLMOptimizer()
        print("✅ Optimizer initialized")
        
        # Create mock candidate schedules
        mock_candidates = [
            CandidateSchedule(
                candidate_id="candidate_001",
                score=0.85,
                total_credit=85.5,
                total_duty=78.2,
                trips=[],
                rationale=None
            ),
            CandidateSchedule(
                candidate_id="candidate_002", 
                score=0.82,
                total_credit=92.1,
                total_duty=85.7,
                trips=[],
                rationale=None
            ),
            CandidateSchedule(
                candidate_id="candidate_003",
                score=0.80,
                total_credit=75.3,
                total_duty=70.1,
                trips=[],
                rationale=None
            )
        ]
        
        # Create mock preferences
        mock_preferences = PreferenceSchema(
            hard_constraints={"no_weekends": True, "no_redeyes": True},
            soft_prefs={
                "weekend_priority": 0.9, 
                "credit_hours_weight": 0.7,
                "departure_time_weight": 0.6
            }
        )
        
        # Test cases
        test_cases = [
            {
                "name": "Family-First Pilot",
                "pilot_context": {
                    "base": "SFO", 
                    "equipment": ["737", "757"], 
                    "seniority_percentile": 0.45,
                    "lifestyle": "family_first"
                },
                "description": "Pilot prioritizing family time and work-life balance"
            },
            {
                "name": "Credit Maximizer",
                "pilot_context": {
                    "base": "ORD",
                    "equipment": ["777"],
                    "seniority_percentile": 0.85,
                    "lifestyle": "credit_focused"
                },
                "description": "Senior pilot focused on maximizing credit hours"
            },
            {
                "name": "Commuter Pilot",
                "pilot_context": {
                    "base": "DEN",
                    "equipment": ["737"],
                    "seniority_percentile": 0.25,
                    "lifestyle": "commuter"
                },
                "description": "Junior pilot who needs to commute to base"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🧪 Test Case {i}: {test_case['name']}")
            print(f"📝 {test_case['description']}")
            print("-" * 50)
            
            try:
                result = await optimizer.optimize_candidates(
                    candidates=mock_candidates,
                    preferences=mock_preferences,
                    pilot_context=test_case["pilot_context"]
                )
                
                print(f"✅ Success: {result.optimization_method.value}")
                print(f"🎯 Confidence: {result.confidence:.2f}")
                print(f"📊 Quality: {result.optimization_quality:.2f}")
                print(f"🎪 Preference Alignment: {result.preference_alignment:.2f}")
                print(f"🏆 Recommended: {result.recommended_candidate_id}")
                print(f"📝 Explanation: {result.explanation[:100]}...")
                
                # Show enhanced candidates
                print(f"📋 Enhanced Candidates ({len(result.enhanced_candidates)}):")
                for j, candidate in enumerate(result.enhanced_candidates[:3], 1):
                    print(f"  {j}. {candidate.candidate_id}: "
                          f"Enhanced={candidate.enhanced_score:.2f}, "
                          f"Fit={candidate.pilot_fit_score:.2f}")
                    if candidate.ai_reasoning:
                        print(f"     💭 {candidate.ai_reasoning[:80]}...")
                
                # Show key insights
                if result.model_insights:
                    print(f"💡 AI Insights:")
                    for insight in result.model_insights[:2]:
                        print(f"  • {insight}")
                
                # Show trade-offs
                if result.trade_off_analysis:
                    print(f"⚖️ Trade-offs: {result.trade_off_analysis[:80]}...")
                
                print(f"🧠 Model: {result.model_version}")
                print(f"💰 Tokens: {result.tokens_used}")
                    
            except Exception as e:
                print(f"❌ Failed: {e}")
        
        print(f"\n{'='*60}")
        print("🎉 LLM Optimization Engine Test Complete!")
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("   Make sure dependencies are installed:")
        print("   pip install openai anthropic tiktoken tenacity")
    except Exception as e:
        print(f"❌ Test failed: {e}")


async def test_schedule_explanation():
    """Test the schedule choice explanation feature"""
    print("\n📖 Testing Schedule Choice Explanation")
    print("=" * 50)
    
    try:
        from app.services.llm_optimizer import LLMOptimizer
        from app.models import CandidateSchedule, PreferenceSchema
        
        optimizer = LLMOptimizer()
        
        # Mock chosen candidate
        chosen = CandidateSchedule(
            candidate_id="best_choice",
            score=0.92,
            total_credit=88.0,
            total_duty=76.5,
            trips=[],
            rationale=None
        )
        
        # Mock alternatives
        alternatives = [
            CandidateSchedule(
                candidate_id="alternative_1",
                score=0.88,
                total_credit=95.0,
                total_duty=82.0,
                trips=[],
                rationale=None
            ),
            CandidateSchedule(
                candidate_id="alternative_2",
                score=0.85,
                total_credit=78.0,
                total_duty=72.0,
                trips=[],
                rationale=None
            )
        ]
        
        # Mock preferences
        preferences = PreferenceSchema(
            hard_constraints={"no_weekends": True},
            soft_prefs={"weekend_priority": 0.9, "credit_hours_weight": 0.6}
        )
        
        pilot_context = {
            "base": "SFO",
            "family_status": "married_with_kids",
            "seniority_percentile": 0.55
        }
        
        print("🤔 Generating schedule choice explanation...")
        
        explanation = await optimizer.explain_schedule_choice(
            chosen_candidate=chosen,
            alternatives=alternatives,
            preferences=preferences,
            pilot_context=pilot_context
        )
        
        print("✅ Explanation generated!")
        print(f"📋 Choice Explanation: {explanation.get('choice_explanation', 'N/A')[:100]}...")
        print(f"⚖️ Comparison: {explanation.get('comparison_analysis', 'N/A')[:100]}...")
        print(f"🏠 Lifestyle Impact: {explanation.get('lifestyle_impact', 'N/A')[:100]}...")
        print(f"📈 Career Implications: {explanation.get('career_implications', 'N/A')[:100]}...")
        
        if explanation.get('potential_concerns'):
            print(f"⚠️ Concerns: {len(explanation['potential_concerns'])} identified")
        
        if explanation.get('optimization_tips'):
            print(f"💡 Tips: {explanation.get('optimization_tips', 'N/A')[:80]}...")
        
    except Exception as e:
        print(f"❌ Explanation test failed: {e}")


async def test_api_integration():
    """Test the enhanced optimization API endpoint"""
    print("\n🌐 Testing Enhanced Optimization API")
    print("=" * 50)
    
    try:
        import requests
        
        # Test the enhanced optimization endpoint
        url = "http://localhost:8000/api/optimize_enhanced"
        
        # Mock feature bundle (simplified)
        test_payload = {
            "feature_bundle": {
                "context": {
                    "pilot_id": "test_pilot",
                    "airline": "UAL",
                    "base": "SFO",
                    "bid_period": "2025-09"
                },
                "preference_schema": {
                    "hard_constraints": {"no_weekends": True, "no_redeyes": True},
                    "soft_prefs": {
                        "weekend_priority": 0.9,
                        "credit_hours_weight": 0.7,
                        "departure_time_weight": 0.6
                    }
                },
                "analytics_features": {},
                "compliance_flags": {},
                "pairing_features": {"pairings": []}
            },
            "K": 10,
            "use_llm": True,
            "pilot_context": {
                "base": "SFO",
                "equipment": ["737"],
                "seniority_percentile": 0.65,
                "lifestyle": "family_first"
            }
        }
        
        print(f"📡 Making request to {url}")
        print(f"📦 Payload includes feature bundle and pilot context")
        
        response = requests.post(url, json=test_payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API Request Successful!")
            
            analysis = result.get('optimization_analysis', {})
            print(f"📊 Quality: {analysis.get('quality', 0):.2f}")
            print(f"🎯 Preference Alignment: {analysis.get('preference_alignment', 0):.2f}")
            
            recommendations = result.get('recommendations', {})
            print(f"🏆 Recommended: {recommendations.get('recommended_candidate_id', 'N/A')}")
            print(f"📝 Explanation: {recommendations.get('explanation', 'N/A')[:80]}...")
            
            ai_insights = result.get('ai_insights', {})
            print(f"🧠 Method: {ai_insights.get('method', 'unknown')}")
            print(f"🎯 Confidence: {ai_insights.get('confidence', 0):.2f}")
            print(f"💰 Tokens: {ai_insights.get('tokens_used', 'N/A')}")
            
            enhanced_candidates = result.get('enhanced_candidates', [])
            print(f"📋 Enhanced Candidates: {len(enhanced_candidates)}")
            
        else:
            print(f"❌ API Request Failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except ImportError:
        print("⚠️ requests library not available - skipping API test")
        print("   Install with: pip install requests")
    except Exception as e:
        print(f"❌ API test failed: {e}")
        print("   Make sure the server is running: uvicorn app.main:app --reload")


if __name__ == "__main__":
    print("VectorBid LLM-Guided Optimization Test")
    print("=" * 60)
    
    # Run LLM optimizer test
    asyncio.run(test_llm_optimizer())
    
    # Run schedule explanation test
    asyncio.run(test_schedule_explanation())
    
    # Run API integration test (optional)
    answer = input("\n🤔 Test enhanced optimization API? (requires server running) [y/N]: ")
    if answer.lower() in ['y', 'yes']:
        asyncio.run(test_api_integration())
    
    print("\n✨ All optimization tests complete!")
    print("\n🚀 Next Steps:")
    print("   1. Run the server: uvicorn app.main:app --reload")
    print("   2. Test the /api/optimize_enhanced endpoint")
    print("   3. Compare results with /api/optimize (mathematical only)")
    print("   4. Integrate with frontend for AI-guided bidding")