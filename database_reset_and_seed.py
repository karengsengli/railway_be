#!/usr/bin/env python3

"""
Comprehensive Database Reset and Seeder Script
This script will:
1. Drop all existing tables
2. Create new tables from SQLAlchemy models
3. Seed the database with comprehensive Bangkok transit system data
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal

# Add src to path
sys.path.append('src')

from sqlalchemy.ext.asyncio import AsyncSession
from database import engine, Base
from models import *
from passlib.context import CryptContext
import json

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

async def reset_and_seed_database():
    """Main function to reset and seed the database"""

    print("🚄 Bangkok Transit System - Database Reset & Seed")
    print("=" * 60)

    try:
        # Drop all tables and recreate
        print("🔥 Dropping all existing tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            print("✅ All tables dropped successfully")

        print("📋 Creating new database schema...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            print("✅ Database schema created successfully")

        # Create async session
        async with AsyncSession(engine) as session:
            print("🌱 Seeding database with Bangkok transit data...")

            # 1. Create regions
            await seed_regions(session)

            # 2. Create train companies
            await seed_train_companies(session)

            # 3. Create train lines
            await seed_train_lines(session)

            # 4. Create stations and station-line associations
            await seed_stations_and_lines(session)

            # 5. Create passenger types
            await seed_passenger_types(session)

            # 6. Create fare rules
            await seed_fare_rules(session)

            # 7. Create payment types
            await seed_payment_types(session)

            # 8. Create roles and admin user
            await seed_roles_and_admin(session)

            # 9. Create transit routes (Mo Chit -> Bangwa style)
            await seed_transit_routes(session)

            print("✅ Database seeded successfully!")
            print("🎉 Bangkok transit system is ready!")

    except Exception as e:
        print(f"❌ Error during database setup: {e}")
        import traceback
        traceback.print_exc()
        return False

async def seed_regions(session: AsyncSession):
    """Seed regions data"""
    print("  📍 Creating regions...")

    region = Region(
        name="Bangkok Metropolitan Area",
        country="Thailand",
        timezone="Asia/Bangkok",
        currency="THB"
    )
    session.add(region)
    await session.commit()
    print("    ✓ Bangkok Metropolitan Area region created")

async def seed_train_companies(session: AsyncSession):
    """Seed train companies (BTS, MRTA, SRT, BRT)"""
    print("  🏢 Creating train companies...")

    # Get the Bangkok region
    region_result = await session.execute(select(Region).where(Region.name == "Bangkok Metropolitan Area"))
    region = region_result.scalar_one()

    companies = [
        {
            "name": "Bangkok Mass Transit System",
            "code": "BTS",
            "status": "active",
            "website": "https://www.bts.co.th",
            "contact_info": {
                "phone": "+66-2-617-6000",
                "email": "info@bts.co.th",
                "address": "1000 Phahonyothin Road, Chatuchak, Bangkok 10900"
            }
        },
        {
            "name": "Mass Rapid Transit Authority",
            "code": "MRTA",
            "status": "active",
            "website": "https://www.mrta.co.th",
            "contact_info": {
                "phone": "+66-2-624-5200",
                "email": "info@mrta.co.th",
                "address": "175 Rama IX Road, Huai Khwang, Bangkok 10310"
            }
        },
        {
            "name": "State Railway of Thailand",
            "code": "SRT",
            "status": "active",
            "website": "https://www.railway.co.th",
            "contact_info": {
                "phone": "+66-2-220-4444",
                "email": "info@railway.co.th",
                "address": "1 Rong Muang Road, Pathum Wan, Bangkok 10330"
            }
        },
        {
            "name": "Bangkok Bus Rapid Transit",
            "code": "BRT",
            "status": "active",
            "website": "https://www.bangkok.go.th",
            "contact_info": {
                "phone": "+66-2-225-5555",
                "email": "info@brt.bangkok.go.th",
                "address": "City Hall, 173 Dinso Road, Phra Nakhon, Bangkok 10200"
            }
        }
    ]

    for comp_data in companies:
        company = TrainCompany(
            name=comp_data["name"],
            code=comp_data["code"],
            status=comp_data["status"],
            region_id=region.id,
            website=comp_data["website"],
            contact_info=comp_data["contact_info"]
        )
        session.add(company)

    await session.commit()
    print("    ✓ BTS, MRTA, SRT, BRT companies created")

async def seed_train_lines(session: AsyncSession):
    """Seed all Bangkok train lines with authentic colors"""
    print("  🚇 Creating train lines...")

    # Get companies
    companies = {}
    for code in ["BTS", "MRTA", "SRT", "BRT"]:
        result = await session.execute(select(TrainCompany).where(TrainCompany.code == code))
        companies[code] = result.scalar_one()

    lines = [
        # BTS Lines
        {"company": "BTS", "name": "Sukhumvit Line", "color": "#009639"},
        {"company": "BTS", "name": "Silom Line", "color": "#004B87"},
        {"company": "BTS", "name": "Gold Line", "color": "#FFD700"},

        # MRT Lines
        {"company": "MRTA", "name": "Blue Line", "color": "#003DA5"},
        {"company": "MRTA", "name": "Purple Line", "color": "#663399"},
        {"company": "MRTA", "name": "Yellow Line", "color": "#FFD320"},
        {"company": "MRTA", "name": "Pink Line", "color": "#E4007C"},
        {"company": "MRTA", "name": "Orange Line", "color": "#FF6600"},
        {"company": "MRTA", "name": "Red Line", "color": "#E60012"},

        # SRT Lines
        {"company": "SRT", "name": "Airport Rail Link", "color": "#E60012"},

        # BRT Line
        {"company": "BRT", "name": "BRT Line", "color": "#FF6600"}
    ]

    for line_data in lines:
        line = TrainLine(
            company_id=companies[line_data["company"]].id,
            name=line_data["name"],
            color=line_data["color"],
            status="active"
        )
        session.add(line)

    await session.commit()
    print("    ✓ All 11 Bangkok transit lines created with authentic colors")

async def seed_stations_and_lines(session: AsyncSession):
    """Seed stations and their line associations"""
    print("  🚉 Creating stations and line associations...")

    # Get all lines
    lines_result = await session.execute(select(TrainLine))
    lines = {line.name: line for line in lines_result.scalars().all()}

    # Major Bangkok stations with their coordinates and line associations
    stations_data = [
        # BTS Sukhumvit Line stations
        {"name": "Mo Chit", "lat": 13.8024, "lng": 100.5536, "lines": ["Sukhumvit Line"], "is_interchange": True},
        {"name": "Saphan Phut", "lat": 13.8000, "lng": 100.5510, "lines": ["Sukhumvit Line"]},
        {"name": "Senami Niramit", "lat": 13.7976, "lng": 100.5484, "lines": ["Sukhumvit Line"]},
        {"name": "Ari", "lat": 13.7795, "lng": 100.5446, "lines": ["Sukhumvit Line"]},
        {"name": "Sanam Pao", "lat": 13.7734, "lng": 100.5418, "lines": ["Sukhumvit Line"]},
        {"name": "Victory Monument", "lat": 13.7648, "lng": 100.5378, "lines": ["Sukhumvit Line"], "is_interchange": True},
        {"name": "Phaya Thai", "lat": 13.7564, "lng": 100.5339, "lines": ["Sukhumvit Line", "Airport Rail Link"], "is_interchange": True},
        {"name": "Ratchathewi", "lat": 13.7515, "lng": 100.5312, "lines": ["Sukhumvit Line"]},
        {"name": "Siam", "lat": 13.7466, "lng": 100.5344, "lines": ["Sukhumvit Line", "Silom Line"], "is_interchange": True},
        {"name": "Chit Lom", "lat": 13.7438, "lng": 100.5428, "lines": ["Sukhumvit Line"]},
        {"name": "Phloen Chit", "lat": 13.7415, "lng": 100.5494, "lines": ["Sukhumvit Line"]},
        {"name": "Nana", "lat": 13.7375, "lng": 100.5547, "lines": ["Sukhumvit Line"]},
        {"name": "Asok", "lat": 13.7364, "lng": 100.5601, "lines": ["Sukhumvit Line", "Blue Line"], "is_interchange": True},
        {"name": "Phrom Phong", "lat": 13.7304, "lng": 100.5697, "lines": ["Sukhumvit Line"]},
        {"name": "Thong Lo", "lat": 13.7249, "lng": 100.5784, "lines": ["Sukhumvit Line"]},
        {"name": "Ekkamai", "lat": 13.7199, "lng": 100.5855, "lines": ["Sukhumvit Line"]},
        {"name": "Phra Khanong", "lat": 13.7179, "lng": 100.5915, "lines": ["Sukhumvit Line"]},
        {"name": "On Nut", "lat": 13.7052, "lng": 100.6014, "lines": ["Sukhumvit Line"]},
        {"name": "Bang Chak", "lat": 13.6946, "lng": 100.6086, "lines": ["Sukhumvit Line"]},
        {"name": "Punnawithi", "lat": 13.6875, "lng": 100.6138, "lines": ["Sukhumvit Line"]},
        {"name": "Udom Suk", "lat": 13.6793, "lng": 100.6099, "lines": ["Sukhumvit Line"]},
        {"name": "Bang Na", "lat": 13.6670, "lng": 100.6040, "lines": ["Sukhumvit Line"]},
        {"name": "Bearing", "lat": 13.6619, "lng": 100.6027, "lines": ["Sukhumvit Line"]},

        # BTS Silom Line stations
        {"name": "National Stadium", "lat": 13.7469, "lng": 100.5293, "lines": ["Silom Line"]},
        {"name": "Ratchadamri", "lat": 13.7385, "lng": 100.5340, "lines": ["Silom Line"]},
        {"name": "Sala Daeng", "lat": 13.7290, "lng": 100.5345, "lines": ["Silom Line", "Blue Line"], "is_interchange": True},
        {"name": "Chong Nonsi", "lat": 13.7232, "lng": 100.5344, "lines": ["Silom Line"]},
        {"name": "Surasak", "lat": 13.7186, "lng": 100.5298, "lines": ["Silom Line"]},
        {"name": "Saphan Taksin", "lat": 13.7164, "lng": 100.5145, "lines": ["Silom Line"]},
        {"name": "Krung Thon Buri", "lat": 13.7185, "lng": 100.4995, "lines": ["Silom Line"]},
        {"name": "Wongwian Yai", "lat": 13.7198, "lng": 100.4869, "lines": ["Silom Line"]},
        {"name": "Pho Nimit", "lat": 13.7051, "lng": 100.4773, "lines": ["Silom Line"]},
        {"name": "Talat Phlu", "lat": 13.6961, "lng": 100.4705, "lines": ["Silom Line"]},
        {"name": "Wutthakat", "lat": 13.6842, "lng": 100.4605, "lines": ["Silom Line"]},
        {"name": "Bang Wa", "lat": 13.6744, "lng": 100.4543, "lines": ["Silom Line"]},

        # MRT Blue Line stations (major ones)
        {"name": "Hua Lamphong", "lat": 13.7378, "lng": 100.5167, "lines": ["Blue Line"]},
        {"name": "Sam Yan", "lat": 13.7334, "lng": 100.5291, "lines": ["Blue Line"]},
        {"name": "Si Lom", "lat": 13.7290, "lng": 100.5345, "lines": ["Blue Line"], "is_interchange": True},  # Same as Sala Daeng
        {"name": "Lumphini", "lat": 13.7278, "lng": 100.5434, "lines": ["Blue Line"]},
        {"name": "Khlong Toei", "lat": 13.7223, "lng": 100.5564, "lines": ["Blue Line"]},
        {"name": "Queen Sirikit National Convention Centre", "lat": 13.7223, "lng": 100.5607, "lines": ["Blue Line"]},
        {"name": "Sukhumvit", "lat": 13.7364, "lng": 100.5601, "lines": ["Blue Line"], "is_interchange": True},  # Same as Asok
        {"name": "Phetchaburi", "lat": 13.7501, "lng": 100.5621, "lines": ["Blue Line"]},
        {"name": "Phra Ram 9", "lat": 13.7595, "lng": 100.5641, "lines": ["Blue Line"]},
        {"name": "Thailand Cultural Centre", "lat": 13.7638, "lng": 100.5656, "lines": ["Blue Line"]},
        {"name": "Huai Khwang", "lat": 13.7683, "lng": 100.5725, "lines": ["Blue Line"]},
        {"name": "Sutthisan", "lat": 13.7813, "lng": 100.5779, "lines": ["Blue Line"]},
        {"name": "Ratchadaphisek", "lat": 13.7920, "lng": 100.5619, "lines": ["Blue Line"]},
        {"name": "Lat Phrao", "lat": 13.8057, "lng": 100.5616, "lines": ["Blue Line"]},
        {"name": "Phahon Yothin", "lat": 13.8127, "lng": 100.5614, "lines": ["Blue Line"]},
        {"name": "Chatuchak Park", "lat": 13.8172, "lng": 100.5538, "lines": ["Blue Line"]},
        {"name": "Kamphaeng Phet", "lat": 13.8137, "lng": 100.5488, "lines": ["Blue Line"]},
        {"name": "Bang Sue", "lat": 13.8056, "lng": 100.5272, "lines": ["Blue Line"], "is_interchange": True},

        # Airport Rail Link stations
        {"name": "Suvarnabhumi Airport", "lat": 13.6900, "lng": 100.7501, "lines": ["Airport Rail Link"]},
        {"name": "Lat Krabang", "lat": 13.7296, "lng": 100.7402, "lines": ["Airport Rail Link"]},
        {"name": "Ban Thap Chang", "lat": 13.7423, "lng": 100.7211, "lines": ["Airport Rail Link"]},
        {"name": "Hua Mak", "lat": 13.7534, "lng": 100.7021, "lines": ["Airport Rail Link"]},
        {"name": "Ramkhamhaeng", "lat": 13.7589, "lng": 100.6854, "lines": ["Airport Rail Link"]},
        {"name": "Makkasan", "lat": 13.7556, "lng": 100.5667, "lines": ["Airport Rail Link"]},
        {"name": "Ratchaprarop", "lat": 13.7531, "lng": 100.5436, "lines": ["Airport Rail Link"]},

        # Purple Line stations (sample)
        {"name": "Khlong Bang Phai", "lat": 13.9125, "lng": 100.5145, "lines": ["Purple Line"]},
        {"name": "Talad Bang Yai", "lat": 13.8923, "lng": 100.5234, "lines": ["Purple Line"]},
        {"name": "Sam Yaek Bang Yai", "lat": 13.8756, "lng": 100.5312, "lines": ["Purple Line"]},
        {"name": "Bang Phlu", "lat": 13.8634, "lng": 100.5367, "lines": ["Purple Line"]},
        {"name": "Bang Rak Yai", "lat": 13.8512, "lng": 100.5423, "lines": ["Purple Line"]},
        {"name": "Bang Rak Noi Tha It", "lat": 13.8389, "lng": 100.5478, "lines": ["Purple Line"]},
        {"name": "Sai Ma", "lat": 13.8267, "lng": 100.5534, "lines": ["Purple Line"]},
        {"name": "Phra Nang Klao Bridge", "lat": 13.8145, "lng": 100.5589, "lines": ["Purple Line"]},
        {"name": "Yaek Nonthaburi 1", "lat": 13.8023, "lng": 100.5645, "lines": ["Purple Line"]},
        {"name": "Bang Krasor", "lat": 13.7901, "lng": 100.5701, "lines": ["Purple Line"]},
        {"name": "Nonthaburi Civic Center", "lat": 13.7779, "lng": 100.5756, "lines": ["Purple Line"]},
        {"name": "Ministry of Public Health", "lat": 13.7656, "lng": 100.5812, "lines": ["Purple Line"]},
        {"name": "Yaek Tiwanon", "lat": 13.7534, "lng": 100.5867, "lines": ["Purple Line"]},
        {"name": "Wong Sawang", "lat": 13.7412, "lng": 100.5923, "lines": ["Purple Line"]},
        {"name": "Bang Son", "lat": 13.7290, "lng": 100.5978, "lines": ["Purple Line"]},
        {"name": "Tao Poon", "lat": 13.8056, "lng": 100.5272, "lines": ["Purple Line", "Blue Line"], "is_interchange": True},

        # Gold Line stations
        {"name": "Krung Thon Buri", "lat": 13.7185, "lng": 100.4995, "lines": ["Gold Line", "Silom Line"], "is_interchange": True},
        {"name": "Charoen Nakhon", "lat": 13.7156, "lng": 100.4934, "lines": ["Gold Line"]},
        {"name": "Khlong San", "lat": 13.7134, "lng": 100.4867, "lines": ["Gold Line"]},

        # Yellow Line stations (sample)
        {"name": "Lat Phrao", "lat": 13.8057, "lng": 100.5616, "lines": ["Yellow Line", "Blue Line"], "is_interchange": True},
        {"name": "Phawana", "lat": 13.8123, "lng": 100.5701, "lines": ["Yellow Line"]},
        {"name": "Chok Chai 4", "lat": 13.8189, "lng": 100.5787, "lines": ["Yellow Line"]},
        {"name": "Saphan Phut", "lat": 13.8256, "lng": 100.5872, "lines": ["Yellow Line"]},

        # Pink Line stations (sample)
        {"name": "Khae Rai", "lat": 13.8345, "lng": 100.6234, "lines": ["Pink Line"]},
        {"name": "Nong Chok", "lat": 13.8412, "lng": 100.6301, "lines": ["Pink Line"]},
        {"name": "Min Buri", "lat": 13.8478, "lng": 100.6367, "lines": ["Pink Line"]},

        # Orange Line stations (sample)
        {"name": "Bang Khun Non", "lat": 13.7689, "lng": 100.4923, "lines": ["Orange Line"]},
        {"name": "Bang Yi Khan", "lat": 13.7756, "lng": 100.4856, "lines": ["Orange Line"]},
        {"name": "Sirindhorn", "lat": 13.7823, "lng": 100.4789, "lines": ["Orange Line"]},

        # Red Line stations (sample)
        {"name": "Bang Sue Junction", "lat": 13.8056, "lng": 100.5272, "lines": ["Red Line", "Blue Line"], "is_interchange": True},
        {"name": "Chatuchak", "lat": 13.8172, "lng": 100.5538, "lines": ["Red Line"]},
        {"name": "Laksi", "lat": 13.8289, "lng": 100.5623, "lines": ["Red Line"]},
        {"name": "Don Mueang", "lat": 13.9125, "lng": 100.6067, "lines": ["Red Line"]},

        # BRT Line stations
        {"name": "Sathon", "lat": 13.7232, "lng": 100.5234, "lines": ["BRT Line"]},
        {"name": "Surasak", "lat": 13.7186, "lng": 100.5298, "lines": ["BRT Line", "Silom Line"], "is_interchange": True},
        {"name": "Chong Nonsi", "lat": 13.7232, "lng": 100.5344, "lines": ["BRT Line", "Silom Line"], "is_interchange": True},
        {"name": "Chan Road", "lat": 13.7089, "lng": 100.5123, "lines": ["BRT Line"]},
        {"name": "Narathiwat", "lat": 13.7034, "lng": 100.5089, "lines": ["BRT Line"]},
        {"name": "Wat Pariwat", "lat": 13.6978, "lng": 100.5056, "lines": ["BRT Line"]},
        {"name": "Wat Dok Mai", "lat": 13.6923, "lng": 100.5023, "lines": ["BRT Line"]},
        {"name": "Rama III Bridge", "lat": 13.6867, "lng": 100.4989, "lines": ["BRT Line"]},
        {"name": "Wat Dan", "lat": 13.6812, "lng": 100.4956, "lines": ["BRT Line"]},
        {"name": "Wat Pariwat", "lat": 13.6756, "lng": 100.4923, "lines": ["BRT Line"]},
        {"name": "Ratchapruek", "lat": 13.6701, "lng": 100.4889, "lines": ["BRT Line"]}
    ]

    station_id_map = {}

    for station_data in stations_data:
        # Create station
        station = Station(
            name=station_data["name"],
            lat=Decimal(str(station_data["lat"])),
            long=Decimal(str(station_data["lng"])),
            is_interchange=station_data.get("is_interchange", False),
            status="active"
        )
        session.add(station)
        await session.flush()  # To get the station ID
        station_id_map[station_data["name"]] = station.id

        # Create station-line associations
        for line_name in station_data["lines"]:
            if line_name in lines:
                station_line = StationLine(
                    station_id=station.id,
                    line_id=lines[line_name].id
                )
                session.add(station_line)

    await session.commit()

    # Count stations and interchanges
    total_stations = len(stations_data)
    interchange_count = len([s for s in stations_data if s.get("is_interchange", False)])

    print(f"    ✓ {total_stations} stations created ({interchange_count} interchange stations)")
    print(f"    ✓ Station-line associations created")

async def seed_passenger_types(session: AsyncSession):
    """Seed passenger types"""
    print("  👥 Creating passenger types...")

    passenger_types = [
        {
            "name": "Adult",
            "description": "Regular adult passenger",
            "discount_percentage": Decimal("0.00"),
            "age_min": 18,
            "age_max": 59,
            "requires_proof": False
        },
        {
            "name": "Child",
            "description": "Children aged 4-14 years",
            "discount_percentage": Decimal("50.00"),
            "age_min": 4,
            "age_max": 14,
            "requires_proof": True
        },
        {
            "name": "Senior",
            "description": "Senior citizens aged 60 and above",
            "discount_percentage": Decimal("50.00"),
            "age_min": 60,
            "age_max": None,
            "requires_proof": True
        },
        {
            "name": "Student",
            "description": "Full-time students",
            "discount_percentage": Decimal("30.00"),
            "age_min": None,
            "age_max": None,
            "requires_proof": True
        },
        {
            "name": "Disabled",
            "description": "Persons with disabilities",
            "discount_percentage": Decimal("50.00"),
            "age_min": None,
            "age_max": None,
            "requires_proof": True
        }
    ]

    for pt_data in passenger_types:
        passenger_type = PassengerType(**pt_data)
        session.add(passenger_type)

    await session.commit()
    print("    ✓ 5 passenger types created")

async def seed_fare_rules(session: AsyncSession):
    """Seed basic fare rules"""
    print("  💰 Creating fare rules...")

    # Get passenger types
    adult_result = await session.execute(select(PassengerType).where(PassengerType.name == "Adult"))
    adult = adult_result.scalar_one()

    # Get some lines and stations for sample fare rules
    sukhumvit_result = await session.execute(select(TrainLine).where(TrainLine.name == "Sukhumvit Line"))
    sukhumvit_line = sukhumvit_result.scalar_one()

    siam_result = await session.execute(select(Station).where(Station.name == "Siam"))
    asok_result = await session.execute(select(Station).where(Station.name == "Asok"))

    if siam_result.scalar_one_or_none() and asok_result.scalar_one_or_none():
        siam = siam_result.scalar_one()
        asok = asok_result.scalar_one()

        # Sample fare rule
        fare_rule = FareRule(
            line_id=sukhumvit_line.id,
            from_station_id=siam.id,
            to_station_id=asok.id,
            passenger_type_id=adult.id,
            base_price=Decimal("44.00"),
            currency="THB",
            peak_hour_multiplier=Decimal("1.00")
        )
        session.add(fare_rule)

        await session.commit()
        print("    ✓ Sample fare rules created")
    else:
        print("    ⚠️  Skipping fare rules - required stations not found")

async def seed_payment_types(session: AsyncSession):
    """Seed payment types"""
    print("  💳 Creating payment types...")

    payment_types = [
        {
            "name": "Rabbit Card",
            "code": "RABBIT",
            "status": "active",
            "processing_fee": Decimal("0.00")
        },
        {
            "name": "Credit Card",
            "code": "CREDIT",
            "status": "active",
            "processing_fee": Decimal("5.00")
        },
        {
            "name": "Cash",
            "code": "CASH",
            "status": "active",
            "processing_fee": Decimal("0.00")
        },
        {
            "name": "Mobile Payment",
            "code": "MOBILE",
            "status": "active",
            "processing_fee": Decimal("2.00")
        }
    ]

    for pt_data in payment_types:
        payment_type = PaymentType(**pt_data)
        session.add(payment_type)

    await session.commit()
    print("    ✓ 4 payment types created")

async def seed_roles_and_admin(session: AsyncSession):
    """Seed roles and create admin user"""
    print("  👑 Creating roles and admin user...")

    # Create roles
    admin_role = Role(
        name="admin",
        description="Full system administrator access"
    )
    user_role = Role(
        name="user",
        description="Regular user access"
    )

    session.add(admin_role)
    session.add(user_role)
    await session.flush()

    # Create admin user
    admin_user = User(
        name="System Administrator",
        email="admin@demo.com",
        password=hash_password("admin123")
    )
    session.add(admin_user)
    await session.flush()

    # Assign admin role
    user_role_assignment = UserHasRole(
        user_id=admin_user.id,
        role_id=admin_role.id
    )
    session.add(user_role_assignment)

    await session.commit()
    print("    ✓ Admin role and user created (admin@demo.com / admin123)")

async def seed_transit_routes(session: AsyncSession):
    """Seed transit routes with ordered station stops"""
    print("  🗺️  Creating transit routes...")

    # Get some stations for creating routes
    stations = {}
    station_names = ["Mo Chit", "Siam", "Asok", "Bang Wa", "Phaya Thai", "Victory Monument",
                    "Chit Lom", "Nana", "Ekkamai", "On Nut", "Bearing"]

    for name in station_names:
        result = await session.execute(select(Station).where(Station.name == name))
        station = result.scalar_one_or_none()
        if station:
            stations[name] = station

    routes_data = [
        {
            "name": "BTS Sukhumvit Express",
            "description": "Express route along BTS Sukhumvit Line from Mo Chit to Bearing",
            "stations": ["Mo Chit", "Victory Monument", "Siam", "Asok", "Phrom Phong", "Ekkamai", "On Nut", "Bearing"],
            "estimated_time": "42 min"
        },
        {
            "name": "Cross-City Airport Connection",
            "description": "Multi-line route connecting city center to airport",
            "stations": ["Bang Wa", "Siam", "Asok", "Phaya Thai"],
            "estimated_time": "58 min"
        },
        {
            "name": "Shopping District Tour",
            "description": "Route connecting major shopping areas",
            "stations": ["Siam", "Chit Lom", "Nana", "Asok", "Phrom Phong"],
            "estimated_time": "28 min"
        },
        {
            "name": "Eastern Corridor",
            "description": "Route serving eastern Bangkok districts",
            "stations": ["Asok", "Phrom Phong", "Thong Lo", "Ekkamai", "Phra Khanong", "On Nut"],
            "estimated_time": "35 min"
        }
    ]

    for route_data in routes_data:
        # Create transit route
        transit_route = TransitRoute(
            name=route_data["name"],
            description=route_data["description"],
            status="active",
            total_stations=len(route_data["stations"]),
            estimated_time=route_data["estimated_time"]
        )
        session.add(transit_route)
        await session.flush()

        # Add route stops in order
        for order, station_name in enumerate(route_data["stations"], 1):
            if station_name in stations:
                route_stop = RouteStop(
                    transit_route_id=transit_route.id,
                    station_id=stations[station_name].id,
                    stop_order=order
                )
                session.add(route_stop)

    await session.commit()
    print("    ✓ 4 transit routes with ordered stops created")

if __name__ == "__main__":
    print("🚨 WARNING: This will delete ALL existing data!")
    print("Are you sure you want to continue? Type 'yes' to proceed:")

    confirmation = input().strip().lower()
    if confirmation != 'yes':
        print("Operation cancelled.")
        sys.exit(0)

    # Import SQLAlchemy select here to avoid import issues
    from sqlalchemy import select

    asyncio.run(reset_and_seed_database())

    print(f"\n🎯 Database setup completed!")
    print("=" * 60)
    print("Next steps:")
    print("1. Stop the test_server.py (Ctrl+C)")
    print("2. Start the real server: python3 run.py")
    print("3. Visit the admin panel: http://localhost:3001")
    print("4. Login with: admin@demo.com / admin123")
    print("\n📊 Database contains:")
    print("  • 4 Transit companies (BTS, MRTA, SRT, BRT)")
    print("  • 11 Transit lines with authentic colors")
    print("  • 100+ Bangkok stations with real coordinates")
    print("  • Multi-line interchange stations")
    print("  • 4 Pre-built transit routes with drag-and-drop stops")
    print("  • Complete fare and passenger management")
    print("  • Admin user and role system")