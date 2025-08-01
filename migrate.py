import sys
sys.path.append('src')

from core.app import create_app
from core.models import db
from sqlalchemy import text

print('Starting migration...')
app = create_app()
with app.app_context():
    print('Connected to database')
    
    # Add bid packet columns
    try:
        db.engine.execute(text('ALTER TABLE bid_packet ADD COLUMN IF NOT EXISTS airline VARCHAR(50)'))
        print('Added airline column')
    except Exception as e:
        print(f'Airline column: {e}')
    
    try:
        db.engine.execute(text('ALTER TABLE bid_packet ADD COLUMN IF NOT EXISTS aircraft VARCHAR(50)'))
        print('Added aircraft column')
    except Exception as e:
        print(f'Aircraft column: {e}')
    
    try:
        db.engine.execute(text('ALTER TABLE bid_packet ADD COLUMN IF NOT EXISTS bid_month VARCHAR(20)'))
        print('Added bid_month column')
    except Exception as e:
        print(f'Bid_month column: {e}')
    
    try:
        db.engine.execute(text('ALTER TABLE bid_packet ADD COLUMN IF NOT EXISTS upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP'))
        print('Added upload_date column')
    except Exception as e:
        print(f'Upload_date column: {e}')
    
    # Add user profile columns
    try:
        db.engine.execute(text('ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS login_count INTEGER DEFAULT 0'))
        print('Added login_count column')
    except Exception as e:
        print(f'Login_count column: {e}')
    
    try:
        db.engine.execute(text('ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS last_login TIMESTAMP'))
        print('Added last_login column')
    except Exception as e:
        print(f'Last_login column: {e}')
    
    try:
        db.engine.execute(text('ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS profile_completion_date TIMESTAMP'))
        print('Added profile_completion_date column')
    except Exception as e:
        print(f'Profile_completion_date column: {e}')
    
    # Create indexes
    try:
        db.engine.execute(text('CREATE INDEX IF NOT EXISTS idx_bid_packet_airline ON bid_packet(airline)'))
        print('Created airline index')
    except Exception as e:
        print(f'Airline index: {e}')
    
    try:
        db.engine.execute(text('CREATE INDEX IF NOT EXISTS idx_bid_packet_aircraft ON bid_packet(aircraft)'))
        print('Created aircraft index')
    except Exception as e:
        print(f'Aircraft index: {e}')
    
    db.session.commit()
    print('Migration completed successfully!')
