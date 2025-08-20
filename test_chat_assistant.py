#!/usr/bin/env python3
"""
Test script for VectorBot Chat Assistant
Run this to verify the conversational AI is working
"""

import asyncio
import json
import os
from pathlib import Path

# Add the app directory to the path
import sys
sys.path.append(str(Path(__file__).parent))

async def test_chat_assistant_basic():
    """Test basic chat functionality"""
    
    print("🤖 Testing VectorBot Chat Assistant")
    print("=" * 60)
    
    # Check if API key is set
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set - will test fallback only")
        print("   Set your OpenAI API key to test full chat functionality")
        print("   export OPENAI_API_KEY='your-key-here'")
    else:
        print(f"✅ OpenAI API key found: {api_key[:10]}...")
    
    try:
        from app.services.chat_assistant import VectorBidChatAssistant
        print("✅ Chat assistant imported successfully")
        
        assistant = VectorBidChatAssistant()
        print("✅ Assistant initialized")
        
        # Test Case 1: New pilot conversation
        print("\n🧪 Test Case 1: New Pilot Seeking Guidance")
        print("-" * 50)
        
        user_id = "test_pilot_001"
        pilot_context = {
            "base": "SFO",
            "equipment": ["737"],
            "seniority_percentile": 0.25,
            "career_stage": "first_year_fo"
        }
        
        # Start conversation
        conversation = await assistant.start_conversation(user_id, pilot_context)
        print(f"🤖 VectorBot: {conversation.messages[-1].content[:100]}...")
        
        # Test messages
        test_messages = [
            "I'm new to bidding and confused about how to set my preferences. Can you help?",
            "I want weekends off but also need decent credit hours. Is this realistic?",
            "What should a junior pilot like me focus on?"
        ]
        
        for message in test_messages:
            print(f"\n👨‍✈️ Pilot: {message}")
            response = await assistant.chat(user_id, message)
            print(f"🤖 VectorBot: {response.content[:150]}...")
            print(f"   📊 Confidence: Generated at {response.timestamp}")
        
        print(f"\n✅ Conversation completed with {len(conversation.messages)} messages")
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("   Make sure dependencies are installed:")
        print("   pip install openai anthropic tiktoken tenacity")
    except Exception as e:
        print(f"❌ Test failed: {e}")


async def test_preference_analysis():
    """Test preference analysis functionality"""
    print("\n📊 Testing Preference Analysis")
    print("=" * 50)
    
    try:
        from app.services.chat_assistant import VectorBidChatAssistant
        
        assistant = VectorBidChatAssistant()
        user_id = "test_pilot_002"
        
        # Start conversation with context
        pilot_context = {
            "base": "ORD",
            "equipment": ["777"],
            "seniority_percentile": 0.75,
            "career_stage": "captain"
        }
        
        await assistant.start_conversation(user_id, pilot_context)
        
        # Test preference analysis
        preferences_text = "I want to maximize credit hours but still have some weekends off. I prefer international flying and don't mind longer trips if they're efficient."
        
        print(f"👨‍✈️ Analyzing preferences: '{preferences_text}'")
        
        analysis = await assistant.analyze_preferences(user_id, preferences_text)
        
        print(f"🤖 Analysis: {analysis[:200]}...")
        print("✅ Preference analysis completed")
        
    except Exception as e:
        print(f"❌ Preference analysis failed: {e}")


async def test_schedule_comparison():
    """Test schedule comparison functionality"""
    print("\n⚖️ Testing Schedule Comparison")
    print("=" * 50)
    
    try:
        from app.services.chat_assistant import VectorBidChatAssistant
        from app.models import CandidateSchedule
        
        assistant = VectorBidChatAssistant()
        user_id = "test_pilot_003"
        
        # Mock schedules for comparison
        mock_schedules = [
            CandidateSchedule(
                candidate_id="schedule_a",
                score=0.85,
                total_credit=88.5,
                total_duty=76.2,
                trips=[]
            ),
            CandidateSchedule(
                candidate_id="schedule_b",
                score=0.82,
                total_credit=95.1,
                total_duty=82.7,
                trips=[]
            ),
            CandidateSchedule(
                candidate_id="schedule_c",
                score=0.79,
                total_credit=78.3,
                total_duty=68.9,
                trips=[]
            )
        ]
        
        pilot_priorities = "family time is most important, but I need at least 80 credit hours"
        
        print(f"👨‍✈️ Comparing {len(mock_schedules)} schedules with priorities: '{pilot_priorities}'")
        
        comparison = await assistant.compare_schedules(user_id, mock_schedules, pilot_priorities)
        
        print(f"🤖 Comparison: {comparison[:200]}...")
        print("✅ Schedule comparison completed")
        
    except Exception as e:
        print(f"❌ Schedule comparison failed: {e}")


async def test_career_guidance():
    """Test career guidance functionality"""
    print("\n🎯 Testing Career Guidance")
    print("=" * 50)
    
    try:
        from app.services.chat_assistant import VectorBidChatAssistant
        
        assistant = VectorBidChatAssistant()
        user_id = "test_pilot_004"
        
        career_questions = [
            "I'm a regional pilot looking to transition to a major airline. What should I focus on in my bidding to prepare?",
            "Should I prioritize international flying for Captain upgrade opportunities?",
            "I'm thinking about changing bases. What factors should I consider?"
        ]
        
        pilot_context = {
            "base": "DEN",
            "equipment": ["EMB175"],
            "seniority_percentile": 0.60,
            "career_stage": "regional_captain"
        }
        
        for question in career_questions:
            print(f"\n👨‍✈️ Career Question: {question[:80]}...")
            
            guidance = await assistant.career_guidance(user_id, question, pilot_context)
            
            print(f"🤖 Guidance: {guidance[:150]}...")
        
        print("✅ Career guidance tests completed")
        
    except Exception as e:
        print(f"❌ Career guidance failed: {e}")


async def test_quick_tips():
    """Test quick tips functionality"""
    print("\n💡 Testing Quick Tips")
    print("=" * 50)
    
    try:
        from app.services.chat_assistant import VectorBidChatAssistant
        
        assistant = VectorBidChatAssistant()
        
        categories = ["general", "family", "commuting", "career"]
        
        for category in categories:
            tips = await assistant.get_quick_tips(category)
            print(f"\n📋 {category.upper()} TIPS:")
            for i, tip in enumerate(tips[:3], 1):
                print(f"  {i}. {tip}")
        
        print("✅ Quick tips test completed")
        
    except Exception as e:
        print(f"❌ Quick tips failed: {e}")


async def test_conversation_persistence():
    """Test conversation history and persistence"""
    print("\n💾 Testing Conversation Persistence")
    print("=" * 50)
    
    try:
        from app.services.chat_assistant import VectorBidChatAssistant
        
        assistant = VectorBidChatAssistant()
        user_id = "test_pilot_005"
        
        # Start conversation
        await assistant.start_conversation(user_id)
        
        # Send several messages
        messages = [
            "Hello, I need help with bidding",
            "I'm based in LAX and fly 737s", 
            "What's the best strategy for weekend time off?"
        ]
        
        for message in messages:
            await assistant.chat(user_id, message)
        
        # Get conversation history
        history = assistant.get_conversation_history(user_id)
        
        print(f"✅ Conversation stored with {len(history.messages)} messages")
        print(f"📅 Created: {history.created_at}")
        print(f"🔄 Updated: {history.updated_at}")
        
        # Clear conversation
        cleared = assistant.clear_conversation(user_id)
        print(f"🗑️ Conversation cleared: {cleared}")
        
        # Verify cleared
        history_after = assistant.get_conversation_history(user_id)
        print(f"✅ Conversation properly cleared: {history_after is None}")
        
    except Exception as e:
        print(f"❌ Conversation persistence failed: {e}")


async def test_api_endpoints():
    """Test API endpoints for chat functionality"""
    print("\n🌐 Testing Chat API Endpoints")
    print("=" * 50)
    
    try:
        import requests
        
        base_url = "http://localhost:8000/api"
        
        # Test start chat session
        start_payload = {
            "user_id": "api_test_pilot",
            "pilot_context": {
                "base": "SFO",
                "equipment": ["737"],
                "seniority_percentile": 0.45
            }
        }
        
        print("📡 Testing /chat/start endpoint...")
        response = requests.post(f"{base_url}/chat/start", json=start_payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Chat session started: {result['session_id']}")
            print(f"🤖 Greeting: {result['greeting_message'][:80]}...")
        else:
            print(f"❌ Start chat failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
        # Test send message
        message_payload = {
            "user_id": "api_test_pilot",
            "message": "What should I prioritize as a mid-seniority pilot?"
        }
        
        print("\n📡 Testing /chat/message endpoint...")
        response = requests.post(f"{base_url}/chat/message", json=message_payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Message processed successfully")
            print(f"🤖 Response: {result['response'][:100]}...")
        else:
            print(f"❌ Send message failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
        
        # Test get tips
        print("\n📡 Testing /chat/tips/family endpoint...")
        response = requests.get(f"{base_url}/chat/tips/family", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Tips retrieved: {len(result['tips'])} family tips")
            for i, tip in enumerate(result['tips'][:2], 1):
                print(f"  {i}. {tip}")
        else:
            print(f"❌ Get tips failed: {response.status_code}")
            
    except ImportError:
        print("⚠️ requests library not available - skipping API tests")
        print("   Install with: pip install requests")
    except Exception as e:
        print(f"❌ API test failed: {e}")
        print("   Make sure the server is running: uvicorn app.main:app --reload")


async def test_realistic_conversation():
    """Test a realistic pilot conversation scenario"""
    print("\n🎭 Testing Realistic Pilot Conversation")
    print("=" * 60)
    
    try:
        from app.services.chat_assistant import VectorBidChatAssistant
        
        assistant = VectorBidChatAssistant()
        user_id = "realistic_pilot"
        
        # Realistic pilot context
        pilot_context = {
            "base": "EWR",
            "equipment": ["737-800"],
            "seniority_percentile": 0.55,
            "career_stage": "captain",
            "years_experience": 8
        }
        
        # Start conversation
        conversation = await assistant.start_conversation(user_id, pilot_context)
        print(f"🤖 {conversation.messages[-1].content[:120]}...")
        
        # Realistic conversation flow
        realistic_flow = [
            "Hi VectorBot! I'm having trouble with my upcoming bid. I usually get decent schedules but this month looks different.",
            "My main priorities are spending time with my teenage kids and maintaining at least 85 credit hours for the mortgage. Is that reasonable?", 
            "I've been looking at the routes and it seems like there are more red-eyes available than usual. Should I consider them for the extra credit?",
            "What about commuting? I live about 90 minutes from EWR. Should I consider the overnight layovers to reduce commute days?",
            "One more question - I'm thinking about bidding Captain on the 757 eventually. Should I start adding some international preferences to build experience?"
        ]
        
        for i, message in enumerate(realistic_flow, 1):
            print(f"\n👨‍✈️ Captain Johnson: {message}")
            response = await assistant.chat(user_id, message)
            print(f"🤖 VectorBot: {response.content[:180]}...")
            
            # Simulate thinking time
            await asyncio.sleep(0.5)
        
        print(f"\n✅ Realistic conversation completed!")
        print(f"📊 Total messages: {len(conversation.messages)}")
        print(f"🎯 Conversation demonstrates real-world pilot concerns and AI guidance")
        
    except Exception as e:
        print(f"❌ Realistic conversation failed: {e}")


if __name__ == "__main__":
    print("VectorBot Chat Assistant Test Suite")
    print("=" * 60)
    
    # Run all tests
    asyncio.run(test_chat_assistant_basic())
    asyncio.run(test_preference_analysis()) 
    asyncio.run(test_schedule_comparison())
    asyncio.run(test_career_guidance())
    asyncio.run(test_quick_tips())
    asyncio.run(test_conversation_persistence())
    asyncio.run(test_realistic_conversation())
    
    # API tests (optional)
    answer = input("\n🤔 Test chat API endpoints? (requires server running) [y/N]: ")
    if answer.lower() in ['y', 'yes']:
        asyncio.run(test_api_endpoints())
    
    print("\n✨ All chat assistant tests complete!")
    print("\n🚀 Next Steps:")
    print("   1. Start the server: uvicorn app.main:app --reload")
    print("   2. Test chat endpoints at http://localhost:8000/docs")
    print("   3. Try the /api/chat/start endpoint with pilot context")
    print("   4. Send messages to /api/chat/message")
    print("   5. Get tips from /api/chat/tips/[category]")
    print("   6. Build frontend chat interface with these APIs")
    print("\n💡 Demo Script Ideas:")
    print("   • Show live conversation with VectorBot about bidding strategy")
    print("   • Compare schedules with AI explanation and trade-off analysis")
    print("   • Get personalized career advice based on pilot context")
    print("   • Demonstrate preference analysis with improvement suggestions")