#!/usr/bin/env python
"""Debug script to test database access from app context"""
import sys
import os

# Add app/src to path and change working dir
script_dir = os.path.dirname(os.path.abspath(__file__))
app_src_dir = os.path.join(script_dir, 'app', 'src')
sys.path.insert(0, app_src_dir)
os.chdir(app_src_dir)

from database.db import SessionLocal
from modules.users.user_model import User

print("Testing database access...")
db = SessionLocal()

try:
    # Query all users
    all_users = db.query(User).all()
    print(f'\nTotal users in database: {len(all_users)}')
    for user in all_users:
        print(f'  User ID={user.id}, username="{user.username}", password="***"')
        print(f'    └─ Username (repr): {repr(user.username)}')
    
    # Test the exact query used in facade
    test_username = "jhonMaconha"
    print(f'\nSearching for username: "{test_username}"')
    print(f'  └─ Repr: {repr(test_username)}')
    print(f'  └─ Bytes: {test_username.encode("utf-8")}')
    
    found_user = db.query(User).filter(User.username == test_username).first()
    
    if found_user:
        print(f'✓ Found user: ID={found_user.id}, username="{found_user.username}"')
    else:
        print(f'✗ User not found with ==')
        
        # Try different SQLAlchemy methods
        print(f'\nTrying different SQLAlchemy filter methods:')
        
        # Method 1: Using ilike (case-insensitive)
        import sqlalchemy
        result = db.query(User).filter(User.username.ilike(test_username)).first()
        print(f'  ilike: {result is not None} (username="{result.username if result else "N/A"}")')
        
        # Method 2: Using == with explicit collation
        try:
            result = db.query(User).filter(User.username == test_username).collate('NOCASE').first()
            print(f'  == with NOCASE collation: {result is not None}')
        except:
            print(f'  == with NOCASE collation: Error')
        
        # Method 3: Get all and filter in Python
        all_users = db.query(User).all()
        result = next((u for u in all_users if u.username == test_username), None)
        print(f'  Python filter on all: {result is not None} (username="{result.username if result else "N/A"}")')
        
        # Method 4: Using get with just ID (verify query works at all)
        result = db.query(User).get(1)
        print(f'  Direct get(1): {result is not None} (username="{result.username if result else "N/A"}")')

except Exception as e:
    print(f'Error: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()

finally:
    db.close()
