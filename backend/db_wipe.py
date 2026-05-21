# backend/reset_db.py
from app.db.database import engine, Base
# Import all your models so SQLAlchemy knows about them
from app.db.models import User, SearchConfig, FoundOpportunity

print("Dropping all existing tables...")
Base.metadata.drop_all(bind=engine)

print("Recreating tables with new cascade rules...")
Base.metadata.create_all(bind=engine)

print("Database reset complete!")