#!/usr/bin/env python3
import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from src.models import TrainLine

DATABASE_URL = "postgresql+asyncpg://neondb_owner:npg_Vv1DS3cYLEyg@ep-shy-violet-a106m9dw-pooler.ap-southeast-1.aws.neon.tech/neondb?ssl=require"

async def check_lines():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute(select(TrainLine.id, TrainLine.name))
        lines = result.fetchall()
        print('Existing train lines:')
        for line in lines:
            print(f'  ID: {line.id}, Name: {line.name}')

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_lines())