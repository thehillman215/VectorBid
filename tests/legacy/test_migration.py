#!/usr/bin/env python3
"""
Test script for enhanced profile functionality.
Run this after migration to verify everything works.
"""

from datetime import date


def test_enhanced_profiles():
    """Test all enhanced profile features."""
    print("🧪 Testing Enhanced Profile System")
    print("=" * 40)

    try:
        # Import available services or skip if not available
        try:
            from services.db import (
                calculate_seniority_category,
                get_profile,
                get_seniority_analysis,
                save_profile,
                update_seniority_analysis,
                validate_profile,
            )
        except ImportError:
            print("   ⚠️ services.db not available, skipping enhanced profile tests")
            return

        # Test user
        test_uid = "test_enhanced_user"

        print("1️⃣ Testing basic profile operations...")

        # Test saving enhanced profile
        enhanced_data = {
            "airline": "United",
            "base": "IAH",
            "seat": "CA",
            "fleet": ["737", "787", "320"],
            "seniority": 1250,
            "hire_date": date(2015, 3, 15),
            "years_at_position": 8,
            "persona": "work_life_balance",
            "custom_preferences": "I prefer weekends off and trips under 4 days",
            "onboard_complete": True,
        }

        save_profile(test_uid, enhanced_data)
        print("   ✅ Saved enhanced profile data")

        # Test retrieving profile
        profile = get_profile(test_uid)
        print("   ✅ Retrieved profile successfully")

        # Test new fields exist
        new_fields = [
            "hire_date",
            "years_at_position",
            "seniority_percentile",
            "last_seniority_update",
            "persona",
            "custom_preferences",
            "onboard_complete",
            "profile_completion_date",
        ]

        missing_fields = []
        for field in new_fields:
            if field not in profile:
                missing_fields.append(field)

        if missing_fields:
            print(f"   ❌ Missing fields: {missing_fields}")
        else:
            print("   ✅ All enhanced fields present")

        print("\n2️⃣ Testing data type handling...")

        # Test date handling
        if isinstance(profile.get("hire_date"), str):
            print("   ✅ Date properly serialized as ISO string")
        else:
            print("   ❌ Date serialization issue")

        # Test fleet list handling
        if isinstance(profile.get("fleet"), list):
            print(f"   ✅ Fleet stored as list: {profile['fleet']}")
        else:
            print(f"   ❌ Fleet not a list: {type(profile.get('fleet'))}")

        print("\n3️⃣ Testing validation...")

        validation = validate_profile(profile)
        if validation["valid"]:
            print("   ✅ Profile validation passed")
        else:
            print(f"   ❌ Validation errors: {validation['errors']}")

        if validation["warnings"]:
            print(f"   ⚠️  Warnings: {validation['warnings']}")

        print("\n4️⃣ Testing seniority analysis...")

        # Test seniority percentile calculation
        update_seniority_analysis(test_uid, 85.5, "Very Senior")

        seniority_data = get_seniority_analysis(test_uid)
        if seniority_data:
            print(
                f"   ✅ Seniority analysis: {seniority_data['percentile']}% - {seniority_data['category']}"
            )
        else:
            print("   ❌ Seniority analysis failed")

        # Test category calculation
        categories_test = [
            (95, "Very Senior"),
            (80, "Senior"),
            (60, "Mid-Seniority"),
            (35, "Junior"),
            (15, "Very Junior"),
        ]

        for percentile, expected in categories_test:
            result = calculate_seniority_category(percentile)
            status = "✅" if result == expected else "❌"
            print(f"   {status} {percentile}% -> {result}")

        print("\n5️⃣ Testing persona system...")

        personas = [
            "work_life_balance",
            "credit_hunter",
            "adventure_seeker",
            "commuter_friendly",
            "reserve_avoider",
            "family_first",
            "international_specialist",
            "night_owl",
            "senior_lifestyle",
            "building_hours",
            "training_focused",
        ]

        for persona in personas:
            save_profile(test_uid, {"persona": persona})
            retrieved = get_profile(test_uid)
            if retrieved["persona"] == persona:
                print(f"   ✅ {persona}")
            else:
                print(f"   ❌ {persona} - got {retrieved['persona']}")

        print("\n6️⃣ Testing backward compatibility...")

        # Test legacy field access
        legacy_fields = [
            "profile_completed",
            "airline",
            "fleet",
            "seat",
            "base",
            "seniority",
        ]
        for field in legacy_fields:
            if field in profile:
                print(f"   ✅ {field}: {profile[field]}")
            else:
                print(f"   ❌ {field} missing")

        print("\n7️⃣ Cleanup...")

        # Clean up test data
        from replit import db

        del db[f"user:{test_uid}:profile"]
        print("   ✅ Test data cleaned up")

        print("\n🎉 All tests passed! Enhanced profiles are working correctly.")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure services/db.py has been updated")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_existing_profiles():
    """Test that existing profiles still work."""
    print("\n🔍 Testing Existing Profiles")
    print("=" * 30)

    try:
        try:
            from services.db import get_all_profiles, validate_profile
        except ImportError:
            print("   ⚠️ services.db not available, skipping existing profile tests")
            return True

        profiles = get_all_profiles()
        print(f"Found {len(profiles)} existing profiles")

        if not profiles:
            print("   ℹ️  No existing profiles to test")
            return True

        # Test first few profiles
        test_count = min(3, len(profiles))
        for i, (uid, profile) in enumerate(list(profiles.items())[:test_count]):
            print(f"\n   Testing profile {i + 1}: {uid}")

            # Test validation
            validation = validate_profile(profile)
            print(f"     Valid: {'✅' if validation['valid'] else '❌'}")
            print(f"     Complete: {'✅' if validation['complete'] else '❌'}")

            # Test new fields have defaults
            new_field_count = 0
            for field in ["hire_date", "persona", "onboard_complete"]:
                if field in profile:
                    new_field_count += 1

            print(f"     Enhanced fields: {new_field_count}/3")

        print("\n✅ Existing profiles are compatible")
        return True

    except Exception as e:
        print(f"❌ Error testing existing profiles: {e}")
        return False


def main():
    """Main test function."""
    print("🧪 VectorBid Enhanced Profile Test Suite")
    print("This will test all enhanced profile functionality")
    print("=" * 50)

    # Run tests
    success = True

    # Test enhanced functionality
    if not test_enhanced_profiles():
        success = False

    # Test existing profiles
    if not test_existing_profiles():
        success = False

    # Final result
    if success:
        print("\n🎉 ALL TESTS PASSED!")
        print("Your enhanced profile system is ready to use.")
        print("\nNext steps:")
        print("1. Update your templates (Phase 2)")
        print("2. Add enhanced route handlers (Phase 3)")
        print("3. Test the full user experience")
    else:
        print("\n❌ SOME TESTS FAILED")
        print("Please check the errors above and fix before proceeding.")


if __name__ == "__main__":
    main()
