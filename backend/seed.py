import asyncio
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.db import init_db
from app.db.seed import seed_database

async def main():
    print("Initializing database tables...")
    await init_db()
    print("Seeding database...")
    await seed_database()
    print("Database initialization and seeding completed!")

if __name__ == "__main__":
    asyncio.run(main())
