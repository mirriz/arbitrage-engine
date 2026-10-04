# backend/app/api/endpoints/configs.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import SearchConfig, FoundOpportunity
from app.schemas.config import SearchConfigCreate, SearchConfigResponse
from app.worker.tasks import run_arbitrage_pipeline
from typing import List

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[SearchConfigResponse])
def get_configs(db: Session = Depends(get_db)):
    configs = db.query(SearchConfig).all()
    return configs

@router.post("/", response_model=SearchConfigResponse)
def create_config(config: SearchConfigCreate, db: Session = Depends(get_db)):
    new_config = SearchConfig(**config.dict())
    db.add(new_config)
    db.commit()
    db.refresh(new_config)
    return new_config

@router.delete("/{config_id}")
def delete_config(config_id: int, db: Session = Depends(get_db)):
    config = db.query(SearchConfig).filter(SearchConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    db.delete(config)
    db.commit()
    return {"message": "Deleted"}

@router.get("/{config_id}/opportunities")
def get_opportunities(config_id: int, db: Session = Depends(get_db)):
    opps = db.query(FoundOpportunity).filter(FoundOpportunity.config_id == config_id).all()
    return {"data": opps}

@router.post("/{config_id}/run")
def trigger_scrape(config_id: int, db: Session = Depends(get_db)):
    config = db.query(SearchConfig).filter(SearchConfig.id == config_id).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
        
    # Calling .delay() will natively send 'tasks.run_arbitrage_pipeline'
    task = run_arbitrage_pipeline.delay(config_id)
    
    return {"message": "Scraping task queued successfully", "task_id": task.id}