#!/usr/bin/env python3

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def fix_foreign_key_constraint():
    """Fix the foreign key constraint to add RESTRICT behavior"""

    # Database connection from environment
    DATABASE_URL = os.getenv("DATABASE_URL")

    if not DATABASE_URL:
        print("DATABASE_URL not found in environment")
        return

    # Convert SQLAlchemy URL format to AsyncPG format
    if DATABASE_URL.startswith("postgresql+asyncpg://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # First, check current foreign key constraints
        print("Checking current foreign key constraints...")
        constraints = await conn.fetch("""
            SELECT conname, conrelid::regclass, confrelid::regclass, confdeltype
            FROM pg_constraint
            WHERE contype = 'f'
            AND conrelid = 'train_companies'::regclass
            AND confrelid = 'regions'::regclass;
        """)

        print("Current constraints:")
        for constraint in constraints:
            print(f"  {constraint['conname']}: {constraint['conrelid']} -> {constraint['confrelid']}, delete action: {constraint['confdeltype']}")

        # Drop the existing foreign key constraint
        print("\nDropping existing foreign key constraint...")
        await conn.execute("""
            ALTER TABLE train_companies
            DROP CONSTRAINT train_companies_region_id_fkey;
        """)

        # Add the new constraint with RESTRICT
        print("Adding new foreign key constraint with RESTRICT...")
        await conn.execute("""
            ALTER TABLE train_companies
            ADD CONSTRAINT train_companies_region_id_fkey
            FOREIGN KEY (region_id) REFERENCES regions(id) ON DELETE RESTRICT;
        """)

        # Verify the new constraint
        print("\nVerifying new constraint...")
        new_constraints = await conn.fetch("""
            SELECT conname, conrelid::regclass, confrelid::regclass, confdeltype
            FROM pg_constraint
            WHERE contype = 'f'
            AND conrelid = 'train_companies'::regclass
            AND confrelid = 'regions'::regclass;
        """)

        print("New constraints:")
        for constraint in new_constraints:
            print(f"  {constraint['conname']}: {constraint['conrelid']} -> {constraint['confrelid']}, delete action: {constraint['confdeltype']}")

        print("\nForeign key constraint updated successfully!")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(fix_foreign_key_constraint())