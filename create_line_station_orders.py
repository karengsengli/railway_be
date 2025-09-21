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

# BTS Lines with ordered stations (matching our database)
BTS_LINES_ORDERED = {
    "Green Line (Sukhumvit)": [
        "N8", "N7", "N6", "N5", "N4", "N3", "N2", "N1", "CEN",
        "E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8", "E9",
        "E10", "E11", "E12", "E13", "E14", "E15", "E16", "E17",
        "E18", "E19", "E20", "E21", "E22", "E23"
    ],
    "Green Line (Silom)": [
        "CEN", "S1", "S2", "S3", "S4", "S5", "S6", "S7",
        "S8", "S9", "S10", "S11", "S12"
    ],
    "Gold Line": [
        "G1", "G2", "G3"
    ],
    "Pink Line": [
        "PK01", "PK02", "PK03", "PK04", "PK05", "PK06", "PK07", "PK08", "PK09", "PK10",
        "PK11", "PK12", "PK13", "PK14", "PK15", "PK16", "PK17", "PK18", "PK19", "PK20",
        "PK21", "PK22", "PK23", "PK24", "PK25", "PK26", "PK27", "PK28", "PK29", "PK30"
    ],
    "Yellow Line": [
        "YL01", "YL02", "YL03", "YL04", "YL05", "YL06", "YL07", "YL08", "YL09", "YL10",
        "YL11", "YL12", "YL13", "YL14", "YL15", "YL16", "YL17", "YL18", "YL19", "YL20",
        "YL21", "YL22", "YL23"
    ]
}

async def create_line_station_orders():
    """Create line station orders for the route management system"""

    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            print("Creating line station orders for BTS lines...")

            # Check if line_station_orders table exists
            result = await session.execute(text("""
                SELECT table_name FROM information_schema.tables
                WHERE table_name = 'line_station_orders'
            """))
            table_exists = result.fetchone()

            if not table_exists:
                print("Creating line_station_orders table...")
                await session.execute(text("""
                    CREATE TABLE line_station_orders (
                        id SERIAL PRIMARY KEY,
                        line_id BIGINT NOT NULL REFERENCES train_lines(id),
                        station_id BIGINT NOT NULL REFERENCES stations(id),
                        position INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW(),
                        UNIQUE(line_id, station_id),
                        UNIQUE(line_id, position)
                    )
                """))
                await session.commit()
                print("line_station_orders table created")
            else:
                print("line_station_orders table already exists")

            # Clean existing orders
            print("Cleaning existing line station orders...")
            await session.execute(text("DELETE FROM line_station_orders"))
            await session.commit()

            # Get all lines and stations
            lines_result = await session.execute(text("""
                SELECT id, name FROM train_lines ORDER BY name
            """))
            lines = {row.name: row.id for row in lines_result.fetchall()}

            stations_result = await session.execute(text("""
                SELECT id, code, name, line_id FROM stations ORDER BY code
            """))
            stations = {}
            for row in stations_result.fetchall():
                stations[row.code] = {
                    'id': row.id,
                    'name': row.name,
                    'line_id': row.line_id
                }

            print(f"Found {len(lines)} lines and {len(stations)} stations")

            # Create station orders for each line
            print("Creating station orders...")
            total_orders = 0

            for line_name, station_codes in BTS_LINES_ORDERED.items():
                if line_name in lines:
                    line_id = lines[line_name]
                    print(f"  Processing {line_name}...")

                    for position, station_code in enumerate(station_codes, start=1):
                        if station_code in stations:
                            station = stations[station_code]

                            # Insert station order
                            await session.execute(text("""
                                INSERT INTO line_station_orders
                                (line_id, station_id, position, created_at, updated_at)
                                VALUES (:line_id, :station_id, :position, NOW(), NOW())
                            """), {
                                "line_id": line_id,
                                "station_id": station['id'],
                                "position": position
                            })

                            total_orders += 1
                            print(f"    {position:2d}. {station_code} - {station['name']}")

            await session.commit()
            print(f"Created {total_orders} station orders")

            # Verify the results
            print("\nVerifying station orders...")
            result = await session.execute(text("""
                SELECT
                    tl.name as line_name,
                    COUNT(lso.id) as station_count,
                    MIN(lso.position) as min_pos,
                    MAX(lso.position) as max_pos
                FROM train_lines tl
                LEFT JOIN line_station_orders lso ON tl.id = lso.line_id
                GROUP BY tl.id, tl.name
                ORDER BY tl.name
            """))

            print("Station counts by line:")
            for row in result.fetchall():
                print(f"  {row.line_name}: {row.station_count} stations (positions {row.min_pos}-{row.max_pos})")

            # Summary
            print("\n" + "="*60)
            print("LINE STATION ORDERS CREATED SUCCESSFULLY!")
            print("="*60)
            print(f"Total Station Orders: {total_orders}")
            print("="*60)

            print("\nStation Ordering Features Available:")
            print("  - Station positions within each line")
            print("  - Ordered station sequences for route planning")
            print("  - Support for route management API endpoints")
            print("  - Compatible with pathfinding algorithms")

        except Exception as e:
            await session.rollback()
            print(f"Error: {e}")
            raise
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_line_station_orders())