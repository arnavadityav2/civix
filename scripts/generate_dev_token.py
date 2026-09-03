import os
import sys
# Ensure civix_api can be imported when running from scripts/
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import jwt
from datetime import datetime, timedelta, timezone
import argparse
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from civix_api.config import settings

async def get_fallback_user():
    engine = create_async_engine(settings.civix_database_url)
    async with engine.connect() as conn:
        res = await conn.execute(text('SELECT user_id, username FROM civix.civix_user LIMIT 1'))
        row = res.first()
        if row:
            return row.user_id, row.username
        return None, None

async def main():
    parser = argparse.ArgumentParser(description="Generate a development JWT for Civix")
    parser.add_argument("--user-id", type=str, help="UUID of the user to generate the token for")
    parser.add_argument("--expires-in-days", type=int, default=30, help="Expiration time in days")
    
    args = parser.parse_args()
    
    secret = settings.civix_jwt_secret
    if not secret:
        print("Error: CIVIX_JWT_SECRET environment variable is missing.")
        sys.exit(1)
        
    user_id = args.user_id
    username = "unknown"
    if not user_id:
        user_id, username = await get_fallback_user()
        if not user_id:
            print("Error: No users found in the database. Please seed the database first.")
            sys.exit(1)
            
    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(days=args.expires_in_days),
        "role": "INVESTIGATOR"
    }
    
    token = jwt.encode(payload, secret, algorithm="HS256")
    
    print("\n--- CIVIX DEVELOPMENT TOKEN ---")
    print(f"User ID:  {user_id}")
    print(f"Username: {username}")
    print(f"Expires:  {args.expires_in_days} days")
    print("-------------------------------\n")
    print(token)
    print("\nAdd this token to your frontend .env.local as VITE_DEV_JWT")

if __name__ == "__main__":
    asyncio.run(main())
