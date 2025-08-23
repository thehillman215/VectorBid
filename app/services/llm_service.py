"""
LLM Service Abstraction

Provides unified interface for different LLM models optimized for specific tasks.
"""

import asyncio
import json
import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class LLMModel(str, Enum):
    """Available LLM models with their characteristics"""
    # Extraction models (heavy, accurate)
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    GPT_4O = "gpt-4o"
    GPT_4 = "gpt-4-turbo-preview"
    
    # Runtime models (fast, efficient)
    CLAUDE_3_SONNET = "claude-3-5-sonnet-20241022"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_35_TURBO = "gpt-3.5-turbo-16k"
    
    # Embedding models
    ADA_002 = "text-embedding-ada-002"
    COHERE_EMBED = "embed-english-v3.0"


class ModelConfig:
    """Configuration for each model"""
    CONFIGS = {
        LLMModel.CLAUDE_3_OPUS: {
            "provider": "anthropic",
            "max_tokens": 200000,
            "cost_per_1k_input": 0.015,
            "cost_per_1k_output": 0.075,
            "latency_ms": 15000,
            "accuracy": 0.95,
        },
        LLMModel.GPT_4O: {
            "provider": "openai",
            "max_tokens": 128000,
            "cost_per_1k_input": 0.005,
            "cost_per_1k_output": 0.015,
            "latency_ms": 12000,
            "accuracy": 0.94,
        },
        LLMModel.CLAUDE_3_SONNET: {
            "provider": "anthropic",
            "max_tokens": 200000,
            "cost_per_1k_input": 0.003,
            "cost_per_1k_output": 0.015,
            "latency_ms": 3000,
            "accuracy": 0.90,
        },
        LLMModel.GPT_4_TURBO: {
            "provider": "openai",
            "max_tokens": 128000,
            "cost_per_1k_input": 0.01,
            "cost_per_1k_output": 0.03,
            "latency_ms": 2500,
            "accuracy": 0.89,
        },
    }


class LLMService:
    """Unified LLM service with model selection based on task"""
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
    ):
        self.openai_client = AsyncOpenAI(api_key=openai_api_key) if openai_api_key else None
        self.anthropic_client = AsyncAnthropic(api_key=anthropic_api_key) if anthropic_api_key else None
        
        # Track usage for cost monitoring
        self.usage_stats = {
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost": 0.0,
            "requests_by_model": {},
        }
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
    )
    async def extract_contract_rules(
        self,
        contract_text: str,
        airline: str,
        contract_version: str,
        model: LLMModel = LLMModel.CLAUDE_3_OPUS,
    ) -> Dict[str, Any]:
        """
        Extract rules from contract using heavy model for maximum accuracy
        
        Args:
            contract_text: Full contract text
            airline: Airline code
            contract_version: Contract version
            model: LLM model to use (defaults to Opus for accuracy)
        
        Returns:
            Structured extraction of all contract rules
        """
        
        system_prompt = """You are an expert contract analyst specializing in airline pilot contracts and FAR regulations.
        Your task is to extract ALL rules, constraints, and requirements from this contract.
        
        For each rule, provide:
        1. rule_id: Unique identifier
        2. category: (far117, union, scheduling, rest, compensation, training, operational)
        3. subcategory: More specific classification
        4. description: Brief description
        5. original_text: Exact text from contract
        6. is_hard_constraint: Boolean (true for SHALL/MUST, false for SHOULD/MAY)
        7. dsl_expression: Logical expression using these variables:
           - pairing.duty_hours, pairing.rest_hours, pairing.flight_hours
           - pairing.redeye, pairing.layover_hours, pairing.legs
           - pref.* for pilot preferences
        8. parameters: Any numeric values or thresholds
        9. source_section: Section number/name
        10. related_rules: List of related rule IDs
        
        Return as JSON with a 'rules' array."""
        
        user_prompt = f"""Extract all rules from this {airline} contract (version {contract_version}):
        
        {contract_text}
        
        Be extremely thorough - capture every requirement, constraint, and preference.
        Include both explicit rules and implicit requirements."""
        
        if model in [LLMModel.CLAUDE_3_OPUS, LLMModel.CLAUDE_3_SONNET]:
            return await self._call_anthropic(system_prompt, user_prompt, model)
        else:
            return await self._call_openai(system_prompt, user_prompt, model)
    
    async def validate_rules(
        self,
        rules: List[Dict[str, Any]],
        model: LLMModel = LLMModel.GPT_4_TURBO,
    ) -> List[Dict[str, Any]]:
        """
        Validate and enhance extracted rules using fast model
        
        Args:
            rules: List of extracted rules
            model: LLM model to use (defaults to GPT-4 Turbo for speed)
        
        Returns:
            Validated rules with corrections and enhancements
        """
        
        system_prompt = """You are a rule validation expert. Review these extracted rules for:
        1. DSL expression correctness
        2. Conflicts with FAR regulations
        3. Internal consistency
        4. Missing related rules
        
        For each rule, add:
        - confidence_score: 0.0 to 1.0
        - validation_notes: List of issues or confirmations
        - suggested_improvements: Any recommended changes
        
        Return the enhanced rules as JSON."""
        
        user_prompt = f"""Validate these extracted contract rules:
        
        {json.dumps(rules, indent=2)}
        
        Ensure DSL expressions are valid and rules don't conflict with FAR 117."""
        
        if model in [LLMModel.CLAUDE_3_SONNET, LLMModel.GPT_4_TURBO]:
            return await self._call_fast_model(system_prompt, user_prompt, model)
        else:
            return await self._call_openai(system_prompt, user_prompt, model)
    
    async def apply_rules_to_schedule(
        self,
        rules: List[Dict[str, Any]],
        pilot_preferences: Dict[str, Any],
        candidate_schedules: List[Dict[str, Any]],
        model: LLMModel = LLMModel.GPT_4_TURBO,
    ) -> Dict[str, Any]:
        """
        Apply rules to candidate schedules using fast runtime model
        
        Args:
            rules: All applicable rules
            pilot_preferences: Pilot's preferences
            candidate_schedules: Schedules to evaluate
            model: LLM model to use (defaults to GPT-4 Turbo)
        
        Returns:
            Evaluation results with explanations
        """
        
        system_prompt = """You are a scheduling assistant that applies contract rules to pilot schedules.
        
        For each schedule:
        1. Check ALL hard constraints (violations = disqualified)
        2. Score soft preferences (0.0 to 1.0)
        3. Explain significant rule applications
        4. Cite specific contract sections
        
        Be concise but thorough in explanations."""
        
        user_prompt = f"""Apply these rules to evaluate schedules:
        
        RULES:
        {json.dumps(rules, indent=2)}
        
        PILOT PREFERENCES:
        {json.dumps(pilot_preferences, indent=2)}
        
        CANDIDATE SCHEDULES:
        {json.dumps(candidate_schedules, indent=2)}
        
        Return evaluations with scores and explanations."""
        
        return await self._call_fast_model(system_prompt, user_prompt, model)
    
    async def generate_embeddings(
        self,
        texts: List[str],
        model: LLMModel = LLMModel.ADA_002,
    ) -> List[List[float]]:
        """
        Generate embeddings for vector storage
        
        Args:
            texts: List of text chunks to embed
            model: Embedding model to use
        
        Returns:
            List of embedding vectors
        """
        
        if not self.openai_client:
            raise ValueError("OpenAI client required for embeddings")
        
        response = await self.openai_client.embeddings.create(
            model=model.value,
            input=texts,
        )
        
        embeddings = [item.embedding for item in response.data]
        
        # Track usage
        self._track_usage(model, len(" ".join(texts)), 0)
        
        return embeddings
    
    async def _call_anthropic(
        self,
        system_prompt: str,
        user_prompt: str,
        model: LLMModel,
    ) -> Dict[str, Any]:
        """Call Anthropic API"""
        
        if not self.anthropic_client:
            raise ValueError("Anthropic client not configured")
        
        response = await self.anthropic_client.messages.create(
            model=model.value,
            max_tokens=8000,
            temperature=0.1,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        
        content = response.content[0].text
        
        # Track usage
        self._track_usage(
            model,
            response.usage.input_tokens,
            response.usage.output_tokens,
        )
        
        # Parse JSON response
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Extract JSON from markdown if needed
            import re
            json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            return {"raw_response": content}
    
    async def _call_openai(
        self,
        system_prompt: str,
        user_prompt: str,
        model: LLMModel,
    ) -> Dict[str, Any]:
        """Call OpenAI API"""
        
        if not self.openai_client:
            raise ValueError("OpenAI client not configured")
        
        response = await self.openai_client.chat.completions.create(
            model=model.value,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=8000,
            response_format={"type": "json_object"},
        )
        
        content = response.choices[0].message.content
        
        # Track usage
        self._track_usage(
            model,
            response.usage.prompt_tokens,
            response.usage.completion_tokens,
        )
        
        return json.loads(content)
    
    async def _call_fast_model(
        self,
        system_prompt: str,
        user_prompt: str,
        model: LLMModel,
    ) -> Dict[str, Any]:
        """Call fast model for runtime operations"""
        
        if model in [LLMModel.CLAUDE_3_SONNET]:
            return await self._call_anthropic(system_prompt, user_prompt, model)
        else:
            return await self._call_openai(system_prompt, user_prompt, model)
    
    def _track_usage(
        self,
        model: LLMModel,
        input_tokens: int,
        output_tokens: int,
    ):
        """Track token usage and costs"""
        
        config = ModelConfig.CONFIGS.get(model, {})
        
        # Calculate cost
        input_cost = (input_tokens / 1000) * config.get("cost_per_1k_input", 0)
        output_cost = (output_tokens / 1000) * config.get("cost_per_1k_output", 0)
        total_cost = input_cost + output_cost
        
        # Update stats
        self.usage_stats["total_input_tokens"] += input_tokens
        self.usage_stats["total_output_tokens"] += output_tokens
        self.usage_stats["total_cost"] += total_cost
        
        if model.value not in self.usage_stats["requests_by_model"]:
            self.usage_stats["requests_by_model"][model.value] = 0
        self.usage_stats["requests_by_model"][model.value] += 1
        
        logger.info(
            f"LLM call to {model.value}: {input_tokens} in, {output_tokens} out, "
            f"${total_cost:.4f} cost"
        )
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return self.usage_stats
    
    def estimate_cost(
        self,
        model: LLMModel,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """Estimate cost for a given model and token count"""
        
        config = ModelConfig.CONFIGS.get(model, {})
        input_cost = (input_tokens / 1000) * config.get("cost_per_1k_input", 0)
        output_cost = (output_tokens / 1000) * config.get("cost_per_1k_output", 0)
        
        return input_cost + output_cost