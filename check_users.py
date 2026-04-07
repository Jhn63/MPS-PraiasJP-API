import sys
import os

# Change to app/src directory so database path is correct
os.chdir('app/src')
sys.path.insert(0, '.')

from database.db import SessionLocal
from modules.users.user_model import User

db = SessionLocal()
users = db.query(User).all()
print(f'Total users: {len(users)}')
for u in users:
    print(f'  - ID: {u.id}, Username: "{u.username}", Password: {u.password}')
db.close()
