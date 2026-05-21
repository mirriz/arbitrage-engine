# backend/app/api/endpoints/configs.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import SearchConfig, FoundOpportunity
from app.schemas.config import SearchConfigCreate, SearchConfigResponse
from app.worker.tasks import run_arbitrage_pipeline

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ... (other endpoints remain the same) ...

@router.post("/{config_id}/run")
def trigger_scrape(config_id: int, db: Session = Depends(get_db)):
    config = db.query(SearchConfig).filter(SearchConfig.id == config_id).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
        
    # Calling .delay() will natively send 'tasks.run_arbitrage_pipeline'
    task = run_arbitrage_pipeline.delay(config_id)
    
    return {"message": "Scraping task queued successfully", "task_id": task.id}