import os
import psycopg2
from urllib.parse import urlparse

print("Starting direct database migration...")

database_url = os.environ.get("DATABASE_URL")
if not database_url:
    print("DATABASE_URL not set")
    exit(1)

parsed = urlparse(database_url)

try:
    conn = psycopg2.connect(
        host=parsed.hostname,
        database=parsed.path[1:],
        user=parsed.username, 
        password=parsed.password,
        port=parsed.port
    )
    
    cursor = conn.cursor()
    print("Connected to database directly")
    
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Found tables: {tables}")
    
    # Use correct table names
    migrations = [
        ("ALTER TABLE bid_packets ADD COLUMN IF NOT EXISTS airline VARCHAR(50)", "airline to bid_packets"),
        ("ALTER TABLE bid_packets ADD COLUMN IF NOT EXISTS aircraft VARCHAR(50)", "aircraft to bid_packets"),
        ("ALTER TABLE bid_packets ADD COLUMN IF NOT EXISTS bid_month VARCHAR(20)", "bid_month to bid_packets"),
        ("ALTER TABLE bid_packets ADD COLUMN IF NOT EXISTS upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP", "upload_date to bid_packets"),
    ]
    
    # Check which user table exists
    if "user_profiles" in tables:
        migrations.extend([
            ("ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS login_count INTEGER DEFAULT 0", "login_count to user_profiles"),
            ("ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS last_login TIMESTAMP", "last_login to user_profiles"),
            ("ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS profile_completion_date TIMESTAMP", "profile_completion_date to user_profiles"),
        ])
    elif "users" in tables:
        migrations.extend([
            ("ALTER TABLE users ADD COLUMN IF NOT EXISTS login_count INTEGER DEFAULT 0", "login_count to users"), 
            ("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP", "last_login to users"),
            ("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_completion_date TIMESTAMP", "profile_completion_date to users"),
        ])
    
    for sql, desc in migrations:
        try:
            cursor.execute(sql)
            print(f"✅ Added {desc}")
        except Exception as e:
            print(f"⚠️ {desc}: {e}")
    
    # Create indexes
    indexes = [
        ("CREATE INDEX IF NOT EXISTS idx_bid_packets_airline ON bid_packets(airline)", "airline index"),
        ("CREATE INDEX IF NOT EXISTS idx_bid_packets_aircraft ON bid_packets(aircraft)", "aircraft index"),
        ("CREATE INDEX IF NOT EXISTS idx_bid_packets_month ON bid_packets(bid_month)", "bid_month index"),
    ]
    
    for sql, desc in indexes:
        try:
            cursor.execute(sql)
            print(f"✅ Created {desc}")
        except Exception as e:
            print(f"⚠️ {desc}: {e}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    
except Exception as e:
    print(f"Migration failed: {e}")
    import traceback
    traceback.print_exc()
