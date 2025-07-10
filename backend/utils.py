from datetime import datetime
from filters import build_contributor_filter
from database_connection_service.db_connection import get_connection
from fastapi import HTTPException

def format_db_row(row_dict):
    for key, value in row_dict.items():
        if isinstance(value, datetime):
            row_dict[key] = value.isoformat()
    return row_dict

def fetch_list(query, params=None):
    """
    Execute a query and return a list of the first column from the result.
    Handles DB connection and error handling.
    """
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        cur.execute(query, params or [])
        return [row[0] for row in cur.fetchall()]
    finally:
        cur.close()
        conn.close()

def build_search_filters(search):
    """Shared function to build filters and params for search queries"""
    filters = []
    params = []
    if search.brand:
        filters.append("brand ILIKE %s"); params.append(f"%{search.brand}%")
    if search.model:
        filters.append("model ILIKE %s"); params.append(f"%{search.model}%")
    if search.trim:
        filters.append("trim ILIKE %s"); params.append(f"%{search.trim}%")
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
    if search.is_new is not None:
        if search.is_new:
            filters.append("(mileage = 0 OR mileage IS NULL)")
        else:
            filters.append("mileage > 0")
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
    if search.seller:
        # Smart contributor filtering - detect if it's an individual seller or agency
        contributor_filter = build_contributor_filter(search.seller)
        filters.append(contributor_filter["filter"])
        params.extend(contributor_filter["params"])
    if search.website:
        filters.append("website ILIKE %s"); params.append(f"%{search.website}%")
    if search.websites and len(search.websites) > 0:
        website_conditions = []
        for website in search.websites:
            website_conditions.append("website ILIKE %s")
            params.append(f"%{website}%")
        filters.append(f"({' OR '.join(website_conditions)})")
    if search.min_post_date is not None:
        filters.append("post_date >= %s"); params.append(search.min_post_date)
    if search.max_post_date is not None:
        filters.append("post_date <= %s"); params.append(search.max_post_date)
    return filters, params 