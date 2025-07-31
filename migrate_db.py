#!/usr/bin/env python3
"""
VectorBid Replit DB Profile Migration Script
Run this to upgrade existing profiles to the enhanced schema.
"""

import json
from datetime import datetime


def backup_profiles():
    """Create a backup before migration."""
    print("💾 Creating backup before migration...")

    try:
        from replit import db

        # Export all profile data
        backup_data = {}
        profile_count = 0

        for key in db.keys():
            if key.startswith("user:") and key.endswith(":profile"):
                backup_data[key] = db[key]
                profile_count += 1

        # Save backup file
        backup_filename = f"profile_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_filename, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)

        print(
            f"✅ Backup created: {backup_filename} ({profile_count} profiles)")
        return backup_filename

    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return None


def run_migration():
    """Run the profile migration."""
    print("🚀 VectorBid Profile Migration")
    print("=" * 50)

    # Step 1: Backup
    backup_file = backup_profiles()
    if not backup_file:
        print("❌ Migration aborted - backup failed")
        return False

    # Step 2: Run migration
    try:
        from services.db import migrate_existing_profiles

        print("\n🔄 Running migration...")
        migrated_count = migrate_existing_profiles()

        print(f"\n✅ Migration successful!")
        print(f"   - Backup: {backup_file}")
        print(f"   - Migrated: {migrated_count} profiles")
        print(f"   - Status: Ready for enhanced features")

        return True

    except ImportError:
        print("❌ Could not import migration function")
        print("   Make sure you've updated services/db.py first")
        return False
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


def show_profile_stats():
    """Show statistics about profiles."""
    print("\n📊 Profile Statistics:")

    try:
        from replit import db

        # Count profiles
        profile_count = 0
        airlines = {}

        for key in db.keys():
            if key.startswith("user:") and key.endswith(":profile"):
                profile_count += 1
                try:
                    profile = db[key]
                    airline = profile.get('airline', 'Unknown')
                    airlines[airline] = airlines.get(airline, 0) + 1
                except:
                    pass

        print(f"   Total Profiles: {profile_count}")

        if airlines:
            print(f"   Airlines:")
            for airline, count in sorted(airlines.items()):
                print(f"     - {airline}: {count}")

    except Exception as e:
        print(f"❌ Error getting stats: {e}")


def main():
    """Main migration function."""
    print("🚀 VectorBid Enhanced Profile Migration")
    print("This will upgrade your Replit DB profiles with new features")
    print("=" * 60)

    # Check environment
    try:
        from replit import db
        print("✅ Replit environment detected")
    except ImportError:
        print("❌ Not running in Replit environment")
        print("   This migration must be run in Replit")
        return

    # Show current stats
    show_profile_stats()

    # Confirm migration
    print("\n⚠️  This will modify your profile data")
    print("   A backup will be created automatically")

    response = input("\nProceed with migration? (y/N): ").strip().lower()
    if response != 'y':
        print("Migration cancelled")
        return

    # Run migration
    success = run_migration()
    if success:
        print("\n🎉 Migration Complete!")
        print("Your VectorBid profiles are now enhanced and ready for:")
        print("   ✅ Seniority analysis with probability calculations")
        print("   ✅ 11 different pilot personas")
        print("   ✅ Custom preference combinations")
        print("   ✅ Enhanced onboarding experience")
        print("   ✅ Professional results dashboard")

    else:
        print("\n❌ Migration failed")
        print("Check the error messages above and try again")


if __name__ == "__main__":
    main()
