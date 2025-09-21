#!/usr/bin/env python3
import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from src.models import IntersectionPoint, Station, TrainLine

DATABASE_URL = "postgresql+asyncpg://neondb_owner:npg_Vv1DS3cYLEyg@ep-shy-violet-a106m9dw-pooler.ap-southeast-1.aws.neon.tech/neondb?ssl=require"

async def check_intersections_and_stations():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print('=== INTERSECTION POINTS ===')
        result = await session.execute(select(IntersectionPoint))
        intersections = result.fetchall()
        if intersections:
            for intersection in intersections:
                point = intersection[0]
                print(f'  ID: {point.id}, Name: {point.name}, Description: {point.description}, Station Codes: {point.station_codes}')
        else:
            print('  No intersection points found')

        print('\n=== ALL STATIONS ===')
        result = await session.execute(select(Station.id, Station.name, Station.line_id, TrainLine.name.label('line_name')).join(TrainLine))
        stations = result.fetchall()

        print('Stations by line:')
        current_line = None
        for station in sorted(stations, key=lambda x: x.line_id):
            if current_line != station.line_id:
                current_line = station.line_id
                print(f'\n  Line {station.line_id} ({station.line_name}):')
            print(f'    Station ID: {station.id}, Name: {station.name}')

        print('\n=== DUPLICATE STATION NAMES ===')
        from collections import Counter
        station_names = [s.name for s in stations]
        duplicates = [name for name, count in Counter(station_names).items() if count > 1]
        if duplicates:
            for dup_name in duplicates:
                print(f'  Duplicate station name: {dup_name}')
                dup_stations = [s for s in stations if s.name == dup_name]
                for station in dup_stations:
                    print(f'    - ID: {station.id}, Line: {station.line_name} (ID: {station.line_id})')
        else:
            print('  No duplicate station names found')

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_intersections_and_stations())