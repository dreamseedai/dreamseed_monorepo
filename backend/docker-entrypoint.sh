#!/bin/bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DreamSeed Backend - Docker Entrypoint Script
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 DreamSeed Backend - Starting..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Wait for PostgreSQL
echo "⏳ Waiting for PostgreSQL..."
until pg_isready -h postgres -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-dreamseed_dev} >/dev/null 2>&1; do
    echo "   PostgreSQL is unavailable - sleeping"
    sleep 1
done
echo "✅ PostgreSQL is ready!"

# Wait for Redis
echo "⏳ Waiting for Redis..."
until redis-cli -h redis ping >/dev/null 2>&1; do
    echo "   Redis is unavailable - sleeping"
    sleep 1
done
echo "✅ Redis is ready!"

# Run Alembic migrations
echo "📊 Creating database tables..."
python3 << 'PYTHON_SCRIPT'
import asyncio
from app.core.database import async_engine, Base
import app.models  # Import all models

async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('✅ Tables created successfully')
    await async_engine.dispose()

asyncio.run(create_tables())
PYTHON_SCRIPT

# Auto-seed data if enabled
if [ "${AUTO_SEED_DATA:-false}" = "true" ]; then
    echo "🌱 Checking seed data..."
    python3 <<EOF
import sys
import asyncio
sys.path.insert(0, '.')

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func
from app.models.item import Item

DATABASE_URL = "${DATABASE_URL}"

async def check_seed_data():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            result = await session.execute(select(func.count()).select_from(Item))
            item_count = result.scalar()
        
        if item_count == 0:
            print("   No items found. Running seed script...")
            import subprocess
            result = subprocess.run([
                "python3", 
                "../scripts/seed_cat_items.py"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("   ✅ Seed data generated successfully!")
            else:
                print(f"   ⚠️  Seed script failed: {result.stderr}")
        else:
            print(f"   ℹ️  Database already seeded ({item_count} items found)")
    finally:
        await engine.dispose()

asyncio.run(check_seed_data())
EOF
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ Backend initialization complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Execute the main command
exec "$@"
