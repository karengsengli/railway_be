#!/usr/bin/env python3
"""
Insert Bangkok BTS Stations

This script inserts all Bangkok BTS stations from both Sukhumvit and Silom lines
into the database. For interchange stations (like Siam), it creates separate entries
for each line with proper naming like "Siam-Sukhumvit" and "Siam-Silom".
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# BTS Station Data
SUKHUMVIT_STATIONS = [
    # Northern Section (N24 to N1)
    ("N24", "Khu Khot", 14.1167, 100.6167),
    ("N23", "Yaek Kor Por Aor", 14.1072, 100.6139),
    ("N22", "Royal Thai Air Force Museum", 14.0986, 100.6111),
    ("N21", "Bhumibol Adulyadej Hospital", 14.0889, 100.6083),
    ("N20", "Saphan Mai", 14.0792, 100.6056),
    ("N19", "Sai Yud", 14.0694, 100.6028),
    ("N18", "Phahon Yothin 59", 14.0597, 100.6000),
    ("N17", "Wat Phra Sri Mahathat", 14.0500, 100.5972),
    ("N16", "11th Infantry Regiment", 14.0403, 100.5944),
    ("N15", "Bang Bua", 14.0306, 100.5917),
    ("N14", "Royal Forest Department", 14.0208, 100.5889),
    ("N13", "Kasetsart University", 14.0111, 100.5861),
    ("N12", "Sena Nikhom", 14.0014, 100.5833),
    ("N11", "Ratchayothin", 13.9917, 100.5806),
    ("N10", "Phahon Yothin 24", 13.9819, 100.5778),
    ("N9", "Ha Yaek Lat Phrao", 13.9722, 100.5750),
    ("N8", "Mo Chit", 13.9625, 100.5722),
    ("N7", "Saphan Khwai", 13.9528, 100.5694),
    ("N5", "Ari", 13.9431, 100.5667),
    ("N4", "Sanam Pao", 13.9333, 100.5639),
    ("N3", "Victory Monument", 13.9236, 100.5611),
    ("N2", "Phaya Thai", 13.9139, 100.5583),
    ("N1", "Ratchathewi", 13.9042, 100.5556),
    # Central (Interchange)
    ("CEN", "Siam", 13.7456, 100.5342),
    # Eastern Section (E1 to E23)
    ("E1", "Chit Lom", 13.7444, 100.5458),
    ("E2", "Phloen Chit", 13.7444, 100.5500),
    ("E3", "Nana", 13.7444, 100.5583),
    ("E4", "Asok", 13.7375, 100.5611),
    ("E5", "Phrom Phong", 13.7306, 100.5639),
    ("E6", "Thong Lo", 13.7236, 100.5667),
    ("E7", "Ekkamai", 13.7167, 100.5694),
    ("E8", "Phra Khanong", 13.7097, 100.5722),
    ("E9", "On Nut", 13.7028, 100.5750),
    ("E10", "Bang Chak", 13.6958, 100.5778),
    ("E11", "Punnawithi", 13.6889, 100.5806),
    ("E12", "Udom Suk", 13.6819, 100.5833),
    ("E13", "Bang Na", 13.6750, 100.5861),
    ("E14", "Bearing", 13.6681, 100.5889),
    ("E15", "Samrong", 13.6611, 100.5917),
    ("E16", "Pu Chao", 13.6542, 100.5944),
    ("E17", "Chang Erawan", 13.6472, 100.5972),
    ("E18", "Royal Thai Naval Academy", 13.6403, 100.6000),
    ("E19", "Pak Nam", 13.6333, 100.6028),
    ("E20", "Srinagarindra", 13.6264, 100.6056),
    ("E21", "Phraek Sa", 13.6194, 100.6083),
    ("E22", "Sai Luat", 13.6125, 100.6111),
    ("E23", "Kheha", 13.6056, 100.6139),
]

SILOM_STATIONS = [
    ("W1", "National Stadium", 13.7456, 100.5292),
    ("CEN", "Siam", 13.7456, 100.5342),  # Interchange station
    ("S1", "Ratchadamri", 13.7389, 100.5375),
    ("S2", "Sala Daeng", 13.7322, 100.5408),
    ("S3", "Chong Nonsi", 13.7256, 100.5442),
    ("S4", "Saint Louis", 13.7189, 100.5475),
    ("S5", "Surasak", 13.7122, 100.5508),
    ("S6", "Saphan Taksin", 13.7056, 100.5542),
    ("S7", "Krung Thon Buri", 13.6989, 100.5575),
    ("S8", "Wongwian Yai", 13.6922, 100.5608),
    ("S9", "Pho Nimit", 13.6856, 100.5642),
    ("S10", "Talat Phlu", 13.6789, 100.5675),
    ("S11", "Wutthakat", 13.6722, 100.5708),
    ("S12", "Bang Wa", 13.6656, 100.5742),
]

async def insert_bts_stations():
    """Insert all BTS stations into the database."""

    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("[ERROR] DATABASE_URL not found in environment variables")
        return

    asyncpg_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')

    try:
        print("Connecting to database...")
        conn = await asyncpg.connect(asyncpg_url)

        # Get Bangkok region ID
        bangkok_region = await conn.fetchrow("SELECT id FROM regions WHERE name = 'Bangkok'")
        if not bangkok_region:
            print("[ERROR] Bangkok region not found in database")
            await conn.close()
            return

        region_id = bangkok_region['id']

        # Get or create BTS company
        bts_company = await conn.fetchrow(
            "SELECT id FROM train_companies WHERE code = 'BTS'"
        )

        if not bts_company:
            print("Creating BTS company...")
            bts_company = await conn.fetchrow("""
                INSERT INTO train_companies (name, code, region_id, status, website)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """, "Bangkok Mass Transit System", "BTS", region_id, "active", "https://www.bts.co.th")

        company_id = bts_company['id']

        # Get existing Sukhumvit Line
        sukhumvit_line = await conn.fetchrow(
            "SELECT id FROM train_lines WHERE name = 'Sukhumvit Line'"
        )

        if not sukhumvit_line:
            print("Creating Sukhumvit Line...")
            sukhumvit_line = await conn.fetchrow("""
                INSERT INTO train_lines (company_id, name, color, status)
                VALUES ($1, $2, $3, $4)
                RETURNING id
            """, company_id, "Sukhumvit Line", "light-green", "active")

        sukhumvit_line_id = sukhumvit_line['id']

        # Get existing Silom Line
        silom_line = await conn.fetchrow(
            "SELECT id FROM train_lines WHERE name = 'Silom Line'"
        )

        if not silom_line:
            print("Creating Silom Line...")
            silom_line = await conn.fetchrow("""
                INSERT INTO train_lines (company_id, name, color, status)
                VALUES ($1, $2, $3, $4)
                RETURNING id
            """, company_id, "Silom Line", "dark-green", "active")

        silom_line_id = silom_line['id']

        # Clear existing stations
        print("Clearing existing BTS stations...")
        await conn.execute("""
            DELETE FROM stations
            WHERE line_id IN ($1, $2)
        """, sukhumvit_line_id, silom_line_id)

        # Insert Sukhumvit Line stations
        print(f"Inserting {len(SUKHUMVIT_STATIONS)} Sukhumvit Line stations...")
        for code, name, lat, lng in SUKHUMVIT_STATIONS:
            # For interchange stations, add line suffix
            station_name = name
            if name == "Siam":
                station_name = "Siam-Sukhumvit"

            is_interchange = name in ["Siam", "Asok", "Mo Chit"]

            await conn.execute("""
                INSERT INTO stations (line_id, name, lat, long, is_interchange, status)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, sukhumvit_line_id, station_name, lat, lng, is_interchange, "active")

            print(f"   [OK] {code}: {station_name}")

        # Insert Silom Line stations
        print(f"Inserting {len(SILOM_STATIONS)} Silom Line stations...")
        for code, name, lat, lng in SILOM_STATIONS:
            # For interchange stations, add line suffix
            station_name = name
            if name == "Siam":
                station_name = "Siam-Silom"

            is_interchange = name in ["Siam", "Sala Daeng"]

            await conn.execute("""
                INSERT INTO stations (line_id, name, lat, long, is_interchange, status)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, silom_line_id, station_name, lat, lng, is_interchange, "active")

            print(f"   [OK] {code}: {station_name}")

        # Get final count
        total_stations = await conn.fetchval("""
            SELECT COUNT(*) FROM stations
            WHERE line_id IN ($1, $2)
        """, sukhumvit_line_id, silom_line_id)

        print(f"\n[SUCCESS] Successfully inserted {total_stations} BTS stations!")
        print(f"   - Sukhumvit Line: {len(SUKHUMVIT_STATIONS)} stations")
        print(f"   - Silom Line: {len(SILOM_STATIONS)} stations")

        await conn.close()
        print("Database connection closed.")

    except Exception as e:
        print(f"[ERROR] Error: {e}")

if __name__ == "__main__":
    print("BTS Stations Insertion Tool")
    print("=" * 50)
    asyncio.run(insert_bts_stations())