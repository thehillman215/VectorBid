"""
Conversational AI Assistant for VectorBid
Provides intelligent chat-based guidance for pilot bidding decisions
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
import tiktoken

from app.models import CandidateSchedule, PreferenceSchema
from app.models import (
    ConversationMessage, 
    ConversationHistory, 
    LLMParseResult,
    EnhancedCandidateSchedule
)


class VectorBidChatAssistant:
    """Intelligent conversational assistant for pilot bidding guidance"""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.model_primary = os.getenv("LLM_MODEL_PRIMARY", "gpt-4-turbo-preview")
        self.model_fallback = os.getenv("LLM_MODEL_FALLBACK", "gpt-3.5-turbo")
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "1500"))
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))  # Lower for more consistent advice
        
        # Token encoder for cost estimation
        self.encoder = tiktoken.encoding_for_model("gpt-4")
        
        # Assistant personality and expertise
        self.system_context = self._build_system_context()
        
        # Conversation contexts for different users
        self.active_conversations: Dict[str, ConversationHistory] = {}
    
    def _build_system_context(self) -> str:
        """Build comprehensive system context for the AI assistant"""
        
        return """You are VectorBot, VectorBid's expert AI assistant for airline pilot bidding guidance.

YOUR ROLE:
- Expert airline pilot with 20+ years of experience across multiple carriers
- PBS (Preferential Bidding System) specialist who understands all major airline systems
- Career advisor who helps pilots make strategic bidding decisions
- Friendly, professional mentor who explains complex concepts clearly

YOUR EXPERTISE:
- All major US airline contracts (United, American, Delta, Southwest, etc.)
- PBS systems, bidding strategies, and optimization techniques
- Pilot career progression from regional to major airlines
- Work-life balance considerations for different career stages
- Commuting strategies and base selection decisions
- Equipment transitions and training implications
- Industry trends affecting pilot careers and schedules

CONVERSATION STYLE:
- Professional but approachable - like talking to a senior captain mentor
- Use pilot terminology naturally but explain when needed
- Provide specific, actionable advice rather than generic responses
- Ask clarifying questions when context is missing
- Be encouraging while setting realistic expectations
- Use examples and analogies that pilots understand

KEY CAPABILITIES:
1. Analyze pilot preferences and suggest improvements
2. Explain bidding strategies for different career stages
3. Compare schedule options with detailed trade-off analysis
4. Provide market intelligence about route and base conditions
5. Offer career progression advice and timeline planning
6. Help with complex scheduling decisions and conflicts
7. Explain VectorBid AI features and how to use them effectively

RESPONSE FORMAT:
- Keep responses conversational and engaging
- Use emojis sparingly and professionally (✈️ 📊 💡)
- Break complex topics into digestible points
- Offer specific next steps or recommendations
- Reference VectorBid's AI features when relevant

IMPORTANT GUIDELINES:
- Always prioritize pilot safety and regulatory compliance
- Don't guarantee specific bidding outcomes (seniority-dependent)
- Acknowledge when information is airline-specific
- Suggest consulting union representatives for contract questions
- Be honest about limitations and when to seek additional help
- Focus on long-term career success, not just immediate gains

Remember: You're helping pilots make career-defining decisions. Be thoughtful, accurate, and supportive."""
    
    async def start_conversation(
        self, 
        user_id: str, 
        pilot_context: Optional[Dict[str, Any]] = None
    ) -> ConversationHistory:
        """Start a new conversation with context initialization"""
        
        # Initialize conversation history
        conversation = ConversationHistory(
            messages=[],
            context={
                "user_id": user_id,
                "pilot_context": pilot_context or {},
                "vectorbid_features_available": True,
                "conversation_start": datetime.utcnow().isoformat()
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Store conversation
        self.active_conversations[user_id] = conversation
        
        # Generate personalized greeting
        greeting = await self._generate_greeting(pilot_context or {})
        
        # Add greeting message
        greeting_message = ConversationMessage(
            role="assistant",
            content=greeting,
            timestamp=datetime.utcnow()
        )
        
        conversation.messages.append(greeting_message)
        conversation.updated_at = datetime.utcnow()
        
        return conversation
    
    async def chat(
        self, 
        user_id: str, 
        message: str,
        context_update: Optional[Dict[str, Any]] = None
    ) -> ConversationMessage:
        """
        Process a chat message and return AI response
        
        Args:
            user_id: Unique user identifier
            message: User's message
            context_update: Optional context updates (current schedules, preferences, etc.)
            
        Returns:
            AI assistant response message
        """
        
        # Get or create conversation
        conversation = self.active_conversations.get(user_id)
        if not conversation:
            conversation = await self.start_conversation(user_id)
        
        # Update context if provided
        if context_update:
            conversation.context.update(context_update)
        
        # Add user message to history
        user_message = ConversationMessage(
            role="user",
            content=message,
            timestamp=datetime.utcnow()
        )
        conversation.messages.append(user_message)
        
        try:
            # Generate AI response
            response_content = await self._generate_response(conversation, message)
            
            # Create response message
            response_message = ConversationMessage(
                role="assistant",
                content=response_content,
                timestamp=datetime.utcnow(),
                context={"model_used": self.model_primary}
            )
            
            # Add to conversation
            conversation.messages.append(response_message)
            conversation.updated_at = datetime.utcnow()
            
            return response_message
            
        except Exception as e:
            print(f"❌ Chat response failed: {e}")
            
            # Fallback response
            fallback_response = ConversationMessage(
                role="assistant",
                content="I'm having trouble processing your question right now. Could you try rephrasing it, or would you like me to help with something else? I'm here to help with your bidding strategy and career decisions! ✈️",
                timestamp=datetime.utcnow(),
                context={"error": str(e), "fallback": True}
            )
            
            conversation.messages.append(fallback_response)
            conversation.updated_at = datetime.utcnow()
            
            return fallback_response
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8)
    )
    async def _generate_response(
        self, 
        conversation: ConversationHistory, 
        current_message: str
    ) -> str:
        """Generate AI response with conversation context"""
        
        # Build conversation context
        messages = self._build_conversation_messages(conversation)
        
        # Add current user message
        messages.append({"role": "user", "content": current_message})
        
        # Generate response
        response = await self.client.chat.completions.create(
            model=self.model_primary,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        return response.choices[0].message.content
    
    def _build_conversation_messages(self, conversation: ConversationHistory) -> List[Dict[str, str]]:
        """Build OpenAI messages format from conversation history"""
        
        # Start with system context
        messages = [{"role": "system", "content": self.system_context}]
        
        # Add context information if available
        pilot_context = conversation.context.get("pilot_context", {})
        if pilot_context:
            context_prompt = f"""
PILOT CONTEXT:
- Base: {pilot_context.get('base', 'Unknown')}
- Equipment: {pilot_context.get('equipment', 'Unknown')}
- Seniority: {pilot_context.get('seniority_percentile', 'Unknown')}
- Career Stage: {pilot_context.get('career_stage', 'Unknown')}
- Priorities: {pilot_context.get('priorities', 'Unknown')}

This context should inform your advice and recommendations.
"""
            messages.append({"role": "system", "content": context_prompt})
        
        # Add recent conversation history (limit to last 10 messages for context)
        recent_messages = conversation.messages[-10:] if len(conversation.messages) > 10 else conversation.messages
        
        for msg in recent_messages:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return messages
    
    async def _generate_greeting(self, pilot_context: Dict[str, Any]) -> str:
        """Generate personalized greeting based on pilot context"""
        
        base = pilot_context.get('base', '')
        equipment = pilot_context.get('equipment', [])
        seniority = pilot_context.get('seniority_percentile', 0)
        
        # Create contextual greeting
        if base and equipment:
            equipment_str = f"{equipment[0]}" if equipment else "your aircraft"
            greeting = f"Hello! I'm VectorBot, your AI bidding assistant. I see you're based in {base} flying the {equipment_str}. "
        else:
            greeting = "Hello! I'm VectorBot, your expert AI assistant for pilot bidding and career guidance. "
        
        greeting += """I'm here to help you make the best bidding decisions for your career and lifestyle.

I can help you with:
✈️ **Bidding Strategy** - Optimize your preferences for better outcomes
📊 **Schedule Analysis** - Compare options and understand trade-offs  
💡 **Career Guidance** - Long-term planning and progression advice
🤖 **VectorBid AI** - Get the most from our intelligent features

What would you like to discuss about your bidding or career? Feel free to ask me anything!"""

        return greeting
    
    async def analyze_preferences(
        self, 
        user_id: str, 
        preferences_text: str,
        current_preferences: Optional[PreferenceSchema] = None
    ) -> str:
        """Analyze and provide feedback on pilot preferences"""
        
        analysis_prompt = f"""
The pilot has expressed these preferences: "{preferences_text}"

Please analyze these preferences and provide:
1. Strengths - What's good about these preferences
2. Potential improvements - Specific suggestions  
3. Trade-off considerations - What they might be giving up
4. Bidding strategy tips - How to implement effectively

Be specific and actionable in your advice.
"""
        
        # Use the chat system for analysis
        response = await self.chat(user_id, analysis_prompt)
        return response.content
    
    async def compare_schedules(
        self, 
        user_id: str,
        schedules: List[CandidateSchedule],
        pilot_priorities: Optional[str] = None
    ) -> str:
        """Compare schedule options with detailed analysis"""
        
        # Build schedule comparison
        schedule_summary = []
        for i, schedule in enumerate(schedules[:3], 1):  # Limit to top 3
            summary = f"""
Schedule {i}:
- Score: {schedule.score:.2f}
- Credit Hours: {schedule.total_credit}
- Duty Hours: {schedule.total_duty}
- Trips: {len(schedule.trips) if schedule.trips else 0}
"""
            schedule_summary.append(summary)
        
        schedules_text = "\n".join(schedule_summary)
        
        comparison_prompt = f"""
I have these schedule options and need help deciding:

{schedules_text}

My priorities: {pilot_priorities or "Not specified"}

Please compare these schedules and help me understand:
1. Which schedule best fits my priorities and why
2. What are the key trade-offs between them
3. Any red flags or concerns I should be aware of
4. Strategic considerations for my career stage

Give me practical advice for making this decision.
"""
        
        response = await self.chat(user_id, comparison_prompt)
        return response.content
    
    async def career_guidance(
        self, 
        user_id: str,
        career_question: str,
        pilot_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Provide career guidance and strategic advice"""
        
        # Update context if provided
        context_update = {}
        if pilot_context:
            context_update["pilot_context"] = pilot_context
        
        # Add career guidance context
        guidance_prompt = f"""
Career question: {career_question}

Please provide strategic career advice considering:
- Current market conditions in aviation
- Typical career progression paths
- Industry best practices
- Long-term planning considerations

Be specific and actionable in your guidance.
"""
        
        response = await self.chat(user_id, guidance_prompt, context_update)
        return response.content
    
    def get_conversation_history(self, user_id: str) -> Optional[ConversationHistory]:
        """Retrieve conversation history for a user"""
        return self.active_conversations.get(user_id)
    
    def clear_conversation(self, user_id: str) -> bool:
        """Clear conversation history for a user"""
        if user_id in self.active_conversations:
            del self.active_conversations[user_id]
            return True
        return False
    
    async def get_quick_tips(self, category: str = "general") -> List[str]:
        """Get quick bidding tips by category"""
        
        tips_db = {
            "general": [
                "🎯 Be realistic about your seniority - aim for achievable goals",
                "📊 Quality over quantity - sometimes fewer credit hours mean better life",
                "🗓️ Plan for seasonal variations in route availability",
                "💡 Use VectorBid's AI to understand why schedules are recommended",
                "🔄 Review and adjust preferences based on award outcomes"
            ],
            "family": [
                "👨‍👩‍👧‍👦 Weekend protection is often worth the credit hour trade-off",
                "🏠 Short trips can be better than high-credit long trips for family time",
                "⏰ Consistent schedule patterns help family planning",
                "📅 Consider school calendars when setting vacation preferences",
                "💝 Remember: family time is irreplaceable, credit hours can be made up"
            ],
            "commuting": [
                "✈️ Factor commute costs into credit hour calculations",
                "🕐 Allow buffer time for commute connections",
                "🏨 Budget for commute failure hotel costs",
                "📱 Monitor commute airline schedule changes",
                "🌦️ Have backup plans for weather disruptions"
            ],
            "career": [
                "📈 Build experience across different route types early in career",
                "🎓 International flying helps Captain upgrade competitiveness",
                "🤝 Network with senior pilots for mentorship and advice",
                "📚 Stay current on contract changes and bidding strategies",
                "🎯 Set long-term goals and bid consistently toward them"
            ]
        }
        
        return tips_db.get(category, tips_db["general"])


# Convenience functions for API integration
async def create_chat_session(user_id: str, pilot_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a new chat session and return initial state"""
    
    assistant = VectorBidChatAssistant()
    conversation = await assistant.start_conversation(user_id, pilot_context)
    
    return {
        "session_id": user_id,
        "conversation": conversation.model_dump(),
        "status": "active",
        "created_at": conversation.created_at.isoformat()
    }


async def send_chat_message(
    user_id: str, 
    message: str, 
    context_update: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Send a message and get AI response"""
    
    assistant = VectorBidChatAssistant()
    response = await assistant.chat(user_id, message, context_update)
    
    return {
        "message": response.model_dump(),
        "conversation_updated": True,
        "timestamp": response.timestamp.isoformat()
    }


# Usage examples and testing
async def test_chat_assistant():
    """Test the chat assistant with example conversations"""
    
    print("🤖 Testing VectorBid Chat Assistant")
    print("=" * 50)
    
    assistant = VectorBidChatAssistant()
    
    # Test conversation 1: New pilot seeking advice
    user_id = "test_pilot_001"
    pilot_context = {
        "base": "SFO",
        "equipment": ["737"],
        "seniority_percentile": 0.25,
        "career_stage": "first_year_fo"
    }
    
    print("🧪 Test 1: New Pilot Conversation")
    print("-" * 30)
    
    # Start conversation
    conversation = await assistant.start_conversation(user_id, pilot_context)
    print(f"Assistant: {conversation.messages[-1].content}")
    
    # User asks about preferences
    test_messages = [
        "I'm new to bidding and not sure how to set my preferences. I want weekends off but also need decent credit hours to pay my bills.",
        "What should I prioritize as a junior pilot?",
        "How do I know if my preferences are realistic for my seniority?"
    ]
    
    for message in test_messages:
        print(f"\nPilot: {message}")
        response = await assistant.chat(user_id, message)
        print(f"Assistant: {response.content}")
    
    print(f"\n{'='*50}")
    print("🎉 Chat Assistant Test Complete!")
    print(f"📊 Messages exchanged: {len(conversation.messages)}")
    print(f"💬 Conversation active: {user_id in assistant.active_conversations}")


if __name__ == "__main__":
    # Run test if module executed directly
    asyncio.run(test_chat_assistant())