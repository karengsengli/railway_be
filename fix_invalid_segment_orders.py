#!/usr/bin/env python3
"""
Fix invalid segment_order values in the database.
This script will find any route_segments with segment_order <= 0 and fix them.
"""

import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Database configuration
DATABASE_URL = "postgresql+asyncpg://neondb_owner:npg_Vv1DS3cYLEyg@ep-shy-violet-a106m9dw-pooler.ap-southeast-1.aws.neon.tech/neondb?ssl=require"

async def fix_invalid_segment_orders():
    """Fix invalid segment_order values in route_segments table"""

    # Create engine and session
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # Find segments with invalid orders (including negative values like -999999)
            result = await session.execute(
                text("SELECT id, train_route_id, segment_order FROM route_segments WHERE segment_order <= 0 OR segment_order < -100000 ORDER BY train_route_id, id")
            )
            invalid_segments = result.fetchall()

            if not invalid_segments:
                print("No invalid segment orders found.")
                return

            print(f"Found {len(invalid_segments)} segments with invalid orders:")
            for seg in invalid_segments:
                print(f"  ID: {seg.id}, Route: {seg.train_route_id}, Order: {seg.segment_order}")

            # Group by train_route_id to fix orders
            routes_to_fix = {}
            for seg in invalid_segments:
                route_id = seg.train_route_id
                if route_id not in routes_to_fix:
                    routes_to_fix[route_id] = []
                routes_to_fix[route_id].append(seg)

            # Fix each route
            for route_id, segments in routes_to_fix.items():
                print(f"\nFixing route {route_id}:")

                # Get all segments for this route in order
                result = await session.execute(
                    text("SELECT id FROM route_segments WHERE train_route_id = :route_id ORDER BY id")
                    .bindparam(route_id=route_id)
                )
                all_segments = result.fetchall()

                # Reassign orders starting from 1
                for i, seg in enumerate(all_segments, 1):
                    await session.execute(
                        text("UPDATE route_segments SET segment_order = :new_order WHERE id = :seg_id")
                        .bindparam(new_order=i, seg_id=seg.id)
                    )
                    print(f"  Updated segment {seg.id} to order {i}")

            # Commit the changes
            await session.commit()
            print(f"\nSuccessfully fixed {len(invalid_segments)} invalid segment orders.")

        except Exception as e:
            await session.rollback()
            print(f"Error fixing segment orders: {e}")
            raise
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_invalid_segment_orders())