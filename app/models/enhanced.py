"""
Enhanced data models with LLM integration support
Extends existing models with AI fields while maintaining backward compatibility
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum

from app.models import PreferenceSchema, CandidateSchedule


class ParsingMethod(str, Enum):
    """Method used to parse user preferences"""
    LLM = "llm"
    FALLBACK = "fallback"
    MANUAL = "manual"
    HYBRID = "hybrid"


class ConfidenceLevel(str, Enum):
    """User-friendly confidence levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class LLMParseResult(BaseModel):
    """Result from LLM preference parsing"""
    preferences: PreferenceSchema
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0.0-1.0")
    reasoning: str = Field(..., description="LLM's reasoning for the parsing")
    suggestions: List[str] = Field(default_factory=list, description="AI suggestions for improvement")
    warnings: List[str] = Field(default_factory=list, description="Potential issues or conflicts")
    parsing_method: ParsingMethod = Field(..., description="Method used for parsing")
    model_version: Optional[str] = Field(None, description="LLM model version used")
    tokens_used: Optional[int] = Field(None, description="Number of tokens consumed")
    
    @validator('confidence')
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v


class EnhancedPreferenceSchema(PreferenceSchema):
    """Extended PreferenceSchema with LLM fields"""
    
    # Original user input
    natural_language_input: Optional[str] = Field(
        None, 
        description="Original user text input",
        example="I want weekends off and prefer morning departures, avoid red-eyes"
    )
    persona_context: Optional[str] = Field(
        None, 
        description="Persona selected by user",
        example="family_first"
    )
    
    # LLM processing metadata
    parsing_confidence: Optional[float] = Field(
        None, 
        ge=0.0, 
        le=1.0, 
        description="LLM confidence in parsing accuracy"
    )
    llm_reasoning: Optional[str] = Field(
        None, 
        description="LLM's explanation of how it parsed the preferences"
    )
    llm_suggestions: Optional[List[str]] = Field(
        default_factory=list, 
        description="AI suggestions for improving preferences"
    )
    llm_warnings: Optional[List[str]] = Field(
        default_factory=list, 
        description="AI-identified potential issues"
    )
    
    # Processing metadata
    parsed_at: Optional[datetime] = Field(
        None, 
        description="When the preferences were parsed"
    )
    parsing_method: ParsingMethod = Field(
        ParsingMethod.MANUAL, 
        description="Method used to generate these preferences"
    )
    model_version: Optional[str] = Field(
        None, 
        description="LLM model version if applicable"
    )
    
    # Pilot context for personalization
    pilot_context: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional pilot context for personalization"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ScheduleProsCons(BaseModel):
    """Pros and cons analysis for a schedule"""
    pros: List[str] = Field(default_factory=list, description="Positive aspects of the schedule")
    cons: List[str] = Field(default_factory=list, description="Negative aspects of the schedule")
    trade_offs: List[str] = Field(default_factory=list, description="Trade-offs made in optimization")


class RiskAssessment(BaseModel):
    """Risk analysis for a schedule"""
    risk_level: ConfidenceLevel = Field(..., description="Overall risk level")
    risk_factors: List[str] = Field(default_factory=list, description="Specific risk factors identified")
    mitigation_suggestions: List[str] = Field(default_factory=list, description="Suggestions to mitigate risks")


class EnhancedCandidateSchedule(CandidateSchedule):
    """Extended CandidateSchedule with LLM explanations and insights"""
    
    # LLM-generated insights
    quality_explanation: Optional[str] = Field(
        None, 
        description="AI explanation of schedule quality and fit"
    )
    pros_and_cons: Optional[ScheduleProsCons] = Field(
        None, 
        description="Detailed pros and cons analysis"
    )
    improvement_suggestions: Optional[List[str]] = Field(
        default_factory=list, 
        description="AI suggestions for schedule improvement"
    )
    risk_assessment: Optional[RiskAssessment] = Field(
        None, 
        description="Risk analysis for this schedule"
    )
    
    # Comparative analysis
    vs_preferences_analysis: Optional[str] = Field(
        None, 
        description="How well this schedule matches stated preferences"
    )
    market_context: Optional[str] = Field(
        None, 
        description="Context about market conditions affecting this schedule"
    )
    
    # User-friendly metrics
    quality_summary: Optional[str] = Field(
        None, 
        description="Brief, user-friendly quality summary",
        example="Excellent for family time, good for rest"
    )
    confidence_level: ConfidenceLevel = Field(
        ConfidenceLevel.MEDIUM, 
        description="AI confidence in this schedule recommendation"
    )
    
    # LLM metadata
    explanation_generated_at: Optional[datetime] = Field(
        None, 
        description="When the AI explanation was generated"
    )
    explanation_model_version: Optional[str] = Field(
        None, 
        description="LLM model version used for explanations"
    )


class ConversationMessage(BaseModel):
    """Message in a conversation with the AI assistant"""
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    context: Optional[Dict[str, Any]] = Field(
        default_factory=dict, 
        description="Additional context for the message"
    )


class ConversationHistory(BaseModel):
    """History of conversation with AI assistant"""
    messages: List[ConversationMessage] = Field(
        default_factory=list, 
        description="List of conversation messages"
    )
    context: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Conversation context (current bid, preferences, etc.)"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, 
        description="When conversation started"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, 
        description="Last message timestamp"
    )


class OptimizationStrategy(BaseModel):
    """LLM-suggested optimization strategy"""
    strategy_name: str = Field(..., description="Name of the optimization strategy")
    description: str = Field(..., description="Description of the strategy")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Strategy-specific parameters"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in strategy")
    reasoning: str = Field(..., description="Why this strategy was chosen")
    expected_benefits: List[str] = Field(
        default_factory=list, 
        description="Expected benefits of this strategy"
    )
    potential_drawbacks: List[str] = Field(
        default_factory=list, 
        description="Potential drawbacks to consider"
    )


class MarketAnalysis(BaseModel):
    """LLM analysis of current market conditions"""
    analysis_summary: str = Field(..., description="Summary of market conditions")
    competition_level: ConfidenceLevel = Field(
        ..., 
        description="Expected competition level for desirable trips"
    )
    seasonal_factors: List[str] = Field(
        default_factory=list, 
        description="Seasonal factors affecting bidding"
    )
    route_recommendations: List[str] = Field(
        default_factory=list, 
        description="Route-specific recommendations"
    )
    timing_advice: Optional[str] = Field(
        None, 
        description="Advice about bid timing and strategy"
    )
    analyzed_at: datetime = Field(
        default_factory=datetime.utcnow, 
        description="When analysis was performed"
    )


class LLMOptimizationResult(BaseModel):
    """Complete result from LLM-guided optimization"""
    candidates: List[EnhancedCandidateSchedule] = Field(
        ..., 
        description="Optimized schedule candidates"
    )
    strategy_used: OptimizationStrategy = Field(
        ..., 
        description="Strategy used for optimization"
    )
    market_analysis: MarketAnalysis = Field(
        ..., 
        description="Market analysis that informed optimization"
    )
    overall_recommendation: str = Field(
        ..., 
        description="LLM's overall recommendation and guidance"
    )
    optimization_method: str = Field(
        default="llm_guided", 
        description="Method used for optimization"
    )
    processing_time: Optional[float] = Field(
        None, 
        description="Time taken for optimization in seconds"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Helper functions for backward compatibility

def to_enhanced_preference(
    base_pref: PreferenceSchema, 
    llm_result: Optional[LLMParseResult] = None
) -> EnhancedPreferenceSchema:
    """Convert base PreferenceSchema to enhanced version"""
    enhanced_data = base_pref.model_dump()
    
    if llm_result:
        enhanced_data.update({
            'parsing_confidence': llm_result.confidence,
            'llm_reasoning': llm_result.reasoning,
            'llm_suggestions': llm_result.suggestions,
            'llm_warnings': llm_result.warnings,
            'parsing_method': llm_result.parsing_method,
            'model_version': llm_result.model_version,
            'parsed_at': datetime.utcnow()
        })
    
    return EnhancedPreferenceSchema(**enhanced_data)


def to_enhanced_candidate(
    base_candidate: CandidateSchedule
) -> EnhancedCandidateSchedule:
    """Convert base CandidateSchedule to enhanced version"""
    enhanced_data = base_candidate.model_dump()
    return EnhancedCandidateSchedule(**enhanced_data)


# Export all enhanced models
__all__ = [
    'ParsingMethod',
    'ConfidenceLevel', 
    'LLMParseResult',
    'EnhancedPreferenceSchema',
    'ScheduleProsCons',
    'RiskAssessment',
    'EnhancedCandidateSchedule',
    'ConversationMessage',
    'ConversationHistory',
    'OptimizationStrategy',
    'MarketAnalysis',
    'LLMOptimizationResult',
    'to_enhanced_preference',
    'to_enhanced_candidate'
]