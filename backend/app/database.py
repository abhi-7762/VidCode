import asyncio
import motor.motor_asyncio
from app.config import get_settings

settings = get_settings()

client: motor.motor_asyncio.AsyncIOMotorClient = None
db: motor.motor_asyncio.AsyncIOMotorDatabase = None


async def connect_db():
    """Create MongoDB connection."""
    global client, db
    try:
        client = motor.motor_asyncio.AsyncIOMotorClient(
            settings.mongodb_url,
            serverSelectionTimeoutMS=1000,
            connectTimeoutMS=1000,
        )
        db = client[settings.mongodb_db_name]
        await asyncio.wait_for(client.admin.command("ping"), timeout=1.0)
        print(f"✅ Connected to MongoDB: {settings.mongodb_db_name}")
    except Exception as e:
        print(f"⚠️ MongoDB connection check: {e}")


async def close_db():
    """Close MongoDB connection."""
    global client
    if client:
        client.close()
        print("🔌 MongoDB connection closed.")


def get_db() -> motor.motor_asyncio.AsyncIOMotorDatabase:
    """Dependency — returns the active database instance."""
    return db

