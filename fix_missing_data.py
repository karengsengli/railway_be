#!/usr/bin/env python3

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import select
from passlib.context import CryptContext
from decimal import Decimal

DATABASE_URL = 'postgresql+asyncpg://neondb_owner:npg_Vv1DS3cYLEyg@ep-shy-violet-a106m9dw-pooler.ap-southeast-1.aws.neon.tech/neondb?ssl=require'
engine = create_async_engine(DATABASE_URL, echo=False)

class Base(DeclarativeBase):
    pass

from src.models import *

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

async def fix_missing_data():
    print('🔧 Fixing missing transit data...')

    async with AsyncSession(engine) as session:
        # Check if Thailand region exists
        thailand_query = select(Region).where(Region.name == 'Thailand')
        result = await session.execute(thailand_query)
        thailand = result.scalar_one_or_none()

        if not thailand:
            thailand = Region(
                name='Thailand',
                country='Thailand',
                timezone='Asia/Bangkok',
                currency='THB'
            )
            session.add(thailand)
            await session.flush()
            print('✅ Created Thailand region')
        else:
            print('✅ Thailand region already exists')

        # Check if BTS company exists
        bts_query = select(TrainCompany).where(TrainCompany.code == 'BTS')
        result = await session.execute(bts_query)
        bts = result.scalar_one_or_none()

        if not bts:
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
            print('✅ Created BTS company')
        else:
            print('✅ BTS company already exists')

        # Check if Sukhumvit Line exists
        sukhumvit_query = select(TrainLine).where(TrainLine.name == 'Sukhumvit Line')
        result = await session.execute(sukhumvit_query)
        sukhumvit = result.scalar_one_or_none()

        if not sukhumvit:
            sukhumvit = TrainLine(
                company_id=bts.id,
                name='Sukhumvit Line',
                color='#009639',
                status='active'
            )
            session.add(sukhumvit)
            await session.flush()
            print('✅ Created Sukhumvit Line')
        else:
            print('✅ Sukhumvit Line already exists')

        # Check and update stations to have correct line_id
        stations_query = select(Station).where(Station.name.in_([
            'Mo Chit', 'Siam', 'Asok', 'Phrom Phong',
            'Thong Lo', 'Ekkamai', 'Phra Khanong', 'On Nut'
        ]))
        result = await session.execute(stations_query)
        existing_stations = result.scalars().all()

        for station in existing_stations:
            if station.line_id != sukhumvit.id:
                station.line_id = sukhumvit.id
                print(f'✅ Updated station {station.name} line_id')

        # Check if admin role exists
        admin_role_query = select(Role).where(Role.name == 'admin')
        result = await session.execute(admin_role_query)
        admin_role = result.scalar_one_or_none()

        if not admin_role:
            admin_role = Role(
                name='admin',
                description='Administrator with full access'
            )
            session.add(admin_role)
            await session.flush()
            print('✅ Created admin role')
        else:
            print('✅ Admin role already exists')

        # Check if admin user exists
        admin_user_query = select(User).where(User.email == 'admin@demo.com')
        result = await session.execute(admin_user_query)
        admin_user = result.scalar_one_or_none()

        if not admin_user:
            admin_user = User(
                name='Admin User',
                email='admin@demo.com',
                password=pwd_context.hash('admin123')
            )
            session.add(admin_user)
            await session.flush()
            print('✅ Created admin user')
        else:
            print('✅ Admin user already exists')

        # Check if user has admin role
        user_role_query = select(UserHasRole).where(
            (UserHasRole.user_id == admin_user.id) &
            (UserHasRole.role_id == admin_role.id)
        )
        result = await session.execute(user_role_query)
        user_role = result.scalar_one_or_none()

        if not user_role:
            user_role = UserHasRole(
                user_id=admin_user.id,
                role_id=admin_role.id
            )
            session.add(user_role)
            print('✅ Added admin role to user')
        else:
            print('✅ Admin user already has admin role')

        # Check passenger types
        adult_query = select(PassengerType).where(PassengerType.name == 'Adult')
        result = await session.execute(adult_query)
        adult = result.scalar_one_or_none()

        if not adult:
            adult = PassengerType(
                name='Adult',
                description='Regular adult passenger',
                discount_percentage=Decimal('0.00'),
                age_min=18,
                age_max=59,
                requires_proof=False
            )
            session.add(adult)
            print('✅ Created Adult passenger type')
        else:
            print('✅ Adult passenger type already exists')

        child_query = select(PassengerType).where(PassengerType.name == 'Child')
        result = await session.execute(child_query)
        child = result.scalar_one_or_none()

        if not child:
            child = PassengerType(
                name='Child',
                description='Child passenger (under 14)',
                discount_percentage=Decimal('50.00'),
                age_min=3,
                age_max=14,
                requires_proof=True
            )
            session.add(child)
            print('✅ Created Child passenger type')
        else:
            print('✅ Child passenger type already exists')

        # Check payment types
        cash_query = select(PaymentType).where(PaymentType.code == 'CASH')
        result = await session.execute(cash_query)
        cash = result.scalar_one_or_none()

        if not cash:
            cash = PaymentType(
                name='Cash',
                code='CASH',
                status='active',
                processing_fee=Decimal('0.00')
            )
            session.add(cash)
            print('✅ Created Cash payment type')
        else:
            print('✅ Cash payment type already exists')

        rabbit_query = select(PaymentType).where(PaymentType.code == 'RABBIT')
        result = await session.execute(rabbit_query)
        rabbit = result.scalar_one_or_none()

        if not rabbit:
            rabbit = PaymentType(
                name='Rabbit Card',
                code='RABBIT',
                status='active',
                processing_fee=Decimal('0.00')
            )
            session.add(rabbit)
            print('✅ Created Rabbit Card payment type')
        else:
            print('✅ Rabbit Card payment type already exists')

        await session.commit()
        print('\n🎉 Database data fix completed successfully!')
        print('📊 All active transit data is now properly configured')
        print('👤 Admin login: admin@demo.com / admin123')

if __name__ == '__main__':
    asyncio.run(fix_missing_data())