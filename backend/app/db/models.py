# backend/app/db/models.py
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    subscription_tier = Column(String, default="free")
    
    configs = relationship("SearchConfig", back_populates="owner")

class SearchConfig(Base):
    __tablename__ = "search_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Temporarily nullable for easy testing
    search_term = Column(String, nullable=False)
    min_profit_percentage = Column(Float, default=20.0) 
    min_profit_flat = Column(Float, default=15.0)       
    is_active = Column(Boolean, default=True)
    
    owner = relationship("User", back_populates="configs")
    opportunities = relationship("FoundOpportunity", back_populates="config")

class FoundOpportunity(Base):
    __tablename__ = "found_opportunities"
    
    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(Integer, ForeignKey("search_configs.id"))
    fb_listing_id = Column(String, unique=True, index=True, nullable=False)
    fb_title = Column(String, nullable=False)
    fb_price = Column(Float, nullable=False)
    fb_url = Column(String, nullable=False)
    ebay_median_sold = Column(Float, nullable=False)
    calculated_profit = Column(Float, nullable=False)
    status = Column(String, default="New") 
    created_at = Column(DateTime, default=datetime.utcnow)
    
    config = relationship("SearchConfig", back_populates="opportunities")