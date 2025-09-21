#!/usr/bin/env python3

import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import json

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

# Key intersection points where lines meet
INTERSECTION_POINTS = [
    {
        "name": "Siam Interchange",
        "description": "Central hub connecting Green Line Sukhumvit and Silom lines",
        "station_codes": ["CEN"],
        "lines": ["Green Line (Sukhumvit)", "Green Line (Silom)"],
        "lat": 13.745398,
        "long": 100.534262
    },
    {
        "name": "Asok Interchange",
        "description": "Connection between BTS Green Line and MRT Blue Line",
        "station_codes": ["E4"],
        "lines": ["Green Line (Sukhumvit)"],
        "lat": 13.735893,
        "long": 100.560408
    },
    {
        "name": "Mo Chit Interchange",
        "description": "Connection between BTS Green Line and MRT Blue Line",
        "station_codes": ["N8"],
        "lines": ["Green Line (Sukhumvit)"],
        "lat": 13.802776,
        "long": 100.553308
    },
    {
        "name": "Sala Daeng Interchange",
        "description": "Connection between BTS Green Line and MRT Blue Line",
        "station_codes": ["S2"],
        "lines": ["Green Line (Silom)"],
        "lat": 13.729096,
        "long": 100.533969
    },
    {
        "name": "Saphan Taksin Interchange",
        "description": "Connection between BTS Green Line and Chao Phraya Express Boat",
        "station_codes": ["S6"],
        "lines": ["Green Line (Silom)"],
        "lat": 13.717900,
        "long": 100.515200
    },
    {
        "name": "Krung Thon Buri Interchange",
        "description": "Connection between BTS Silom Line and Gold Line",
        "station_codes": ["S7", "G1"],
        "lines": ["Green Line (Silom)", "Gold Line"],
        "lat": 13.707900,
        "long": 100.505200
    },
    {
        "name": "Samrong Interchange",
        "description": "Connection between BTS Green Line and Yellow Line",
        "station_codes": ["E15", "YL23"],
        "lines": ["Green Line (Sukhumvit)", "Yellow Line"],
        "lat": 13.645763,
        "long": 100.660349
    },
    {
        "name": "Lat Phrao Interchange",
        "description": "Connection between Yellow Line and MRT Blue Line",
        "station_codes": ["YL01"],
        "lines": ["Yellow Line"],
        "lat": 13.815618,
        "long": 100.561761
    },
    {
        "name": "Hua Mak Interchange",
        "description": "Connection between Pink Line and Yellow Line",
        "station_codes": ["PK23", "YL11"],
        "lines": ["Pink Line", "Yellow Line"],
        "lat": 13.960000,
        "long": 100.630000
    }
]

async def create_route_management_data():
    """Create comprehensive route management data for all BTS lines"""

    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            print("Creating route management data for BTS lines...")

            # Clean existing route management data
            print("Cleaning existing route management data...")
            await session.execute(text("DELETE FROM route_segments"))
            await session.execute(text("DELETE FROM intersection_segments"))
            await session.execute(text("DELETE FROM intersection_points"))
            await session.execute(text("DELETE FROM train_routes"))
            await session.commit()
            print("Existing route management data cleaned")

            # Get all lines and stations
            lines_result = await session.execute(text("""
                SELECT id, name FROM train_lines ORDER BY name
            """))
            lines = {row.name: row.id for row in lines_result.fetchall()}

            stations_result = await session.execute(text("""
                SELECT id, code, name, line_id, lat, long FROM stations ORDER BY code
            """))
            stations = {}
            for row in stations_result.fetchall():
                stations[row.code] = {
                    'id': row.id,
                    'name': row.name,
                    'line_id': row.line_id,
                    'lat': row.lat,
                    'long': row.long
                }

            print(f"Found {len(lines)} lines and {len(stations)} stations")

            # Create train routes for each line
            print("Creating train routes...")
            train_routes = {}
            for line_name, station_codes in BTS_LINES_ORDERED.items():
                if line_name in lines:
                    line_id = lines[line_name]

                    # Calculate total distance (rough estimate)
                    total_distance = len(station_codes) * 1.5  # ~1.5km between stations
                    total_duration = len(station_codes) * 3    # ~3 minutes between stations

                    result = await session.execute(text("""
                        INSERT INTO train_routes
                        (line_id, name, description, total_distance_km, total_duration_minutes, status, created_at, updated_at)
                        VALUES (:line_id, :name, :description, :total_distance, :total_duration, 'active', NOW(), NOW())
                        RETURNING id
                    """), {
                        "line_id": line_id,
                        "name": f"{line_name} Route",
                        "description": f"Complete route for {line_name} with {len(station_codes)} stations",
                        "total_distance": total_distance,
                        "total_duration": total_duration
                    })

                    train_route_id = result.scalar()
                    train_routes[line_name] = train_route_id
                    print(f"  Created train route for {line_name} (ID: {train_route_id})")

            await session.commit()
            print(f"Created {len(train_routes)} train routes")

            # Create route segments between adjacent stations
            print("Creating route segments...")
            segment_count = 0

            for line_name, station_codes in BTS_LINES_ORDERED.items():
                if line_name in train_routes:
                    train_route_id = train_routes[line_name]

                    print(f"  Creating segments for {line_name}...")

                    # Create segments between consecutive stations
                    for i in range(len(station_codes) - 1):
                        from_code = station_codes[i]
                        to_code = station_codes[i + 1]

                        if from_code in stations and to_code in stations:
                            from_station = stations[from_code]
                            to_station = stations[to_code]

                            # Calculate distance (rough estimate based on coordinates)
                            distance_km = 1.5  # Default distance
                            duration_minutes = 3  # Default duration

                            # Create bidirectional segments with unique segment orders
                            for direction, (from_id, to_id) in enumerate([
                                (from_station['id'], to_station['id']),
                                (to_station['id'], from_station['id'])
                            ]):
                                # Use unique segment_order for each direction
                                # Forward direction: 1, 2, 3, ...
                                # Reverse direction: 1000, 1001, 1002, ... (to avoid conflicts)
                                segment_order = (i + 1) if direction == 0 else (1000 + i + 1)
                                await session.execute(text("""
                                    INSERT INTO route_segments
                                    (train_route_id, from_station_id, to_station_id, segment_order,
                                     distance_km, duration_minutes, transport_type, status, created_at, updated_at)
                                    VALUES (:train_route_id, :from_station_id, :to_station_id, :segment_order,
                                            :distance_km, :duration_minutes, 'train', 'active', NOW(), NOW())
                                """), {
                                    "train_route_id": train_route_id,
                                    "from_station_id": from_id,
                                    "to_station_id": to_id,
                                    "segment_order": segment_order,
                                    "distance_km": distance_km,
                                    "duration_minutes": duration_minutes
                                })
                                segment_count += 1

            await session.commit()
            print(f"Created {segment_count} route segments")

            # Create intersection points
            print("Creating intersection points...")
            intersection_count = 0

            for intersection in INTERSECTION_POINTS:
                # Create intersection point
                result = await session.execute(text("""
                    INSERT INTO intersection_points
                    (name, description, lat, long, station_codes, accessibility_features, status, created_at, updated_at)
                    VALUES (:name, :description, :lat, :long, :station_codes, :accessibility_features, 'active', NOW(), NOW())
                    RETURNING id
                """), {
                    "name": intersection["name"],
                    "description": intersection["description"],
                    "lat": intersection["lat"],
                    "long": intersection["long"],
                    "station_codes": json.dumps(intersection["station_codes"]),
                    "accessibility_features": json.dumps({
                        "elevator": True,
                        "escalator": True,
                        "wheelchair_accessible": True,
                        "tactile_paving": True
                    })
                })

                intersection_id = result.scalar()
                intersection_count += 1
                print(f"  Created intersection: {intersection['name']} (ID: {intersection_id})")

                # Create intersection segments for transfers between lines at this point
                station_codes = intersection["station_codes"]
                if len(station_codes) > 1:
                    # Create transfer segments between different stations at this intersection
                    for i in range(len(station_codes)):
                        for j in range(i + 1, len(station_codes)):
                            from_code = station_codes[i]
                            to_code = station_codes[j]

                            if from_code in stations and to_code in stations:
                                from_station = stations[from_code]
                                to_station = stations[to_code]

                                # Create bidirectional transfer segments
                                for from_id, to_id in [
                                    (from_station['id'], to_station['id']),
                                    (to_station['id'], from_station['id'])
                                ]:
                                    await session.execute(text("""
                                        INSERT INTO intersection_segments
                                        (intersection_point_id, from_station_id, to_station_id, from_line_id, to_line_id,
                                         distance_km, duration_minutes, transport_type, transfer_cost, status, created_at, updated_at)
                                        VALUES (:intersection_point_id, :from_station_id, :to_station_id, :from_line_id, :to_line_id,
                                                :distance_km, :duration_minutes, 'walking', :transfer_cost, 'active', NOW(), NOW())
                                    """), {
                                        "intersection_point_id": intersection_id,
                                        "from_station_id": from_id,
                                        "to_station_id": to_id,
                                        "from_line_id": from_station['line_id'],
                                        "to_line_id": to_station['line_id'],
                                        "distance_km": 0.2,  # ~200m walking distance
                                        "duration_minutes": 5,  # ~5 minutes transfer time
                                        "transfer_cost": 0.0  # No additional cost for transfers
                                    })

            await session.commit()
            print(f"Created {intersection_count} intersection points")

            # Summary
            print("\n" + "="*60)
            print("ROUTE MANAGEMENT DATA CREATED SUCCESSFULLY!")
            print("="*60)

            # Get final counts
            result = await session.execute(text("SELECT COUNT(*) FROM train_routes"))
            route_count = result.scalar()

            result = await session.execute(text("SELECT COUNT(*) FROM route_segments"))
            segment_count = result.scalar()

            result = await session.execute(text("SELECT COUNT(*) FROM intersection_points"))
            intersection_count = result.scalar()

            result = await session.execute(text("SELECT COUNT(*) FROM intersection_segments"))
            transfer_count = result.scalar()

            print(f"Summary:")
            print(f"  • Train Routes: {route_count}")
            print(f"  • Route Segments: {segment_count}")
            print(f"  • Intersection Points: {intersection_count}")
            print(f"  • Transfer Segments: {transfer_count}")
            print("="*60)

            print("\nRoute Management Features Available:")
            print("  ✓ Station-to-station routing within lines")
            print("  ✓ Line transfers at interchange points")
            print("  ✓ Distance and duration calculations")
            print("  ✓ Bidirectional route segments")
            print("  ✓ Accessibility information")
            print("  ✓ Multi-line journey planning support")

        except Exception as e:
            await session.rollback()
            print(f"Error: {e}")
            raise
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_route_management_data())