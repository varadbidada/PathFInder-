"""
MongoDB connection manager for Pathfinder AI Career Counselor.
Provides a reusable database connection layer using environment variables.
"""
import os
import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Global MongoDB client and database
_mongo_client: Optional[AsyncIOMotorClient] = None
_database: Optional[AsyncIOMotorDatabase] = None


def get_mongo_uri() -> str:
    """
    Get MongoDB connection URI from environment variables.
    Supports both full URI and component-based configuration.
    """
    # Try full URI first
    mongo_uri = os.getenv("MONGODB_URI")
    if mongo_uri:
        return mongo_uri
    
    # Fallback to component-based configuration
    username = os.getenv("MONGODB_USERNAME", "")
    password = os.getenv("MONGODB_PASSWORD", "")
    host = os.getenv("MONGODB_HOST", "localhost")
    port = os.getenv("MONGODB_PORT", "27017")
    database = os.getenv("MONGODB_DATABASE", "pathfinder")
    
    if username and password:
        return f"mongodb+srv://{username}:{password}@{host}/?retryWrites=true&w=majority"
    else:
        return f"mongodb://{host}:{port}/{database}"


async def connect_to_database() -> AsyncIOMotorDatabase:
    """
    Connect to MongoDB and return the database instance.
    Creates indexes for optimal query performance.
    """
    global _mongo_client, _database
    
    if _database is not None:
        return _database
    
    try:
        mongo_uri = get_mongo_uri()
        database_name = os.getenv("MONGODB_DATABASE", "pathfinder")
        
        logger.info(f"Connecting to MongoDB database: {database_name}")
        
        _mongo_client = AsyncIOMotorClient(
            mongo_uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,
        )
        
        # Verify connection
        await _mongo_client.admin.command('ping')
        logger.info("✅ MongoDB connection successful")
        
        _database = _mongo_client[database_name]
        
        # Create indexes for better query performance
        await create_indexes(_database)
        
        return _database
        
    except ConnectionFailure as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error connecting to MongoDB: {e}")
        raise


async def create_indexes(db: AsyncIOMotorDatabase):
    """Create indexes for all collections to optimize queries."""
    try:
        # Users collection indexes
        await db.users.create_index("email", unique=True)
        await db.users.create_index("created_at")
        
        # Chats collection indexes
        await db.chats.create_index([("user_id", 1), ("session_id", 1)])
        await db.chats.create_index("timestamp")
        await db.chats.create_index("session_id")
        
        # Resumes collection indexes
        await db.resumes.create_index("user_id")
        await db.resumes.create_index("uploaded_at")
        
        # Roadmaps collection indexes
        await db.roadmaps.create_index("user_id")
        await db.roadmaps.create_index("created_at")
        
        # Skill assessments collection indexes
        await db.skill_assessments.create_index("user_id")
        await db.skill_assessments.create_index("assessed_at")
        
        # Internship recommendations collection indexes
        await db.internship_recommendations.create_index("user_id")
        await db.internship_recommendations.create_index("generated_at")
        
        logger.info("✅ Database indexes created successfully")
        
    except Exception as e:
        logger.warning(f"⚠️  Index creation failed (may already exist): {e}")


def get_database() -> AsyncIOMotorDatabase:
    """
    Get the current database instance.
    Must call connect_to_database() first during app startup.
    """
    if _database is None:
        raise RuntimeError("Database not initialized. Call connect_to_database() first.")
    return _database


async def close_database_connection():
    """Close the MongoDB connection gracefully."""
    global _mongo_client, _database
    
    if _mongo_client:
        logger.info("Closing MongoDB connection...")
        _mongo_client.close()
        _mongo_client = None
        _database = None
        logger.info("✅ MongoDB connection closed")


async def check_database_health() -> dict:
    """Check MongoDB connection health."""
    try:
        db = get_database()
        await db.command('ping')
        return {
            "status": "healthy",
            "database": db.name,
            "message": "MongoDB connection is active"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "MongoDB connection failed"
        }
