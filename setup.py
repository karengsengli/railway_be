#!/usr/bin/env python3

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def setup_database():
    """Setup database with schema and seed data"""

    # Database connection parameters
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL not found in environment variables")
        return False

    # Extract connection details from URL
    # postgresql+asyncpg://user:pass@host/db -> postgresql://user:pass@host/db
    postgres_url = DATABASE_URL.replace('+asyncpg', '').split('?')[0]

    try:
        # Connect to database
        conn = await asyncpg.connect(postgres_url)
        print("✅ Connected to database successfully")

        # Read and execute schema
        print("📋 Creating database schema...")
        with open('schema.sql', 'r') as f:
            schema_sql = f.read()

        await conn.execute(schema_sql)
        print("✅ Database schema created successfully")

        # Read and execute seed data
        print("🌱 Loading seed data...")
        with open('seed_data.sql', 'r') as f:
            seed_sql = f.read()

        await conn.execute(seed_sql)
        print("✅ Seed data loaded successfully")

        # Close connection
        await conn.close()
        print("🎉 Database setup completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        return False

def check_requirements():
    """Check if all required packages are installed"""
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import asyncpg
        import alembic
        import pydantic
        import jose
        import passlib
        import qrcode
        import pandas
        import openpyxl
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Please install requirements: pip install -r requirements/requirements.txt")
        return False

def create_directories():
    """Create necessary directories"""
    directories = [
        'logs',
        'uploads',
        'exports'
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"📁 Created directory: {directory}")

def main():
    print("🚄 Train Transport Booking System - Setup")
    print("=" * 50)

    # Check requirements
    if not check_requirements():
        return

    # Create directories
    create_directories()

    # Setup database
    print("\n🔧 Setting up database...")
    success = asyncio.run(setup_database())

    if success:
        print("\n🎯 Setup completed successfully!")
        print("\nNext steps:")
        print("1. cd src")
        print("2. uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        print("3. Visit http://localhost:8000/docs for API documentation")
        print("4. Open qr_scanner_portal.html for QR code scanner")
    else:
        print("\n❌ Setup failed. Please check the errors above.")

if __name__ == "__main__":
    main()