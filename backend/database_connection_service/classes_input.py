from pydantic import BaseModel
from typing import Optional, List

class ListingBase(BaseModel):
    site: str
    url: str
    title: str
    kilometers: Optional[int] = None
    price: float
    currency: str
    year: int
    make: str
    model: str
    loc: Optional[str] = None
    created_at: str
    image_urls: Optional[str] = None
    
class ListingCreate(ListingBase):
    pass

class Listing(ListingBase):
    id: int
    
    class Config:
        from_attributes = True

class ListingSearch(BaseModel):
    make: Optional[str] = None
    model: Optional[str] = None
    min_year: Optional[int] = None
    max_year: Optional[int] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    location: Optional[str] = None
