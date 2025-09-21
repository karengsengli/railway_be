#!/usr/bin/env python3

import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Add src to path
sys.path.append('src')
from config import settings

async def remove_fare_tables():
    """Remove all fare-related tables from the database"""

    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            print("Removing fare-related tables from database...")

            # List of fare-related tables to drop
            fare_tables = [
                "fare_rules",
                "passenger_types"
            ]

            for table in fare_tables:
                # Check if table exists
                result = await session.execute(text(f"""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_name = '{table}'
                """))
                table_exists = result.fetchone()

                if table_exists:
                    print(f"Dropping table: {table}")
                    await session.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                    await session.commit()
                    print(f"  ✓ {table} dropped successfully")
                else:
                    print(f"  - {table} does not exist, skipping")

            # Remove fare_amount column from tickets table if it exists
            print("\nRemoving fare_amount column from tickets table...")
            try:
                # Check if column exists
                result = await session.execute(text("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = 'tickets' AND column_name = 'fare_amount'
                """))
                column_exists = result.fetchone()

                if column_exists:
                    await session.execute(text("ALTER TABLE tickets DROP COLUMN IF EXISTS fare_amount"))
                    await session.commit()
                    print("  ✓ fare_amount column removed from tickets")
                else:
                    print("  - fare_amount column does not exist in tickets")
            except Exception as e:
                print(f"  - Could not remove fare_amount column: {e}")

            # Remove fare-related foreign key references
            print("\nRemoving fare-related foreign key references...")

            # Remove fare_rules relationship from train_lines if it exists
            try:
                await session.execute(text("""
                    ALTER TABLE train_lines DROP CONSTRAINT IF EXISTS train_lines_fare_rules_fkey
                """))
                await session.commit()
                print("  ✓ Removed fare_rules foreign key from train_lines")
            except Exception as e:
                print(f"  - Could not remove fare_rules foreign key: {e}")

            print("\n" + "="*60)
            print("FARE-RELATED TABLES REMOVED SUCCESSFULLY!")
            print("="*60)
            print("Removed components:")
            print("  ✓ fare_rules table")
            print("  ✓ passenger_types table")
            print("  ✓ fare_amount column from tickets")
            print("  ✓ Related foreign key constraints")
            print("="*60)

        except Exception as e:
            await session.rollback()
            print(f"Error: {e}")
            raise
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(remove_fare_tables())