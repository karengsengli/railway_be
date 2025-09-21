#!/usr/bin/env python3

import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Add src to path
sys.path.append('src')

from config import settings

async def add_station_codes():
    print("Adding code column to stations table and extracting codes...")

    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # Check if code column already exists
            result = await session.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'stations' AND column_name = 'code'
            """))
            code_column_exists = result.fetchone()

            if not code_column_exists:
                print("Adding code column to stations table...")
                await session.execute(text("""
                    ALTER TABLE stations ADD COLUMN code VARCHAR(10)
                """))
                await session.commit()
                print("Code column added successfully")
            else:
                print("Code column already exists")

            # Get all stations with their current names
            result = await session.execute(text("""
                SELECT id, name FROM stations ORDER BY id
            """))
            stations = result.fetchall()

            print(f"Processing {len(stations)} stations...")

            # Update each station to extract code and clean name
            updated_count = 0
            for station in stations:
                station_id = station.id
                full_name = station.name

                # Extract code and name from format "CODE - Name"
                if " - " in full_name:
                    parts = full_name.split(" - ", 1)
                    code = parts[0].strip()
                    clean_name = parts[1].strip()

                    # Update the station with separate code and clean name
                    await session.execute(text("""
                        UPDATE stations
                        SET code = :code, name = :name
                        WHERE id = :id
                    """), {
                        "code": code,
                        "name": clean_name,
                        "id": station_id
                    })

                    updated_count += 1
                    print(f"Updated: {code} - {clean_name}")

            await session.commit()
            print(f"Successfully updated {updated_count} stations")

            # Verify the results
            result = await session.execute(text("""
                SELECT code, name,
                       (SELECT name FROM train_lines WHERE id = stations.line_id) as line_name
                FROM stations
                ORDER BY line_id, code
            """))

            updated_stations = result.fetchall()

            print("\nUpdated stations by line:")
            current_line = None
            for station in updated_stations:
                if station.line_name != current_line:
                    current_line = station.line_name
                    print(f"\n{current_line}:")
                print(f"  {station.code} - {station.name}")

            print(f"\nTotal stations with codes: {len(updated_stations)}")

        except Exception as e:
            await session.rollback()
            print(f"Error: {e}")
            raise
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(add_station_codes())