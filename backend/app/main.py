# backend/app/main.py
from fastapi import FastAPI
from app.api.endpoints import configs
from app.db.database import Base, engine
from app.db import models # <-- Added this line so Base sees the models!

# Ensure tables are created in the database
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Arbitrage Engine API")

# Register our routes
app.include_router(configs.router, prefix="/api/configs", tags=["Configurations"])

@app.get("/health")
def health_check():
    return {"status": "API is running", "database": "connected"}