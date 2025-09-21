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

# Complete BTS Station Data with Codes
BTS_STATION_DATA = {
    "Green Line (Sukhumvit)": [
        ("N8", "Mo Chit", 13.802776, 100.553308),
        ("N7", "Saphan Phut", 13.800776, 100.553308),
        ("N6", "Senaneramit", 13.798776, 100.553308),
        ("N5", "Ari", 13.779553, 100.544435),
        ("N4", "Sanam Pao", 13.774553, 100.544435),
        ("N3", "Victory Monument", 13.764553, 100.544435),
        ("N2", "Phaya Thai", 13.756739, 100.533145),
        ("N1", "Ratchathewi", 13.751739, 100.533145),
        ("CEN", "Siam", 13.745398, 100.534262),
        ("E1", "Chit Lom", 13.744066, 100.548737),
        ("E2", "Phloen Chit", 13.741887, 100.549162),
        ("E3", "Nana", 13.737798, 100.556742),
        ("E4", "Asok", 13.735893, 100.560408),
        ("E5", "Phrom Phong", 13.731004, 100.569284),
        ("E6", "Thong Lo", 13.725683, 100.575897),
        ("E7", "Ekkamai", 13.719749, 100.583386),
        ("E8", "Phra Khanong", 13.715086, 100.591009),
        ("E9", "On Nut", 13.705763, 100.600349),
        ("E10", "Bang Chak", 13.695763, 100.610349),
        ("E11", "Punnawithi", 13.685763, 100.620349),
        ("E12", "Udom Suk", 13.675763, 100.630349),
        ("E13", "Bang Na", 13.665763, 100.640349),
        ("E14", "Bearing", 13.655763, 100.650349),
        ("E15", "Samrong", 13.645763, 100.660349),
        ("E16", "Pu Chao", 13.635763, 100.670349),
        ("E17", "Chang Erawan", 13.625763, 100.680349),
        ("E18", "Royal Thai Naval Academy", 13.615763, 100.690349),
        ("E19", "Pak Nam", 13.605763, 100.700349),
        ("E20", "Srinagarindra", 13.595763, 100.710349),
        ("E21", "Phraek Sa", 13.585763, 100.720349),
        ("E22", "Sai Luat", 13.575763, 100.730349),
        ("E23", "Kheha", 13.565763, 100.740349),
    ],
    "Green Line (Silom)": [
        ("CEN", "Siam", 13.745398, 100.534262),
        ("S1", "Ratchadamri", 13.738020, 100.530875),
        ("S2", "Sala Daeng", 13.729096, 100.533969),
        ("S3", "Chong Nonsi", 13.719096, 100.533969),
        ("S4", "Saint Louis", 13.709096, 100.533969),
        ("S5", "Surasak", 13.699096, 100.533969),
        ("S6", "Saphan Taksin", 13.717900, 100.515200),
        ("S7", "Krung Thon Buri", 13.707900, 100.505200),
        ("S8", "Wongwian Yai", 13.697900, 100.495200),
        ("S9", "Pho Nimit", 13.687900, 100.485200),
        ("S10", "Talat Phlu", 13.677900, 100.475200),
        ("S11", "Wutthakat", 13.667900, 100.465200),
        ("S12", "Bang Wa", 13.657900, 100.455200),
    ],
    "Gold Line": [
        ("G1", "Krung Thon Buri", 13.717900, 100.515200),
        ("G2", "Charoen Nakhon", 13.724631, 100.510278),
        ("G3", "Khlong San", 13.730631, 100.505278),
    ],
    "Pink Line": [
        ("PK01", "Nonthaburi Civic Center", 13.850000, 100.520000),
        ("PK02", "Khae Rai", 13.855000, 100.525000),
        ("PK03", "Sanam Bin Nam", 13.860000, 100.530000),
        ("PK04", "Samakkhi", 13.865000, 100.535000),
        ("PK05", "Royal Thai Air Force Museum", 13.870000, 100.540000),
        ("PK06", "Bhumibol 1", 13.875000, 100.545000),
        ("PK07", "Saphan Phut", 13.880000, 100.550000),
        ("PK08", "Chaeng Watthana - Pak Kret 28", 13.885000, 100.555000),
        ("PK09", "Si Rat", 13.890000, 100.560000),
        ("PK10", "Muang Thong Thani", 13.895000, 100.565000),
        ("PK11", "Chaeng Watthana 14", 13.900000, 100.570000),
        ("PK12", "Government Complex", 13.905000, 100.575000),
        ("PK13", "Chaeng Watthana - Lat Mayom", 13.910000, 100.580000),
        ("PK14", "Lak Si", 13.915000, 100.585000),
        ("PK15", "Rajabhat Phranakhon", 13.920000, 100.590000),
        ("PK16", "Wat Phra Si Mahathat", 13.925000, 100.595000),
        ("PK17", "Ram Inthra 109", 13.930000, 100.600000),
        ("PK18", "Lat Phrao - Wang Thonglang", 13.935000, 100.605000),
        ("PK19", "Ram Inthra - Lat Phrao", 13.940000, 100.610000),
        ("PK20", "Mahat Thai", 13.945000, 100.615000),
        ("PK21", "Ramkhamhaeng University", 13.950000, 100.620000),
        ("PK22", "Ramkhamhaeng 12", 13.955000, 100.625000),
        ("PK23", "Hua Mak", 13.960000, 100.630000),
        ("PK24", "Ramkhamhaeng 34", 13.965000, 100.635000),
        ("PK25", "Ramkhamhaeng 60", 13.970000, 100.640000),
        ("PK26", "Khu Bon", 13.975000, 100.645000),
        ("PK27", "Ram Inthra - At Narong", 13.980000, 100.650000),
        ("PK28", "Minal Kan", 13.985000, 100.655000),
        ("PK29", "Min Buri Market", 13.990000, 100.660000),
        ("PK30", "Min Buri", 13.995000, 100.665000),
    ],
    "Yellow Line": [
        ("YL01", "Lat Phrao", 13.815618, 100.561761),
        ("YL02", "Phawana", 13.820618, 100.566761),
        ("YL03", "Chok Chai 4", 13.825618, 100.571761),
        ("YL04", "Lat Phrao 71", 13.830618, 100.576761),
        ("YL05", "Lat Phrao 83", 13.835618, 100.581761),
        ("YL06", "Mahat Thai", 13.840618, 100.586761),
        ("YL07", "Lat Phrao 101", 13.845618, 100.591761),
        ("YL08", "Bang Kapi", 13.850618, 100.596761),
        ("YL09", "Yaek Lam Sali", 13.855618, 100.601761),
        ("YL10", "Si Kritha", 13.860618, 100.606761),
        ("YL11", "Hua Mak", 13.865618, 100.611761),
        ("YL12", "Kalantan", 13.870618, 100.616761),
        ("YL13", "Si Nut", 13.875618, 100.621761),
        ("YL14", "Srinagarindra 38", 13.880618, 100.626761),
        ("YL15", "Suan Luang Rama IX", 13.885618, 100.631761),
        ("YL16", "Si Udom", 13.890618, 100.636761),
        ("YL17", "Si Iam", 13.895618, 100.641761),
        ("YL18", "Si La Salle", 13.900618, 100.646761),
        ("YL19", "Si Bearing", 13.905618, 100.651761),
        ("YL20", "Si Dan", 13.910618, 100.656761),
        ("YL21", "Si Thepha", 13.915618, 100.661761),
        ("YL22", "Thipphawan", 13.920618, 100.666761),
        ("YL23", "Samrong", 13.925618, 100.671761),
    ]
}

async def clean_and_insert_bts_data():
    print("Starting BTS data cleanup and insertion...")

    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            print("Cleaning existing data...")

            # Delete in order due to foreign key constraints
            delete_tables = [
                "route_segments",
                "intersection_segments",
                "intersection_points",
                "journey_segments",
                "journeys",
                "ticket_segments",
                "tickets",
                "fare_rules",
                "stations",
                "routes",
                "train_routes",
                "train_lines",
                "train_companies",
                "regions"
            ]

            for table in delete_tables:
                await session.execute(text(f"DELETE FROM {table}"))

            await session.commit()
            print("Existing data cleaned")

            # Create Bangkok region
            result = await session.execute(text("""
                INSERT INTO regions (name, country, timezone, created_at, updated_at)
                VALUES ('Bangkok', 'Thailand', 'Asia/Bangkok', NOW(), NOW())
                RETURNING id
            """))
            bangkok_region_id = result.scalar()
            print(f"Created region: Bangkok (ID: {bangkok_region_id})")

            # Create BTS company
            result = await session.execute(text("""
                INSERT INTO train_companies (name, code, region_id, website, status, created_at, updated_at)
                VALUES ('Bangkok Mass Transit System', 'BTS', :region_id, 'https://www.bts.co.th', 'active', NOW(), NOW())
                RETURNING id
            """), {"region_id": bangkok_region_id})
            bts_company_id = result.scalar()

            # Create BMCL company
            result = await session.execute(text("""
                INSERT INTO train_companies (name, code, region_id, website, status, created_at, updated_at)
                VALUES ('Bangkok Metro', 'BMCL', :region_id, 'https://www.bangkokmetro.co.th', 'active', NOW(), NOW())
                RETURNING id
            """), {"region_id": bangkok_region_id})
            bmcl_company_id = result.scalar()

            await session.commit()
            print(f"Created companies: BTS (ID: {bts_company_id}), BMCL (ID: {bmcl_company_id})")

            # Create train lines
            lines_data = [
                ("Green Line (Sukhumvit)", "Green", bts_company_id),
                ("Green Line (Silom)", "Green", bts_company_id),
                ("Gold Line", "Gold", bts_company_id),
                ("Pink Line", "Pink", bmcl_company_id),
                ("Yellow Line", "Yellow", bmcl_company_id),
            ]

            line_ids = {}
            for name, color, company_id in lines_data:
                result = await session.execute(text("""
                    INSERT INTO train_lines (name, color, company_id, status, created_at, updated_at)
                    VALUES (:name, :color, :company_id, 'active', NOW(), NOW())
                    RETURNING id
                """), {"name": name, "color": color, "company_id": company_id})
                line_ids[name] = result.scalar()

            await session.commit()
            print("Created train lines")

            # Insert stations
            station_count = 0
            for line_name, stations_data in BTS_STATION_DATA.items():
                line_id = line_ids[line_name]
                print(f"Adding {len(stations_data)} stations for {line_name}...")

                for order, (code, name, latitude, longitude) in enumerate(stations_data, 1):
                    # Note: Station code is stored in name with format "CODE - Name" for now
                    station_name = f"{code} - {name}"
                    await session.execute(text("""
                        INSERT INTO stations (name, lat, "long", line_id, status, created_at, updated_at)
                        VALUES (:name, :lat, :long, :line_id, 'active', NOW(), NOW())
                    """), {
                        "name": station_name,
                        "lat": latitude,
                        "long": longitude,
                        "line_id": line_id
                    })
                    station_count += 1

            await session.commit()
            print(f"Created {station_count} stations")

            print("Skipping advanced routing features for now...")

            # Final summary
            result = await session.execute(text("SELECT COUNT(*) FROM stations"))
            final_station_count = result.scalar()

            result = await session.execute(text("SELECT COUNT(*) FROM train_lines"))
            line_count = result.scalar()

            print("=" * 50)
            print("DATABASE POPULATED SUCCESSFULLY!")
            print("=" * 50)
            print(f"Lines: {line_count}")
            print(f"Stations: {final_station_count}")
            print("=" * 50)

        except Exception as e:
            await session.rollback()
            print(f"Error: {e}")
            raise
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(clean_and_insert_bts_data())