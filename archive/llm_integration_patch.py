"""
Integration patch for llm_service.py to add enhanced international scoring.
"""

# Add this import at the top of your llm_service.py
# from enhanced_international import enhanced_international_scoring


def patch_fallback_ranking():
    """
    Instructions to modify your existing _fallback_ranking method in llm_service.py
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
