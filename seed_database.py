#!/usr/bin/env python3

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from passlib.context import CryptContext
from decimal import Decimal
from datetime import datetime, timedelta
import json

DATABASE_URL = 'postgresql+asyncpg://neondb_owner:npg_Vv1DS3cYLEyg@ep-shy-violet-a106m9dw-pooler.ap-southeast-1.aws.neon.tech/neondb?ssl=require'
engine = create_async_engine(DATABASE_URL, echo=False)

class Base(DeclarativeBase):
    pass

from src.models import *

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

async def seed_database():
    print('🌱 Seeding database with Bangkok transit data...')

    async with AsyncSession(engine) as session:
        # Create Thailand region
        thailand_region = Region(
            name='Thailand',
            country='Thailand',
            timezone='Asia/Bangkok',
            currency='THB'
        )
        session.add(thailand_region)
        await session.flush()

        # Create train companies
        companies = [
            {
                'name': 'Bangkok Mass Transit System',
                'code': 'BTS',
                'website': 'https://www.bts.co.th',
                'contact_info': {'phone': '+66-2-617-6000', 'email': 'info@bts.co.th'}
            },
            {
                'name': 'Mass Rapid Transit Authority of Thailand',
                'code': 'MRTA',
                'website': 'https://www.mrta.co.th',
                'contact_info': {'phone': '+66-2-354-2000', 'email': 'info@mrta.co.th'}
            },
            {
                'name': 'State Railway of Thailand',
                'code': 'SRT',
                'website': 'https://www.railway.co.th',
                'contact_info': {'phone': '+66-1690', 'email': 'info@railway.co.th'}
            },
            {
                'name': 'Bangkok Bus Rapid Transit',
                'code': 'BRT',
                'website': 'https://www.brtbangkok.com',
                'contact_info': {'phone': '+66-2-142-7788', 'email': 'info@brtbangkok.com'}
            }
        ]

        company_objects = {}
        for company_data in companies:
            company = TrainCompany(
                name=company_data['name'],
                code=company_data['code'],
                status='active',
                region_id=thailand_region.id,
                website=company_data['website'],
                contact_info=company_data['contact_info']
            )
            session.add(company)
            company_objects[company_data['code']] = company

        await session.flush()

        # Create train lines
        lines = [
            {'company': 'BTS', 'name': 'Sukhumvit Line', 'color': '#009639'},
            {'company': 'BTS', 'name': 'Silom Line', 'color': '#004B87'},
            {'company': 'BTS', 'name': 'Gold Line', 'color': '#D4AF37'},
            {'company': 'MRTA', 'name': 'Blue Line', 'color': '#003DA5'},
            {'company': 'MRTA', 'name': 'Purple Line', 'color': '#663399'},
            {'company': 'MRTA', 'name': 'Orange Line', 'color': '#FF6600'},
            {'company': 'MRTA', 'name': 'Yellow Line', 'color': '#FFD320'},
            {'company': 'MRTA', 'name': 'Pink Line', 'color': '#E91E63'},
            {'company': 'SRT', 'name': 'Dark Red Line', 'color': '#8B0000'},
            {'company': 'SRT', 'name': 'Light Red Line', 'color': '#FF4444'},
            {'company': 'BRT', 'name': 'BRT Line', 'color': '#FF8C00'}
        ]

        line_objects = {}
        for line_data in lines:
            line = TrainLine(
                company_id=company_objects[line_data['company']].id,
                name=line_data['name'],
                color=line_data['color'],
                status='active'
            )
            session.add(line)
            line_objects[line_data['name']] = line

        await session.flush()

        # Create stations with real Bangkok coordinates
        stations_data = [
            # BTS Sukhumvit Line
            {'line': 'Sukhumvit Line', 'name': 'Mo Chit', 'lat': Decimal('13.8022'), 'lng': Decimal('100.5531'), 'interchange': True},
            {'line': 'Sukhumvit Line', 'name': 'Saphan Phut', 'lat': Decimal('13.7562'), 'lng': Decimal('100.5096'), 'interchange': False},
            {'line': 'Sukhumvit Line', 'name': 'Siam', 'lat': Decimal('13.7456'), 'lng': Decimal('100.5351'), 'interchange': True},
            {'line': 'Sukhumvit Line', 'name': 'Asok', 'lat': Decimal('13.7367'), 'lng': Decimal('100.5601'), 'interchange': True},
            {'line': 'Sukhumvit Line', 'name': 'Phrom Phong', 'lat': Decimal('13.7306'), 'lng': Decimal('100.5700'), 'interchange': False},
            {'line': 'Sukhumvit Line', 'name': 'Thong Lo', 'lat': Decimal('13.7238'), 'lng': Decimal('100.5805'), 'interchange': False},
            {'line': 'Sukhumvit Line', 'name': 'Ekkamai', 'lat': Decimal('13.7197'), 'lng': Decimal('100.5902'), 'interchange': False},
            {'line': 'Sukhumvit Line', 'name': 'Phra Khanong', 'lat': Decimal('13.7167'), 'lng': Decimal('100.5978'), 'interchange': False},
            {'line': 'Sukhumvit Line', 'name': 'On Nut', 'lat': Decimal('13.7055'), 'lng': Decimal('100.5994'), 'interchange': False},
            {'line': 'Sukhumvit Line', 'name': 'Bang Chak', 'lat': Decimal('13.6958'), 'lng': Decimal('100.6051'), 'interchange': False},

            # BTS Silom Line
            {'line': 'Silom Line', 'name': 'Siam', 'lat': Decimal('13.7456'), 'lng': Decimal('100.5351'), 'interchange': True},
            {'line': 'Silom Line', 'name': 'Ratchadamri', 'lat': Decimal('13.7395'), 'lng': Decimal('100.5416'), 'interchange': False},
            {'line': 'Silom Line', 'name': 'Sala Daeng', 'lat': Decimal('13.7296'), 'lng': Decimal('100.5340'), 'interchange': True},
            {'line': 'Silom Line', 'name': 'Chong Nonsi', 'lat': Decimal('13.7235'), 'lng': Decimal('100.5308'), 'interchange': False},
            {'line': 'Silom Line', 'name': 'Surasak', 'lat': Decimal('13.7197'), 'lng': Decimal('100.5191'), 'interchange': False},
            {'line': 'Silom Line', 'name': 'Saphan Taksin', 'lat': Decimal('13.7197'), 'lng': Decimal('100.5113'), 'interchange': False},
            {'line': 'Silom Line', 'name': 'Krung Thon Buri', 'lat': Decimal('13.7254'), 'lng': Decimal('100.5067'), 'interchange': False},
            {'line': 'Silom Line', 'name': 'Wongwian Yai', 'lat': Decimal('13.7274'), 'lng': Decimal('100.4978'), 'interchange': False},
            {'line': 'Silom Line', 'name': 'Pho Nimit', 'lat': Decimal('13.7259'), 'lng': Decimal('100.4869'), 'interchange': False},
            {'line': 'Silom Line', 'name': 'Talat Phlu', 'lat': Decimal('13.7285'), 'lng': Decimal('100.4768'), 'interchange': False},

            # MRT Blue Line
            {'line': 'Blue Line', 'name': 'Hua Lamphong', 'lat': Decimal('13.7370'), 'lng': Decimal('100.5148'), 'interchange': False},
            {'line': 'Blue Line', 'name': 'Lumphini', 'lat': Decimal('13.7297'), 'lng': Decimal('100.5340'), 'interchange': True},
            {'line': 'Blue Line', 'name': 'Silom', 'lat': Decimal('13.7281'), 'lng': Decimal('100.5342'), 'interchange': True},
            {'line': 'Blue Line', 'name': 'Sukhumvit', 'lat': Decimal('13.7367'), 'lng': Decimal('100.5601'), 'interchange': True},
            {'line': 'Blue Line', 'name': 'Queen Sirikit National Convention Centre', 'lat': Decimal('13.7237'), 'lng': Decimal('100.5602'), 'interchange': False},
            {'line': 'Blue Line', 'name': 'Khlong Toei', 'lat': Decimal('13.7217'), 'lng': Decimal('100.5640'), 'interchange': False},
            {'line': 'Blue Line', 'name': 'Thailand Cultural Centre', 'lat': Decimal('13.7465'), 'lng': Decimal('100.5602'), 'interchange': False},
            {'line': 'Blue Line', 'name': 'Huai Khwang', 'lat': Decimal('13.7663'), 'lng': Decimal('100.5742'), 'interchange': False},
            {'line': 'Blue Line', 'name': 'Sutthisan', 'lat': Decimal('13.7802'), 'lng': Decimal('100.5743'), 'interchange': False},
            {'line': 'Blue Line', 'name': 'Ratchadaphisek', 'lat': Decimal('13.7901'), 'lng': Decimal('100.5617'), 'interchange': False}
        ]

        station_objects = {}
        for station_data in stations_data:
            line = line_objects[station_data['line']]
            # Check if station already exists (for interchanges)
            existing_station = None
            for existing_name, existing_obj in station_objects.items():
                if existing_name == station_data['name']:
                    existing_station = existing_obj
                    break

            if existing_station:
                # For interchanges, we don't create new stations, just add to StationLine after flush
                pass
            else:
                # Create new station
                station = Station(
                    line_id=line.id,
                    name=station_data['name'],
                    lat=station_data['lat'],
                    long=station_data['lng'],
                    is_interchange=station_data['interchange'],
                    platform_count=2,
                    status='active',
                    zone_number=1
                )
                session.add(station)
                station_objects[station_data['name']] = station

        await session.flush()

        # Create routes between adjacent stations
        sukhumvit_stations = ['Mo Chit', 'Saphan Phut', 'Siam', 'Asok', 'Phrom Phong', 'Thong Lo', 'Ekkamai', 'Phra Khanong', 'On Nut', 'Bang Chak']
        silom_stations = ['Siam', 'Ratchadamri', 'Sala Daeng', 'Chong Nonsi', 'Surasak', 'Saphan Taksin', 'Krung Thon Buri', 'Wongwian Yai', 'Pho Nimit', 'Talat Phlu']

        # Create routes for Sukhumvit Line
        sukhumvit_line = line_objects['Sukhumvit Line']
        for i in range(len(sukhumvit_stations) - 1):
            from_station = station_objects[sukhumvit_stations[i]]
            to_station = station_objects[sukhumvit_stations[i + 1]]

            route = Route(
                line_id=sukhumvit_line.id,
                from_station_id=from_station.id,
                to_station_id=to_station.id,
                transport_type='train',
                distance_km=Decimal('2.5'),
                duration_minutes=3,
                station_count=2,
                status='active'
            )
            session.add(route)

        # Create a sample transit route (Mo Chit to On Nut)
        mo_chit_on_nut_route = TransitRoute(
            name='Mo Chit to On Nut',
            description='Complete journey along Sukhumvit Line from Mo Chit to On Nut',
            status='active',
            total_stations=9,
            estimated_time='30 min'
        )
        session.add(mo_chit_on_nut_route)
        await session.flush()

        # Add route stops in order
        for i, station_name in enumerate(['Mo Chit', 'Saphan Phut', 'Siam', 'Asok', 'Phrom Phong', 'Thong Lo', 'Ekkamai', 'Phra Khanong', 'On Nut']):
            route_stop = RouteStop(
                transit_route_id=mo_chit_on_nut_route.id,
                station_id=station_objects[station_name].id,
                stop_order=i + 1
            )
            session.add(route_stop)

        # Create admin role and user
        admin_role = Role(
            name='admin',
            description='Administrator role with full access to all system features'
        )
        session.add(admin_role)
        await session.flush()

        admin_user = User(
            name='Admin User',
            email='admin@demo.com',
            password=pwd_context.hash('admin123')
        )
        session.add(admin_user)
        await session.flush()

        user_role = UserHasRole(
            user_id=admin_user.id,
            role_id=admin_role.id
        )
        session.add(user_role)

        # Create passenger types
        passenger_types = [
            {'name': 'Adult', 'description': 'Regular adult passenger', 'discount': 0.00, 'age_min': 18, 'age_max': 59, 'proof': False},
            {'name': 'Child', 'description': 'Child passenger (under 14)', 'discount': 50.00, 'age_min': 3, 'age_max': 14, 'proof': True},
            {'name': 'Senior', 'description': 'Senior citizen (60+)', 'discount': 50.00, 'age_min': 60, 'age_max': 120, 'proof': True},
            {'name': 'Student', 'description': 'Student with valid ID', 'discount': 30.00, 'age_min': 15, 'age_max': 25, 'proof': True},
            {'name': 'Disabled', 'description': 'Disabled person with valid certification', 'discount': 100.00, 'age_min': 0, 'age_max': 120, 'proof': True}
        ]

        passenger_type_objects = {}
        for pt_data in passenger_types:
            pt = PassengerType(
                name=pt_data['name'],
                description=pt_data['description'],
                discount_percentage=Decimal(str(pt_data['discount'])),
                age_min=pt_data['age_min'],
                age_max=pt_data['age_max'],
                requires_proof=pt_data['proof']
            )
            session.add(pt)
            passenger_type_objects[pt_data['name']] = pt

        await session.flush()

        # Create fare rules for Bangkok BTS
        adult_type = passenger_type_objects['Adult']
        for i in range(len(sukhumvit_stations) - 1):
            from_station = station_objects[sukhumvit_stations[i]]
            to_station = station_objects[sukhumvit_stations[i + 1]]

            fare_rule = FareRule(
                line_id=sukhumvit_line.id,
                from_station_id=from_station.id,
                to_station_id=to_station.id,
                passenger_type_id=adult_type.id,
                base_price=Decimal('16.00'),  # Thai Baht
                currency='THB',
                valid_from=datetime.now().date(),
                peak_hour_multiplier=Decimal('1.00')
            )
            session.add(fare_rule)

        # Create payment types
        payment_types = [
            {'name': 'Cash', 'code': 'CASH', 'fee': 0.00},
            {'name': 'Credit Card', 'code': 'CREDIT', 'fee': 2.50},
            {'name': 'Rabbit Card', 'code': 'RABBIT', 'fee': 0.00},
            {'name': 'Mobile Payment', 'code': 'MOBILE', 'fee': 1.00}
        ]

        for payment_data in payment_types:
            payment_type = PaymentType(
                name=payment_data['name'],
                code=payment_data['code'],
                status='active',
                processing_fee=Decimal(str(payment_data['fee']))
            )
            session.add(payment_type)

        await session.commit()
        print('✅ Database seeded successfully!')
        print(f'📊 Created {len(companies)} train companies')
        print(f'🚇 Created {len(lines)} train lines')
        print(f'🚉 Created {len(station_objects)} stations')
        print(f'👥 Created {len(passenger_types)} passenger types')
        print(f'💳 Created {len(payment_types)} payment types')
        print(f'👤 Admin login: admin@demo.com / admin123')

if __name__ == '__main__':
    asyncio.run(seed_database())