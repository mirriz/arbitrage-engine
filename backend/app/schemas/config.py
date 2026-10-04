from pydantic import BaseModel
from typing import Optional

class SearchConfigBase(BaseModel):
    search_term: str
    min_profit_percentage: float = 20.0
    min_profit_flat: float = 15.0
    min_item_price: float = 0.0 # ADDED THIS
    is_active: bool = True

class SearchConfigCreate(SearchConfigBase):
    user_id: Optional[int] = None

class SearchConfigResponse(SearchConfigBase):
    id: int
    user_id: Optional[int] = None

    class Config:
        from_attributes = True