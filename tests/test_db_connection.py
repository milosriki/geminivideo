import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from shared.db.connection import check_db_connection, init_db, get_db

async def test_connection():
    print("🔌 Testing Database Connection...")
    
    # Override DB URL for testing if needed, but default should work with docker-compose
    # os.environ["DATABASE_URL"] = "postgresql+asyncpg://geminivideo:geminivideo@localhost:5432/geminivideo"
    
    try:
        # We need to implement check_db_connection in connection.py or just use init_db
        print("Initializing DB (creating tables)...")
        await init_db()
        print("✅ Database initialized successfully!")
        
        # Test session
        print("Testing session acquisition...")
        async for session in get_db():
            print("✅ Session acquired!")
            break
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_connection())
