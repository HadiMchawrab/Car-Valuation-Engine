# main.py
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from database_connection_service.db_connection import get_connection
from database_connection_service.classes_input import (
    Listing, ListingSearch,
    DubizzleDetails, ListingSearchResponse,
    ListingWithDetails
)
from typing import List, Dict
from datetime import datetime

app = FastAPI(
    title="Markaba API",
    description="API for the Markaba car listings database",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper function to format datetime objects
def format_db_row(row_dict):
    for key, value in row_dict.items():
        if isinstance(value, datetime):
            row_dict[key] = value.isoformat()
    return row_dict

@app.get("/", response_model=Dict[str, str])
def root():
    return {"message": "Welcome to the Markaba API!"}

@app.get("/listings", response_model=List[Listing])
def get_all_listings(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT ad_id, url, website, title, price, currency, brand, model, year, mileage, mileage_unit, "
            "fuel_type, transmission_type, body_type, condition, color, seller, seller_type, "
            "location_city, location_region, image_url, number_of_images, post_date "
            "FROM listings ORDER BY ad_id LIMIT %s OFFSET %s",
            (limit, offset)
        )
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        return [Listing(**format_db_row(dict(zip(cols, row)))) for row in rows]
    finally:
        cur.close()
        conn.close()

@app.get("/listings/{ad_id}", response_model=Listing)
def get_listing_by_id(ad_id: str):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT ad_id, url, website, title, price, currency, brand, model, year, mileage, mileage_unit, "
            "fuel_type, transmission_type, body_type, condition, color, seller, seller_type, "
            "location_city, location_region, image_url, number_of_images, post_date "
            "FROM listings WHERE ad_id = %s", (ad_id,)
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Listing {ad_id} not found")
        cols = [d[0] for d in cur.description]
        return Listing(**format_db_row(dict(zip(cols, row))))
    finally:
        cur.close()
        conn.close()

@app.post("/search", response_model=List[Listing])
def search_listings(
    search: ListingSearch,
    limit: int = Query(40, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        filters = []
        params = []
        if search.brand:
            filters.append("brand ILIKE %s"); params.append(f"%{search.brand}%")
        if search.model:
            filters.append("model ILIKE %s"); params.append(f"%{search.model}%")
        if search.min_year is not None:
            filters.append("year >= %s"); params.append(search.min_year)
        if search.max_year is not None:
            filters.append("year <= %s"); params.append(search.max_year)
        if search.min_price is not None:
            filters.append("price >= %s"); params.append(search.min_price)
        if search.max_price is not None:
            filters.append("price <= %s"); params.append(search.max_price)
        if search.location_city:
            filters.append("location_city ILIKE %s"); params.append(f"%{search.location_city}%")
        if search.location_region:
            filters.append("location_region ILIKE %s"); params.append(f"%{search.location_region}%")
        if search.min_mileage is not None:
            filters.append("mileage >= %s"); params.append(search.min_mileage)
        if search.max_mileage is not None:
            filters.append("mileage <= %s"); params.append(search.max_mileage)
        if search.fuel_type:
            filters.append("fuel_type ILIKE %s"); params.append(f"%{search.fuel_type}%")
        if search.transmission_type:
            filters.append("transmission_type ILIKE %s"); params.append(f"%{search.transmission_type}%")
        if search.body_type:
            filters.append("body_type ILIKE %s"); params.append(f"%{search.body_type}%")
        if search.condition:
            filters.append("condition ILIKE %s"); params.append(f"%{search.condition}%")
        if search.color:
            filters.append("color ILIKE %s"); params.append(f"%{search.color}%")
        if search.seller_type:
            filters.append("seller_type ILIKE %s"); params.append(f"%{search.seller_type}%")
            
        where_clause = " AND ".join(filters) if filters else "1=1"
        query = (
            "SELECT ad_id, url, website, title, price, currency, brand, model, year, mileage, mileage_unit, "
            "fuel_type, transmission_type, body_type, condition, color, seller, seller_type, "
            "location_city, location_region, image_url, number_of_images, post_date "
            "FROM listings WHERE " + where_clause + " ORDER BY ad_id LIMIT %s OFFSET %s"
        )
        params.extend([limit, offset])
        cur.execute(query, tuple(params))
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        return [Listing(**format_db_row(dict(zip(cols, row)))) for row in rows]
    finally:
        cur.close()
        conn.close()

@app.post("/search/count", response_model=Dict[str, int])
def count_search_listings(search: ListingSearch):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        filters = []
        params = []
        if search.brand:
            filters.append("brand ILIKE %s"); params.append(f"%{search.brand}%")
        if search.model:
            filters.append("model ILIKE %s"); params.append(f"%{search.model}%")
        if search.min_year is not None:
            filters.append("year >= %s"); params.append(search.min_year)
        if search.max_year is not None:
            filters.append("year <= %s"); params.append(search.max_year)
        if search.min_price is not None:
            filters.append("price >= %s"); params.append(search.min_price)
        if search.max_price is not None:
            filters.append("price <= %s"); params.append(search.max_price)
        if search.location_city:
            filters.append("location_city ILIKE %s"); params.append(f"%{search.location_city}%")
        if search.location_region:
            filters.append("location_region ILIKE %s"); params.append(f"%{search.location_region}%")
        if search.min_mileage is not None:
            filters.append("mileage >= %s"); params.append(search.min_mileage)
        if search.max_mileage is not None:
            filters.append("mileage <= %s"); params.append(search.max_mileage)
        if search.fuel_type:
            filters.append("fuel_type ILIKE %s"); params.append(f"%{search.fuel_type}%")
        if search.transmission_type:
            filters.append("transmission_type ILIKE %s"); params.append(f"%{search.transmission_type}%")
        if search.body_type:
            filters.append("body_type ILIKE %s"); params.append(f"%{search.body_type}%")
        if search.condition:
            filters.append("condition ILIKE %s"); params.append(f"%{search.condition}%")
        if search.color:
            filters.append("color ILIKE %s"); params.append(f"%{search.color}%")
        if search.seller_type:
            filters.append("seller_type ILIKE %s"); params.append(f"%{search.seller_type}%")
            
        where_clause = " AND ".join(filters) if filters else "1=1"
        cur.execute(f"SELECT COUNT(*) FROM listings WHERE {where_clause}", tuple(params))
        total = cur.fetchone()[0]
        return {"total": total}
    finally:
        cur.close()
        conn.close()

@app.get("/brands", response_model=List[str])
def get_all_brands():
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT brand FROM listings WHERE brand IS NOT NULL AND brand <> '' ORDER BY brand")
        return [row[0] for row in cur.fetchall()]
    finally:
        cur.close()
        conn.close()

@app.get("/locations/cities", response_model=List[str])
def get_all_cities():
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT location_city FROM listings WHERE location_city IS NOT NULL AND location_city <> '' ORDER BY location_city")
        return [row[0] for row in cur.fetchall()]
    finally:
        cur.close()
        conn.close()

@app.get("/locations/regions", response_model=List[str])
def get_all_regions():
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT location_region FROM listings WHERE location_region IS NOT NULL AND location_region <> '' ORDER BY location_region")
        return [row[0] for row in cur.fetchall()]
    finally:
        cur.close()
        conn.close()

@app.get("/details/{ad_id}", response_model=DubizzleDetails)
def get_details_by_ad_id(ad_id: str):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT loc_breadcrumb, loc_1_id, loc_1_name, loc_2_id, loc_2_name, "
            "category_1_id, category_1_name, category_2_id, category_2_name, "
            "page_type, website_section, has_video, has_panorama, deliverable, delivery_option "
            "FROM dubizzle_details WHERE ad_id = %s", 
            (ad_id,)
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Details not found for ad {ad_id}")
        cols = [d[0] for d in cur.description]
        return DubizzleDetails(**dict(zip(cols, row)))
    finally:
        cur.close()
        conn.close()

@app.get("/listings/{ad_id}/with-details", response_model=ListingWithDetails)
def get_listing_with_details(ad_id: str):
    base = get_listing_by_id(ad_id)
    try:
        details = get_details_by_ad_id(ad_id)
        data = base.dict()
        data['details'] = details
        return ListingWithDetails(**data)
    except HTTPException as he:
        if he.status_code == 404:
            return ListingWithDetails(**{**base.dict(), 'details': None})
        raise he

