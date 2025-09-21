#!/usr/bin/env python3
"""
Create Route Management Tables

This script creates the new train_routes and route_segments tables
for managing one-to-one train line routes with sortable station connections.
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def create_route_management_tables():
    """Create the route management tables."""

    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("[ERROR] DATABASE_URL not found in environment variables")
        return

    asyncpg_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')

    try:
        print("Connecting to database...")
        conn = await asyncpg.connect(asyncpg_url)

        print("\nCreating route management tables...")

        # Create train_routes table
        print("Creating train_routes table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS train_routes (
                id BIGSERIAL PRIMARY KEY,
                line_id BIGINT UNIQUE NOT NULL REFERENCES train_lines(id) ON DELETE CASCADE,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                total_distance_km DECIMAL(8,2),
                total_duration_minutes INTEGER,
                status VARCHAR(50) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("[OK] Created train_routes table")

        # Create route_segments table
        print("Creating route_segments table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS route_segments (
                id BIGSERIAL PRIMARY KEY,
                train_route_id BIGINT NOT NULL REFERENCES train_routes(id) ON DELETE CASCADE,
                from_station_id BIGINT NOT NULL REFERENCES stations(id) ON DELETE CASCADE,
                to_station_id BIGINT NOT NULL REFERENCES stations(id) ON DELETE CASCADE,
                segment_order INTEGER NOT NULL,
                distance_km DECIMAL(8,2) NOT NULL,
                duration_minutes INTEGER NOT NULL,
                transport_type VARCHAR(50) DEFAULT 'train',
                status VARCHAR(50) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                -- Constraints
                UNIQUE(train_route_id, segment_order),
                UNIQUE(train_route_id, from_station_id, to_station_id),
                CHECK(from_station_id != to_station_id),
                CHECK(segment_order > 0),
                CHECK(distance_km > 0),
                CHECK(duration_minutes > 0)
            );
        """)
        print("[OK] Created route_segments table")

        # Create indexes for better performance
        print("Creating indexes...")
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_train_routes_line_id ON train_routes(line_id);
            CREATE INDEX IF NOT EXISTS idx_route_segments_train_route_id ON route_segments(train_route_id);
            CREATE INDEX IF NOT EXISTS idx_route_segments_order ON route_segments(train_route_id, segment_order);
            CREATE INDEX IF NOT EXISTS idx_route_segments_stations ON route_segments(from_station_id, to_station_id);
        """)
        print("[OK] Created indexes")

        # Create updated_at trigger function if not exists
        print("Creating updated_at trigger...")
        await conn.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql';
        """)

        # Create triggers for updated_at
        await conn.execute("""
            DROP TRIGGER IF EXISTS update_train_routes_updated_at ON train_routes;
            CREATE TRIGGER update_train_routes_updated_at
                BEFORE UPDATE ON train_routes
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """)

        await conn.execute("""
            DROP TRIGGER IF EXISTS update_route_segments_updated_at ON route_segments;
            CREATE TRIGGER update_route_segments_updated_at
                BEFORE UPDATE ON route_segments
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """)
        print("[OK] Created updated_at triggers")

        print("\n[SUCCESS] Route management tables created successfully!")

        # List all tables to verify
        print("\nDatabase tables:")
        result = await conn.fetch("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)

        for row in result:
            print(f"  - {row['table_name']}")

        await conn.close()

    except Exception as e:
        print(f"[ERROR] Failed to create tables: {e}")
        return

if __name__ == "__main__":
    asyncio.run(create_route_management_tables())