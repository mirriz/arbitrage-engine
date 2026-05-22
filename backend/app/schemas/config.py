# backend/app/schemas/config.py
from pydantic import BaseModel
from typing import Optional

class SearchConfigBase(BaseModel):
    search_term: str
    min_profit_percentage: float = 20.0
    min_profit_flat: float = 15.0
    
    # --- NEW: Dynamic Filtering Fields ---
    min_listing_price: float = 0.0
    max_listing_price: Optional[float] = None
    category_id: Optional[str] = None
    
    is_active: bool = True

class SearchConfigCreate(SearchConfigBase):
    user_id: Optional[int] = None # Defaults to None so we bypass the user check for now

class SearchConfigResponse(SearchConfigBase):
    id: int
    user_id: Optional[int] = None

    class Config:
        from_attributes = True