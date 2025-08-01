import sys
sys.path.append('src')

from core.app import create_app
from core.extensions import db
from sqlalchemy import text

print('Starting migration...')
app = create_app()

with app.app_context():
    print('Connected to database')
    
    # Add bid packet columns
    try:
        db.session.execute(text('ALTER TABLE bid_packet ADD COLUMN IF NOT EXISTS airline VARCHAR(50)'))
        print('✅ Added airline column')
    except Exception as e:
        print(f'Airline: {e}')
    
    try:
        db.session.execute(text('ALTER TABLE bid_packet ADD COLUMN IF NOT EXISTS aircraft VARCHAR(50)'))
        print('✅ Added aircraft column')
    except Exception as e:
        print(f'Aircraft: {e}')
    
    try:
        db.session.execute(text('ALTER TABLE bid_packet ADD COLUMN IF NOT EXISTS bid_month VARCHAR(20)'))
        print('✅ Added bid_month column')
    except Exception as e:
        print(f'Bid_month: {e}')
    
    try:
        db.session.execute(text('ALTER TABLE bid_packet ADD COLUMN IF NOT EXISTS upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP'))
        print('✅ Added upload_date column')
    except Exception as e:
        print(f'Upload_date: {e}')
    
    # Add user profile columns  
    try:
        db.session.execute(text('ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS login_count INTEGER DEFAULT 0'))
        print('✅ Added login_count column')
    except Exception as e:
        print(f'Login_count: {e}')
    
    try:
        db.session.execute(text('ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS last_login TIMESTAMP'))
        print('✅ Added last_login column')
    except Exception as e:
        print(f'Last_login: {e}')
    
    try:
        db.session.execute(text('ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS profile_completion_date TIMESTAMP'))
        print('✅ Added profile_completion_date column')
    except Exception as e:
        print(f'Profile_completion_date: {e}')
    
    # Create indexes for better performance
    try:
        db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_bid_packet_airline ON bid_packet(airline)'))
        print('✅ Created airline index')
    except Exception as e:
        print(f'Airline index: {e}')
    
    try:
        db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_bid_packet_aircraft ON bid_packet(aircraft)'))
        print('✅ Created aircraft index')
    except Exception as e:
        print(f'Aircraft index: {e}')
    
    try:
        db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_bid_packet_month ON bid_packet(bid_month)'))
        print('✅ Created bid_month index')
    except Exception as e:
        print(f'Bid_month index: {e}')
    
    # Commit all changes
    db.session.commit()
    print('✅ Migration completed successfully!')
    
    print('\n🎉 Database enhanced features added!')
    print('New columns available:')
    print('- bid_packet: airline, aircraft, bid_month, upload_date')
    print('- user_profile: login_count, last_login, profile_completion_date')
    print('- Indexes for better performance')
    
