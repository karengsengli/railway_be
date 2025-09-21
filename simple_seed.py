#!/usr/bin/env python3

import asyncio
import sys
import os

sys.path.insert(0, 'src')

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from passlib.context import CryptContext
from decimal import Decimal

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
        thailand = Region(
            name='Thailand',
            country='Thailand',
            timezone='Asia/Bangkok',
            currency='THB'
        )
        session.add(thailand)
        await session.flush()

        # Create BTS company
        bts = TrainCompany(
            name='Bangkok Mass Transit System',
            code='BTS',
            status='active',
            region_id=thailand.id,
            website='https://www.bts.co.th',
            contact_info={'phone': '+66-2-617-6000'}
        )
        session.add(bts)
        await session.flush()

        # Create Sukhumvit Line
        sukhumvit = TrainLine(
            company_id=bts.id,
            name='Sukhumvit Line',
            color='#009639',
            status='active'
        )
        session.add(sukhumvit)
        await session.flush()

        # Create stations
        stations_data = [
            ('Mo Chit', Decimal('13.8022'), Decimal('100.5531')),
            ('Siam', Decimal('13.7456'), Decimal('100.5351')),
            ('Asok', Decimal('13.7367'), Decimal('100.5601')),
            ('Phrom Phong', Decimal('13.7306'), Decimal('100.5700')),
            ('Thong Lo', Decimal('13.7238'), Decimal('100.5805')),
            ('Ekkamai', Decimal('13.7197'), Decimal('100.5902')),
            ('Phra Khanong', Decimal('13.7167'), Decimal('100.5978')),
            ('On Nut', Decimal('13.7055'), Decimal('100.5994'))
        ]

        for name, lat, lng in stations_data:
            station = Station(
                line_id=sukhumvit.id,
                name=name,
                lat=lat,
                long=lng,
                is_interchange=(name in ['Siam', 'Asok']),
                platform_count=2,
                status='active',
                zone_number=1
            )
            session.add(station)

        await session.flush()

        # Create admin role and user
        admin_role = Role(
            name='admin',
            description='Administrator with full access'
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
        adult = PassengerType(
            name='Adult',
            description='Regular adult passenger',
            discount_percentage=Decimal('0.00'),
            age_min=18,
            age_max=59,
            requires_proof=False
        )
        session.add(adult)

        child = PassengerType(
            name='Child',
            description='Child passenger (under 14)',
            discount_percentage=Decimal('50.00'),
            age_min=3,
            age_max=14,
            requires_proof=True
        )
        session.add(child)

        # Create payment types
        cash = PaymentType(
            name='Cash',
            code='CASH',
            status='active',
            processing_fee=Decimal('0.00')
        )
        session.add(cash)

        rabbit = PaymentType(
            name='Rabbit Card',
            code='RABBIT',
            status='active',
            processing_fee=Decimal('0.00')
        )
        session.add(rabbit)

        await session.commit()
        print('✅ Database seeded successfully!')
        print(f'📊 Created 1 company (BTS)')
        print(f'🚇 Created 1 train line (Sukhumvit)')
        print(f'🚉 Created {len(stations_data)} stations')
        print(f'👥 Created 2 passenger types')
        print(f'💳 Created 2 payment types')
        print(f'👤 Admin login: admin@demo.com / admin123')

if __name__ == '__main__':
    asyncio.run(seed_database())