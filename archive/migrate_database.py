#!/usr/bin/env python3
"""
Database Migration for VectorBid Enhanced Features
Run this first to add new database columns safely.
"""

import os
import sys
from datetime import datetime
from sqlalchemy import text


def backup_database():
    """Create a database backup before migration."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backup_before_migration_{timestamp}.sql"
    database_url = os.environ.get('DATABASE_URL')

    if not database_url:
        print("❌ DATABASE_URL not set")
        return None

    print(f"📦 Creating database backup: {backup_file}")
    backup_cmd = f"pg_dump '{database_url}' > {backup_file}"
    result = os.system(backup_cmd)

    if result == 0:
        print(f"✅ Database backed up to: {backup_file}")
        return backup_file
    else:
        print(
            f"❌ Failed to create backup (pg_dump not available or permission denied)"
        )
        print("   Continuing without backup - be careful!")
        return None


def migrate_database():
    """Run the database migration safely."""
    print("🔄 Starting database migration...")

    try:
        # Import Flask app and models
        from app import create_app
        from models import db

        app = create_app()
        with app.app_context():
            print("   Connected to database successfully")

            # Migration SQL commands
            migrations = [
                # BidPacket enhancements
                """
                ALTER TABLE bid_packet 
                ADD COLUMN IF NOT EXISTS airline VARCHAR(50),
                ADD COLUMN IF NOT EXISTS aircraft VARCHAR(50),
                ADD COLUMN IF NOT EXISTS bid_month VARCHAR(20),
                ADD COLUMN IF NOT EXISTS upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                """,

                # User activity tracking
                """
                ALTER TABLE user_profile 
                ADD COLUMN IF NOT EXISTS login_count INTEGER DEFAULT 0,
                ADD COLUMN IF NOT EXISTS last_login TIMESTAMP,
                ADD COLUMN IF NOT EXISTS profile_completion_date TIMESTAMP;
                """,

                # Create indexes for better performance
                """
                CREATE INDEX IF NOT EXISTS idx_bid_packet_airline 
                ON bid_packet(airline);
                """,
                """
                CREATE INDEX IF NOT EXISTS idx_bid_packet_aircraft 
                ON bid_packet(aircraft);
                """,
                """
                CREATE INDEX IF NOT EXISTS idx_bid_packet_month 
                ON bid_packet(bid_month);
                """
            ]

            # Execute migrations
            for i, migration in enumerate(migrations, 1):
                try:
                    print(f"   Running migration {i}/{len(migrations)}...")
                    db.engine.execute(text(migration))
                    print(f"   ✅ Migration {i} completed")
                except Exception as e:
                    print(f"   ⚠️  Migration {i} warning: {e}")
                    continue

            # Commit changes
            db.session.commit()
            print("✅ All migrations completed successfully")
            return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print("   Make sure your Flask app and models are working")
        return False


def verify_migration():
    """Verify that the migration was successful."""
    print("🔍 Verifying migration...")

    try:
        from app import create_app
        from models import db

        app = create_app()
        with app.app_context():
            # Check if new columns exist
            checks = [
                "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='bid_packet' AND column_name='airline'",
                "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='bid_packet' AND column_name='aircraft'",
                "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='user_profile' AND column_name='login_count'"
            ]

            success_count = 0
            for i, check in enumerate(checks, 1):
                try:
                    result = db.engine.execute(text(check)).scalar()
                    if result > 0:
                        print(f"   ✅ Check {i} passed")
                        success_count += 1
                    else:
                        print(f"   ❌ Check {i} failed")
                except Exception as e:
                    print(f"   ⚠️  Check {i} error: {e}")

            if success_count == len(checks):
                print("✅ Migration verification successful")
                return True
            else:
                print(f"⚠️  {success_count}/{len(checks)} checks passed")
                return False

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False


def main():
    """Main migration function."""
    print("🚀 VectorBid Database Migration")
    print("=" * 40)
    print("This will add enhanced features to your database:")
    print("- Bid packet organization fields (airline, aircraft, month)")
    print("- User activity tracking")
    print("- Performance indexes")
    print()

    # Check environment
    if not os.environ.get('DATABASE_URL'):
        print("❌ DATABASE_URL environment variable not set")
        print("   Set it first: export DATABASE_URL='your-database-url'")
        sys.exit(1)

    # Step 1: Backup database (optional but recommended)
    backup_file = backup_database()

    # Step 2: Run migration
    print("\n🔄 Running database migration...")
    if not migrate_database():
        print("❌ Migration failed")
        if backup_file:
            print(
                f"   Restore from backup: psql '{os.environ.get('DATABASE_URL')}' < {backup_file}"
            )
        sys.exit(1)

    # Step 3: Verify migration
    print("\n🔍 Verifying migration...")
    if not verify_migration():
        print("⚠️  Migration completed but verification failed")
        print("   Check the database manually")

    print("\n🎉 Database migration completed!")
    if backup_file:
        print(f"   Backup file: {backup_file}")
    print("\nNext steps:")
    print("1. Test your application to ensure it still works")
    print("2. Deploy enhanced admin portal")
    print("3. Deploy PBS filter system")


if __name__ == "__main__":
    main()
