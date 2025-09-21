#!/usr/bin/env python3
"""
Database Cleanup Script - Remove Unused Tables

This script removes tables that are not currently implemented or used in the project:
- transit_routes, route_stops (alternative route system)
- station_lines (multi-line station support - not implemented)
- unified_routes, route_segments (alternative unified route system)

Before running, make sure to backup your database!
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def cleanup_unused_tables():
    """Remove unused tables from the database."""

    # Get database URL and convert for asyncpg
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("[ERROR] DATABASE_URL not found in environment variables")
        return

    # Convert SQLAlchemy URL to asyncpg format
    asyncpg_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')

    try:
        print("Connecting to database...")
        conn = await asyncpg.connect(asyncpg_url)

        # List of unused tables to remove (in order to handle foreign key constraints)
        unused_tables = [
            'route_segments',        # References unified_routes
            'unified_routes',        # References train_lines
            'route_stops',          # References transit_routes and stations
            'transit_routes',       # Standalone table
            'station_lines',        # References stations and train_lines
        ]

        print("\nTables to be removed:")
        for table in unused_tables:
            print(f"   - {table}")

        # Check which tables actually exist
        existing_tables_query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = ANY($1);
        """

        existing_tables = await conn.fetch(existing_tables_query, unused_tables)
        existing_table_names = [row['table_name'] for row in existing_tables]

        if not existing_table_names:
            print("\n[INFO] No unused tables found to remove.")
            await conn.close()
            return

        print(f"\nFound {len(existing_table_names)} unused tables to remove:")
        for table in existing_table_names:
            print(f"   - {table}")

        # Confirm before deletion
        print(f"\nWARNING: This will permanently delete {len(existing_table_names)} tables and all their data!")
        print("Make sure you have backed up your database before proceeding.")

        confirmation = input("\nType 'YES' to confirm deletion: ")
        if confirmation != 'YES':
            print("[INFO] Operation cancelled.")
            await conn.close()
            return

        print("\nRemoving unused tables...")

        # Remove tables in order (to handle foreign key constraints)
        for table in unused_tables:
            if table in existing_table_names:
                try:
                    await conn.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
                    print(f"   [OK] Removed table: {table}")
                except Exception as e:
                    print(f"   [ERROR] Error removing {table}: {e}")

        # Verify cleanup
        remaining_check = await conn.fetch(existing_tables_query, unused_tables)
        remaining_tables = [row['table_name'] for row in remaining_check]

        if remaining_tables:
            print(f"\n[WARNING] Some tables could not be removed: {remaining_tables}")
        else:
            print(f"\n[SUCCESS] Successfully removed all {len(existing_table_names)} unused tables!")

        # Show final table count
        final_tables = await conn.fetch("""
            SELECT COUNT(*) as count
            FROM information_schema.tables
            WHERE table_schema = 'public';
        """)

        print(f"[INFO] Database now has {final_tables[0]['count']} tables remaining.")

        await conn.close()
        print("Database connection closed.")

    except Exception as e:
        print(f"[ERROR] Error: {e}")

async def list_current_tables():
    """List all current tables for reference."""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("[ERROR] DATABASE_URL not found")
        return

    asyncpg_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')

    try:
        conn = await asyncpg.connect(asyncpg_url)

        tables = await conn.fetch("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)

        print("Current database tables:")
        for table in tables:
            print(f"   - {table['table_name']}")

        await conn.close()

    except Exception as e:
        print(f"[ERROR] Error listing tables: {e}")

if __name__ == "__main__":
    print("Database Cleanup Tool")
    print("=" * 50)

    # First show current tables
    print("Current state:")
    asyncio.run(list_current_tables())

    print("\n" + "=" * 50)

    # Then run cleanup
    asyncio.run(cleanup_unused_tables())