"""
Integration patch for llm_service.py to add enhanced international scoring.
"""

# Add this import at the top of your llm_service.py
# from enhanced_international import enhanced_international_scoring


def patch_fallback_ranking():
    """
    Instructions to modify your existing _fallback_ranking method in llm_service.py
    """

    integration_code = """
    # Find your existing _fallback_ranking method and modify the calculate_score function
    # Add this after your existing scoring logic:
    
    def calculate_score(trip: Dict) -> Tuple[float, List[str]]:
        score = 5  # baseline score
        key_factors = []
        reasoning_parts = []
        
        # Your existing scoring logic here...
        # (efficiency, weekend, length, etc.)
        
        # ADD THIS NEW SECTION - Enhanced International Scoring
        try:
            from enhanced_international import enhanced_international_scoring
            intl_boost, intl_factors, intl_reasoning = enhanced_international_scoring(trip, prefs_lower)
            
            if intl_boost > 0:
                score += intl_boost / 10  # Scale boost to reasonable range
                key_factors.extend(intl_factors)
                reasoning_parts.extend(intl_reasoning)
                
        except ImportError:
            # Fallback if enhanced_international module not available
            pass
        
        # Your existing return statement...
        return score, key_factors
    """

    print("🔧 Integration Instructions:")
    print("=" * 50)
    print("1. Add import at top of llm_service.py:")
    print("   from enhanced_international import enhanced_international_scoring")
    print()
    print("2. In your _fallback_ranking method, find the calculate_score function")
    print("3. Add the enhanced international scoring after your existing logic")
    print("4. The boost will be scaled down (/10) to fit your existing scoring range")
    print()
    print("📝 Full integration code saved above")


if __name__ == "__main__":
    patch_fallback_ranking()
