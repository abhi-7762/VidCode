import motor.motor_asyncio
from app.config import get_settings

settings = get_settings()

client: motor.motor_asyncio.AsyncIOMotorClient = None
db: motor.motor_asyncio.AsyncIOMotorDatabase = None


async def connect_db():
    """Create MongoDB connection."""
    global client, db
    client = motor.motor_asyncio.AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db_name]
    # Ping to confirm connection
    await client.admin.command("ping")
    print(f"✅ Connected to MongoDB: {settings.mongodb_db_name}")


async def close_db():
    """Close MongoDB connection."""
    global client
    if client:
        client.close()
        print("🔌 MongoDB connection closed.")


def get_db() -> motor.motor_asyncio.AsyncIOMotorDatabase:
    """Dependency — returns the active database instance."""
    return db

