from pydantic import BaseModel, Field, validator
from typing import Optional, List, Union, Dict, Any
from datetime import datetime

class Listing(BaseModel):
    ad_id: str
    url: str
    website: str  # was 'site' in old schema
    title: str
    price: float
    currency: str
    brand: str  # was 'make' in old schema
    model: str
    year: int
    mileage: Optional[int] = None  # was 'kilometers' in old schema
    mileage_unit: Optional[str] = None
    fuel_type: Optional[str] = None
    transmission_type: Optional[str] = None
    body_type: Optional[str] = None
    condition: Optional[str] = None
    color: Optional[str] = None
    seller: Optional[str] = None
    seller_type: Optional[str] = None
    location_city: Optional[str] = None  # was part of 'location' in old schema
    location_region: Optional[str] = None  
    image_url: Optional[str] = None  # was 'image' in old schema
    number_of_images: Optional[int] = None
    post_date: Union[str, datetime]  # was 'scraped_at' in old schema

    @validator('post_date', pre=True)
    def parse_post_date(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        return v
        
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }




class DubizzleDetails(BaseModel):
    # The output was cut off but included fields like 'breadcrumb', 'loc_1_id', etc.
    loc_breadcrumb: Optional[str] = None
    loc_1_id: Optional[str] = None
    loc_1_name: Optional[str] = None
    loc_2_id: Optional[str] = None
    loc_2_name: Optional[str] = None
    category_1_id: Optional[str] = None
    category_1_name: Optional[str] = None
    category_2_id: Optional[str] = None
    category_2_name: Optional[str] = None
    page_type: Optional[str] = None
    website_section: Optional[str] = None
    has_video: Optional[bool] = None
    has_panorama: Optional[bool] = None
    deliverable: Optional[bool] = None
    delivery_option: Optional[str] = None


class ListingSearch(BaseModel):
    brand: Optional[str] = None
    model: Optional[str] = None
    min_year: Optional[int] = None
    max_year: Optional[int] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    location_city: Optional[str] = None
    location_region: Optional[str] = None
    min_mileage: Optional[int] = None
    max_mileage: Optional[int] = None
    is_new: Optional[bool] = None  # True for new vehicles (mileage = 0), False for used vehicles (mileage > 0)
    fuel_type: Optional[str] = None
    transmission_type: Optional[str] = None
    body_type: Optional[str] = None
    condition: Optional[str] = None
    color: Optional[str] = None
    seller_type: Optional[str] = None
    min_post_date: Optional[Union[str, datetime]] = None  # Filter listings posted on or after this date
    max_post_date: Optional[Union[str, datetime]] = None  # Filter listings posted on or before this date
    
    @validator('min_post_date', 'max_post_date', pre=True)
    def parse_date_filters(cls, v):
        if v is None:
            return v
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            try:
                # Try to parse ISO format datetime string
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                try:
                    # Try to parse date only format (YYYY-MM-DD)
                    return datetime.strptime(v, '%Y-%m-%d')
                except ValueError:
                    raise ValueError(f"Invalid date format: {v}. Use ISO format or YYYY-MM-DD")
        return v

class ListingSearchResponse(BaseModel):
    listings: List[Listing]
    total_count: int

class ListingWithDetails(BaseModel):
    ad_id: str
    url: str
    website: str
    title: str
    price: float
    currency: str
    brand: str
    model: str
    year: int
    mileage: Optional[int] = None
    mileage_unit: Optional[str] = None
    fuel_type: Optional[str] = None
    transmission_type: Optional[str] = None
    body_type: Optional[str] = None
    condition: Optional[str] = None
    color: Optional[str] = None
    seller: Optional[str] = None
    seller_type: Optional[str] = None
    location_city: Optional[str] = None
    location_region: Optional[str] = None
    image_url: Optional[str] = None
    number_of_images: Optional[int] = None
    post_date: Union[str, datetime]
    details: Optional[DubizzleDetails] = None

    @validator('post_date', pre=True)
    def parse_post_date(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


