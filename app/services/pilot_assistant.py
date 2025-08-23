"""
Pilot Assistant Service

Runtime service for pilots using fast LLM models with full contract context.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from .llm_service import LLMModel, LLMService
from .vector_store import VectorStoreService

logger = logging.getLogger(__name__)


class ScheduleEvaluation(BaseModel):
    """Evaluation result for a candidate schedule"""
    
    schedule_id: str
    overall_score: float
    is_valid: bool
    
    # Rule violations
    hard_violations: List[Dict[str, Any]] = []
    soft_penalties: List[Dict[str, Any]] = []
    
    # Scoring breakdown
    scoring_details: Dict[str, float] = {}
    
    # Explanations
    summary: str
    detailed_explanation: Optional[str] = None
    rule_citations: List[Dict[str, Any]] = []
    
    # Recommendations
    improvements: List[str] = []
    alternatives: List[str] = []


class PilotAssistant:
    """
    Fast runtime assistant for pilot schedule evaluation.
    Uses pre-extracted rules with full context for comprehensive analysis.
    """
    
    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        vector_store: Optional[VectorStoreService] = None,
    ):
        self.llm_service = llm_service or LLMService()
        self.vector_store = vector_store or VectorStoreService(store_type="memory")
        
        # Performance tracking
        self.stats = {
            "evaluations_performed": 0,
            "average_response_time": 0.0,
            "rules_applied_per_evaluation": 0.0,
        }
    
    async def evaluate_schedules(
        self,
        pilot_preferences: Dict[str, Any],
        candidate_schedules: List[Dict[str, Any]],
        airline: str,
        contract_version: str,
        explain_details: bool = True,
    ) -> List[ScheduleEvaluation]:
        """
        Evaluate candidate schedules against contract rules and pilot preferences.
        
        Args:
            pilot_preferences: Pilot's preferences and constraints
            candidate_schedules: List of schedules to evaluate
            airline: Airline code
            contract_version: Contract version to use
            explain_details: Whether to generate detailed explanations
        
        Returns:
            List of evaluation results for each schedule
        """
        
        start_time = datetime.now()
        logger.info(f"Evaluating {len(candidate_schedules)} schedules for {airline}")
        
        try:
            # Step 1: Retrieve ALL relevant rules from vector store
            all_rules = await self._get_comprehensive_rules(
                airline=airline,
                contract_version=contract_version,
                pilot_preferences=pilot_preferences,
            )
            
            logger.info(f"Retrieved {len(all_rules)} rules for evaluation")
            
            # Step 2: Apply rules using fast LLM model
            evaluation_result = await self.llm_service.apply_rules_to_schedule(
                rules=all_rules,
                pilot_preferences=pilot_preferences,
                candidate_schedules=candidate_schedules,
                model=LLMModel.GPT_4_TURBO,  # Fast model for runtime
            )
            
            # Step 3: Parse and structure results
            evaluations = self._parse_evaluation_results(
                evaluation_result,
                candidate_schedules,
                all_rules,
            )
            
            # Step 4: Generate detailed explanations if requested
            if explain_details:
                evaluations = await self._enhance_with_explanations(
                    evaluations,
                    all_rules,
                    pilot_preferences,
                )
            
            # Update statistics
            response_time = (datetime.now() - start_time).total_seconds()
            self._update_stats(len(candidate_schedules), len(all_rules), response_time)
            
            logger.info(
                f"Evaluation complete in {response_time:.2f}s, "
                f"applied {len(all_rules)} rules"
            )
            
            return evaluations
            
        except Exception as e:
            logger.error(f"Schedule evaluation failed: {e}")
            # Return basic evaluations with error
            return [
                ScheduleEvaluation(
                    schedule_id=schedule.get("id", f"schedule_{i}"),
                    overall_score=0.0,
                    is_valid=False,
                    summary=f"Evaluation failed: {str(e)}",
                )
                for i, schedule in enumerate(candidate_schedules)
            ]
    
    async def _get_comprehensive_rules(
        self,
        airline: str,
        contract_version: str,
        pilot_preferences: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Retrieve comprehensive set of rules based on context.
        Gets both universally applicable rules and preference-specific ones.
        """
        
        all_rules = []
        
        # Get all hard constraints (always apply)
        hard_rules = await self.vector_store.get_all_rules(
            airline=airline,
            contract_version=contract_version,
        )
        
        # Filter to only hard constraints and relevant soft rules
        for rule in hard_rules:
            rule_dict = {
                "rule_id": rule.rule_id,
                "category": rule.category,
                "description": rule.description,
                "original_text": rule.original_text,
                "is_hard_constraint": rule.is_hard_constraint,
                "dsl_expression": rule.dsl_expression,
                "parameters": rule.parameters,
                "source_section": rule.source_section,
            }
            
            # Include all hard constraints
            if rule.is_hard_constraint:
                all_rules.append(rule_dict)
            # Include soft rules relevant to preferences
            elif self._is_relevant_to_preferences(rule, pilot_preferences):
                all_rules.append(rule_dict)
        
        # Search for additional rules based on specific preferences
        if pilot_preferences.get("special_requirements"):
            for requirement in pilot_preferences["special_requirements"]:
                search_results = await self.vector_store.search_rules(
                    query=requirement,
                    airline=airline,
                    contract_version=contract_version,
                    top_k=20,
                )
                
                for rule_vector, score in search_results:
                    if score > 0.7:  # Only high-relevance rules
                        rule_dict = {
                            "rule_id": rule_vector.rule_id,
                            "category": rule_vector.category,
                            "description": rule_vector.description,
                            "original_text": rule_vector.original_text,
                            "is_hard_constraint": rule_vector.is_hard_constraint,
                            "dsl_expression": rule_vector.dsl_expression,
                            "parameters": rule_vector.parameters,
                            "source_section": rule_vector.source_section,
                            "relevance_score": score,
                        }
                        
                        # Avoid duplicates
                        if not any(r["rule_id"] == rule_dict["rule_id"] for r in all_rules):
                            all_rules.append(rule_dict)
        
        return all_rules
    
    def _is_relevant_to_preferences(
        self,
        rule: Any,
        pilot_preferences: Dict[str, Any],
    ) -> bool:
        """Check if a soft rule is relevant to pilot preferences"""
        
        # Check category relevance
        preference_categories = pilot_preferences.get("priority_categories", [])
        if rule.category in preference_categories:
            return True
        
        # Check keyword matching
        preference_text = json.dumps(pilot_preferences).lower()
        rule_text = (rule.description + rule.original_text).lower()
        
        relevance_keywords = [
            "layover", "rest", "duty", "credit", "pay", "deadhead",
            "reserve", "training", "vacation", "commute", "base",
        ]
        
        for keyword in relevance_keywords:
            if keyword in preference_text and keyword in rule_text:
                return True
        
        return False
    
    def _parse_evaluation_results(
        self,
        evaluation_result: Dict[str, Any],
        candidate_schedules: List[Dict[str, Any]],
        all_rules: List[Dict[str, Any]],
    ) -> List[ScheduleEvaluation]:
        """Parse LLM evaluation results into structured format"""
        
        evaluations = []
        
        # Handle different response formats
        if "evaluations" in evaluation_result:
            eval_data = evaluation_result["evaluations"]
        elif "schedules" in evaluation_result:
            eval_data = evaluation_result["schedules"]
        else:
            eval_data = [evaluation_result]
        
        for i, schedule in enumerate(candidate_schedules):
            schedule_id = schedule.get("id", f"schedule_{i}")
            
            # Find corresponding evaluation
            schedule_eval = None
            for eval_item in eval_data:
                if eval_item.get("schedule_id") == schedule_id or eval_item.get("index") == i:
                    schedule_eval = eval_item
                    break
            
            if not schedule_eval:
                # Create default evaluation
                schedule_eval = {
                    "score": 0.5,
                    "valid": True,
                    "violations": [],
                    "summary": "No evaluation data",
                }
            
            evaluation = ScheduleEvaluation(
                schedule_id=schedule_id,
                overall_score=schedule_eval.get("score", 0.5),
                is_valid=schedule_eval.get("valid", True),
                hard_violations=schedule_eval.get("hard_violations", []),
                soft_penalties=schedule_eval.get("soft_penalties", []),
                scoring_details=schedule_eval.get("scoring_details", {}),
                summary=schedule_eval.get("summary", ""),
                rule_citations=schedule_eval.get("citations", []),
                improvements=schedule_eval.get("improvements", []),
            )
            
            evaluations.append(evaluation)
        
        return evaluations
    
    async def _enhance_with_explanations(
        self,
        evaluations: List[ScheduleEvaluation],
        all_rules: List[Dict[str, Any]],
        pilot_preferences: Dict[str, Any],
    ) -> List[ScheduleEvaluation]:
        """Add detailed explanations to evaluations"""
        
        for evaluation in evaluations:
            # Build detailed explanation
            explanation_parts = []
            
            # Explain hard violations
            if evaluation.hard_violations:
                explanation_parts.append("**Contract Violations:**")
                for violation in evaluation.hard_violations:
                    rule_id = violation.get("rule_id")
                    rule = next((r for r in all_rules if r["rule_id"] == rule_id), None)
                    if rule:
                        explanation_parts.append(
                            f"- {rule['description']} (Section {rule.get('source_section', 'N/A')})"
                        )
            
            # Explain soft penalties
            if evaluation.soft_penalties:
                explanation_parts.append("\n**Preference Impacts:**")
                for penalty in evaluation.soft_penalties:
                    explanation_parts.append(f"- {penalty.get('description', 'Unknown penalty')}")
            
            # Add scoring breakdown
            if evaluation.scoring_details:
                explanation_parts.append("\n**Scoring Breakdown:**")
                for category, score in evaluation.scoring_details.items():
                    explanation_parts.append(f"- {category}: {score:.2f}")
            
            evaluation.detailed_explanation = "\n".join(explanation_parts)
        
        return evaluations
    
    async def explain_rule_application(
        self,
        schedule: Dict[str, Any],
        rule_id: str,
        airline: str,
        contract_version: str,
    ) -> str:
        """
        Explain how a specific rule applies to a schedule.
        
        Args:
            schedule: Schedule to analyze
            rule_id: Specific rule to explain
            airline: Airline code
            contract_version: Contract version
        
        Returns:
            Natural language explanation
        """
        
        # Get the specific rule
        all_rules = await self.vector_store.get_all_rules(airline, contract_version)
        rule = next((r for r in all_rules if r.rule_id == rule_id), None)
        
        if not rule:
            return f"Rule {rule_id} not found"
        
        # Generate explanation using LLM
        system_prompt = """Explain how this specific contract rule applies to the given schedule.
        Be clear about whether the rule is satisfied or violated, and why.
        Reference specific values from the schedule."""
        
        user_prompt = f"""Rule: {rule.original_text}
        DSL Expression: {rule.dsl_expression}
        
        Schedule: {json.dumps(schedule, indent=2)}
        
        Explain the application of this rule."""
        
        response = await self.llm_service._call_fast_model(
            system_prompt,
            user_prompt,
            LLMModel.GPT_4_TURBO,
        )
        
        return response.get("explanation", "Unable to generate explanation")
    
    async def suggest_schedule_improvements(
        self,
        schedule: Dict[str, Any],
        pilot_preferences: Dict[str, Any],
        airline: str,
        contract_version: str,
    ) -> List[str]:
        """
        Suggest improvements to make a schedule better align with preferences.
        
        Args:
            schedule: Current schedule
            pilot_preferences: Pilot's preferences
            airline: Airline code
            contract_version: Contract version
        
        Returns:
            List of improvement suggestions
        """
        
        # Get relevant rules
        all_rules = await self._get_comprehensive_rules(
            airline, contract_version, pilot_preferences
        )
        
        # Generate suggestions using LLM
        system_prompt = """Analyze this schedule against contract rules and pilot preferences.
        Suggest specific, actionable improvements that would:
        1. Better satisfy soft preferences
        2. Increase overall schedule quality
        3. Avoid potential issues
        
        Be specific and reference contract sections where relevant."""
        
        user_prompt = f"""Schedule: {json.dumps(schedule, indent=2)}
        
        Pilot Preferences: {json.dumps(pilot_preferences, indent=2)}
        
        Contract Rules (summary): {len(all_rules)} rules from {airline} contract v{contract_version}
        
        Provide 3-5 specific improvement suggestions."""
        
        response = await self.llm_service._call_fast_model(
            system_prompt,
            user_prompt,
            LLMModel.GPT_4_TURBO,
        )
        
        suggestions = response.get("suggestions", [])
        if isinstance(suggestions, str):
            suggestions = [suggestions]
        
        return suggestions
    
    def _update_stats(
        self,
        schedules_evaluated: int,
        rules_applied: int,
        response_time: float,
    ):
        """Update performance statistics"""
        
        self.stats["evaluations_performed"] += 1
        
        # Update average response time
        prev_avg = self.stats["average_response_time"]
        prev_count = self.stats["evaluations_performed"] - 1
        self.stats["average_response_time"] = (
            (prev_avg * prev_count + response_time) / self.stats["evaluations_performed"]
        )
        
        # Update average rules per evaluation
        prev_rules_avg = self.stats["rules_applied_per_evaluation"]
        self.stats["rules_applied_per_evaluation"] = (
            (prev_rules_avg * prev_count + rules_applied) / self.stats["evaluations_performed"]
        )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        
        return {
            **self.stats,
            "llm_usage": self.llm_service.get_usage_stats(),
            "vector_store_stats": self.vector_store.get_statistics(),
        }