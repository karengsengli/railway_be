"""
Add new columns to users table to match frontend schema
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def migrate_users_table():
    """Add new columns to users table"""

    # Database connection from .env
    DATABASE_URL = os.getenv("DATABASE_URL")

    # Convert SQLAlchemy URL to asyncpg format
    if DATABASE_URL.startswith("postgresql+asyncpg://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # Add new columns to users table
        print("Adding new columns to users table...")

        await conn.execute('''
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS first_name VARCHAR(100),
            ADD COLUMN IF NOT EXISTS last_name VARCHAR(100),
            ADD COLUMN IF NOT EXISTS phone VARCHAR(20),
            ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE NOT NULL;
        ''')

        print("SUCCESS: Successfully added new columns to users table")

        # Update existing users to have active status
        await conn.execute('''
            UPDATE users
            SET is_active = TRUE
            WHERE is_active IS NULL;
        ''')

        print("SUCCESS: Updated existing users to be active")

    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(migrate_users_table())