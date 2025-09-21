#!/bin/bash

# Render startup script for ThakhinMala Train Booking System

echo "Starting ThakhinMala Train Booking API..."
echo "Python version: $(python --version)"
echo "Current directory: $(pwd)"

# Create tables if they don't exist
echo "Setting up database..."
python -c "
import asyncio
import sys
sys.path.append('src')

from src.database import init_db

async def setup():
    print('Initializing database...')
    await init_db()
    print('Database initialization complete')

if __name__ == '__main__':
    asyncio.run(setup())
"

# Start the FastAPI application
echo "Starting FastAPI server..."
exec uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}