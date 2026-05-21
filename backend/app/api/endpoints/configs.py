# backend/app/api/endpoints/configs.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import SearchConfig, FoundOpportunity
from app.schemas.config import SearchConfigCreate, SearchConfigResponse

# Import our Celery task
from app.worker.tasks import run_arbitrage_pipeline

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=SearchConfigResponse)
def create_config(config: SearchConfigCreate, db: Session = Depends(get_db)):
    db_config = SearchConfig(**config.model_dump())
    db.add(db_config)
    db.commit()
    db.refresh(db_config) 
    return db_config

# --- NEW ENDPOINTS BELOW ---

@router.post("/{config_id}/run")
def trigger_scrape(config_id: int, db: Session = Depends(get_db)):
    """Triggers the background Celery worker for a specific search config."""
    config = db.query(SearchConfig).filter(SearchConfig.id == config_id).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
        
    # .delay() is the Celery command that sends the task to Redis instead of running it immediately
    task = run_arbitrage_pipeline.delay(config_id)
    
    return {"message": "Scraping task queued successfully", "task_id": task.id}

@router.get("/{config_id}/opportunities")
def get_opportunities(config_id: int, db: Session = Depends(get_db)):
    """Fetches all profitable items found for a specific search config."""
    opportunities = db.query(FoundOpportunity).filter(FoundOpportunity.config_id == config_id).all()
    return {"count": len(opportunities), "data": opportunities}

@router.get("/", response_model=list[SearchConfigResponse])
def get_all_configs(db: Session = Depends(get_db)):
    """Fetches all search configurations from the database."""
    return db.query(SearchConfig).all()

@router.delete("/{config_id}")
def delete_config(config_id: int, db: Session = Depends(get_db)):
    """Deletes a specific search configuration."""
    config = db.query(SearchConfig).filter(SearchConfig.id == config_id).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
        
    db.delete(config)
    db.commit()
    return {"message": f"Config {config_id} deleted successfully"}