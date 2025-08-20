#!/usr/bin/env python3
"""
Test script for LLM integration
Run this to verify the LLM preference parser is working
"""

import asyncio
import os
from pathlib import Path

# Add the app directory to the path
import sys
sys.path.append(str(Path(__file__).parent))

async def test_llm_parser():
    """Test the LLM preference parser"""
    
    print("🧪 Testing LLM Preference Parser")
    print("=" * 50)
    
    # Check if API key is set
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set - will test fallback only")
        print("   Set your OpenAI API key to test full LLM functionality")
        print("   export OPENAI_API_KEY='your-key-here'")
    else:
        print(f"✅ OpenAI API key found: {api_key[:10]}...")
    
    try:
        from app.services.llm_parser import PreferenceParser
        print("✅ LLM parser imported successfully")
        
        parser = PreferenceParser()
        print("✅ Parser initialized")
        
        # Test cases
        test_cases = [
            {
                "text": "I want weekends off and prefer morning departures, avoid red-eyes",
                "context": {"base": "SFO", "equipment": ["737", "757"], "seniority_percentile": 0.65}
            },
            {
                "text": "Maximize my credit hours but keep trips under 4 days", 
                "context": {"base": "ORD", "equipment": ["777"], "seniority_percentile": 0.85}
            },
            {
                "text": "Family first - weekends and holidays off, short trips only",
                "persona": "family_first",
                "context": {"base": "EWR", "equipment": ["737"], "seniority_percentile": 0.45}
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🧪 Test Case {i}: '{test_case['text']}'")
            print("-" * 40)
            
            try:
                result = await parser.parse_preferences(
                    text=test_case["text"],
                    persona=test_case.get("persona"),
                    pilot_context=test_case["context"]
                )
                
                print(f"✅ Success: {result.parsing_method.value}")
                print(f"🎯 Confidence: {result.confidence:.2f}")
                print(f"🧠 Model: {result.model_version}")
                print(f"💰 Tokens: {result.tokens_used}")
                print(f"📝 Reasoning: {result.reasoning}")
                
                # Show parsed preferences
                prefs = result.preferences
                print(f"🔒 Hard Constraints: {prefs.hard_constraints}")
                print(f"⚖️  Soft Preferences: {prefs.soft_prefs}")
                
                if result.suggestions:
                    print(f"💡 Suggestions: {result.suggestions}")
                if result.warnings:
                    print(f"⚠️  Warnings: {result.warnings}")
                    
            except Exception as e:
                print(f"❌ Failed: {e}")
        
        print(f"\n{'='*50}")
        print("🎉 LLM Integration Test Complete!")
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("   Make sure dependencies are installed:")
        print("   pip install openai anthropic tiktoken tenacity")
    except Exception as e:
        print(f"❌ Test failed: {e}")


async def test_api_integration():
    """Test the API integration"""
    print("\n🌐 Testing API Integration")
    print("=" * 50)
    
    try:
        import requests
        import json
        
        # Test the parse_preferences endpoint
        url = "http://localhost:8000/api/parse_preferences"
        
        test_payload = {
            "preferences_text": "I want weekends off and prefer morning departures",
            "persona": "family_first",
            "airline": "UAL",
            "pilot_context": {
                "base": "SFO",
                "equipment": ["737"],
                "seniority_percentile": 0.65
            }
        }
        
        print(f"📡 Making request to {url}")
        print(f"📦 Payload: {json.dumps(test_payload, indent=2)}")
        
        response = requests.post(url, json=test_payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API Request Successful!")
            print(f"📊 Method: {result.get('method', 'unknown')}")
            print(f"🎯 Confidence: {result.get('confidence', 0):.2f}")
            print(f"📝 Reasoning: {result.get('reasoning', 'N/A')}")
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
    print("VectorBid LLM Integration Test")
    print("=" * 50)
    
    # Run LLM parser test
    asyncio.run(test_llm_parser())
    
    # Run API integration test (optional)
    answer = input("\n🤔 Test API integration? (requires server running) [y/N]: ")
    if answer.lower() in ['y', 'yes']:
        asyncio.run(test_api_integration())
    
    print("\n✨ All tests complete!")