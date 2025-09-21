#!/usr/bin/env python3

import asyncio
from src.database import engine, Base
from src import models  # Import all models

async def create_tables():
    """Create all database tables"""
    print("Creating all database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully!")

if __name__ == "__main__":
    asyncio.run(create_tables())