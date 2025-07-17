from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from database_connection_service.db_connection import get_connection
from database_connection_service.classes_input import (
    Listing, ListingSearch,
    DubizzleDetails, ListingSearchResponse,
    ListingWithDetails
)
from typing import List, Dict, Any
from datetime import datetime
import logging
from routers.analytics import router as analytics_router
from filters import build_contributor_filter, build_search_filters_for_contributor, build_search_filters, build_dynamic_filter_query
from utils import format_db_row, fetch_list

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def get_order_by_clause(sort_by: str = "post_date_desc"):
    """Convert sort_by parameter to SQL ORDER BY clause"""
    sort_mappings = {
        "post_date_desc": "post_date DESC",
        "post_date_asc": "post_date ASC",
        # For Arabic, A-Z is ي to أ (descending), Z-A is أ to ي (ascending)
        "title_az": "title COLLATE \"ar-x-icu\" DESC NULLS LAST",  # أ to ي (A-Z in Arabic)
        "title_za": "title COLLATE \"ar-x-icu\" ASC NULLS LAST",   # ي to أ (Z-A in Arabic)
        "year_desc": "year DESC NULLS LAST",
        "year_asc": "year ASC NULLS LAST",
        "verified_seller": "COALESCE(l.seller_type = 'business', false) DESC, post_date DESC",
        "price_desc": "price DESC NULLS LAST",
        "price_asc": "price ASC NULLS LAST"
    }
    
    return sort_mappings.get(sort_by, "post_date DESC")

# Root endpoint
@app.get("/", response_model=Dict[str, str])
def root():
    return {"message": "Welcome to the Markaba API!"}

# Basic listing endpoints
@app.get("/listings")
def get_all_listings(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0, description="Number of items to skip (overridden by page if provided)"),
    page: int = Query(None, ge=1, description="Page number (1-based, overrides offset if provided)"),
    meta: bool = Query(False, description="Include pagination metadata in response")
):
    if page is not None:
        offset = (page - 1) * limit
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT ad_id, url, website, title, price, currency, brand, model,trim, year, mileage, mileage_unit, "
            "fuel_type, transmission_type, body_type, condition, color, seller, seller_type, "
            "location_city, location_region, image_url, number_of_images, post_date "
            "FROM listings ORDER BY ad_id LIMIT %s OFFSET %s",
            (limit, offset)
        )
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        items = [Listing(**format_db_row(dict(zip(cols, row)))) for row in rows]
        # Get total count
        cur.execute("SELECT COUNT(*) FROM listings")
        total_count = cur.fetchone()[0]
        if meta:
            page_num = (offset // limit) + 1 if limit else 1
            return {
                "items": items,
                "total_count": total_count,
                "page": page_num,
                "items_per_page": limit
            }
        return items
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
            "SELECT l.ad_id, l.url, l.website, l.title, l.price, l.currency, l.brand, l.model,l.trim, l.year, l.mileage, l.mileage_unit, "
            "l.fuel_type, l.transmission_type, l.body_type, l.condition, l.color, l.seller, "
            "l.seller_type, "
            "l.location_city, l.location_region, l.image_url, l.number_of_images, l.post_date, l.date_scraped "
            "FROM listings l WHERE l.ad_id = %s", (ad_id,)
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Listing {ad_id} not found")
        cols = [d[0] for d in cur.description]
        return Listing(**format_db_row(dict(zip(cols, row))))
    finally:
        cur.close()
        conn.close()

# Change /search from POST to GET and convert ListingSearch to query parameters
@app.get("/search")
def search_listings(
    # ListingSearch fields as query params
    brand: str = Query(None),
    model: str = Query(None),
    trim: str = Query(None),
    year: int = Query(None),
    min_price: int = Query(None),
    max_price: int = Query(None),
    min_year: int = Query(None),
    max_year: int = Query(None),
    min_mileage: int = Query(None),
    max_mileage: int = Query(None),
    fuel_type: str = Query(None),
    transmission_type: str = Query(None),
    body_type: str = Query(None),
    condition: str = Query(None),
    color: str = Query(None),
    seller_type: str = Query(None),
    location_city: str = Query(None),
    location_region: str = Query(None),
    website: str = Query(None),
    sort_by: str = Query("post_date_desc"),
    limit: int = Query(40, ge=1, le=100),
    offset: int = Query(0, ge=0, description="Number of items to skip (overridden by page if provided)"),
    page: int = Query(None, ge=1, description="Page number (1-based, overrides offset if provided)"),
    meta: bool = Query(False, description="Include pagination metadata in response")
):
    if page is not None:
        offset = (page - 1) * limit
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        # Build ListingSearch object from query params
        search = ListingSearch(
            brand=brand, model=model, trim=trim, year=year,
            min_price=min_price, max_price=max_price,
            min_year=min_year, max_year=max_year,
            min_mileage=min_mileage, max_mileage=max_mileage,
            fuel_type=fuel_type, transmission_type=transmission_type,
            body_type=body_type, condition=condition, color=color,
            seller_type=seller_type, location_city=location_city,
            location_region=location_region, website=website, sort_by=sort_by
        )
        filters, params = build_search_filters(search)
        where_clause = " AND ".join(filters) if filters else "1=1"
        order_clause = get_order_by_clause(search.sort_by)
        query = (
            "SELECT l.ad_id, l.url, l.website, l.title, l.price, l.currency, l.brand, l.model, l.trim, l.year, l.mileage, l.mileage_unit, "
            "l.fuel_type, l.transmission_type, l.body_type, l.condition, l.color, "
            "CASE "
            "l.seller, "
            "l.seller_type, "
            "l.location_city, l.location_region, l.image_url, l.number_of_images, l.post_date, l.date_scraped "
            "FROM listings l "
            "WHERE " + where_clause + " ORDER BY " + order_clause + " LIMIT %s OFFSET %s"
        )
        params.extend([limit, offset])
        cur.execute(query, tuple(params))
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        items = [Listing(**format_db_row(dict(zip(cols, row)))) for row in rows]
        # Get total count
        cur.execute(f"SELECT COUNT(*) FROM listings l WHERE {where_clause}", tuple(params[:-2]))
        total_count = cur.fetchone()[0]
        if meta:
            page_num = (offset // limit) + 1 if limit else 1
            return {
                "items": items,
                "total_count": total_count,
                "page": page_num,
                "items_per_page": limit
            }
        return items
    finally:
        cur.close()
        conn.close()

# Change /search/count from POST to GET and convert ListingSearch to query parameters
@app.get("/search/count")
def count_search_listings(
    brand: str = Query(None),
    model: str = Query(None),
    trim: str = Query(None),
    year: int = Query(None),
    min_price: int = Query(None),
    max_price: int = Query(None),
    min_year: int = Query(None),
    max_year: int = Query(None),
    min_mileage: int = Query(None),
    max_mileage: int = Query(None),
    fuel_type: str = Query(None),
    transmission_type: str = Query(None),
    body_type: str = Query(None),
    condition: str = Query(None),
    color: str = Query(None),
    seller_type: str = Query(None),
    location_city: str = Query(None),
    location_region: str = Query(None),
    website: str = Query(None),
    sort_by: str = Query("post_date_desc")
):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        search = ListingSearch(
            brand=brand, model=model, trim=trim, year=year,
            min_price=min_price, max_price=max_price,
            min_year=min_year, max_year=max_year,
            min_mileage=min_mileage, max_mileage=max_mileage,
            fuel_type=fuel_type, transmission_type=transmission_type,
            body_type=body_type, condition=condition, color=color,
            seller_type=seller_type, location_city=location_city,
            location_region=location_region, website=website, sort_by=sort_by
        )
        filters, params = build_search_filters(search)
        where_clause = " AND ".join(filters) if filters else "1=1"
        query = f"SELECT COUNT(*) FROM listings l WHERE {where_clause}"
        cur.execute(query, tuple(params))
        total = cur.fetchone()[0]
        return {"total": total}
    finally:
        cur.close()
        conn.close()

# Enhanced Contributor Search Endpoints
# Change /search/contributor from POST to GET and convert ListingSearch to query parameters
@app.get("/search/contributor")
def search_contributor_listings(
    seller_identifier: str = Query(..., description="Seller/Agency identifier"),
    brand: str = Query(None),
    model: str = Query(None),
    trim: str = Query(None),
    year: int = Query(None),
    min_price: int = Query(None),
    max_price: int = Query(None),
    min_year: int = Query(None),
    max_year: int = Query(None),
    min_mileage: int = Query(None),
    max_mileage: int = Query(None),
    fuel_type: str = Query(None),
    transmission_type: str = Query(None),
    body_type: str = Query(None),
    condition: str = Query(None),
    color: str = Query(None),
    seller_type: str = Query(None),
    location_city: str = Query(None),
    location_region: str = Query(None),
    website: str = Query(None),
    sort_by: str = Query("post_date_desc"),
    limit: int = Query(40, ge=1, le=100),
    offset: int = Query(0, ge=0, description="Number of items to skip (overridden by page if provided)"),
    page: int = Query(None, ge=1, description="Page number (1-based, overrides offset if provided)"),
    meta: bool = Query(False, description="Include pagination metadata in response")
):
    if page is not None:
        offset = (page - 1) * limit
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        search = ListingSearch(
            brand=brand, model=model, trim=trim, year=year,
            min_price=min_price, max_price=max_price,
            min_year=min_year, max_year=max_year,
            min_mileage=min_mileage, max_mileage=max_mileage,
            fuel_type=fuel_type, transmission_type=transmission_type,
            body_type=body_type, condition=condition, color=color,
            seller_type=seller_type, location_city=location_city,
            location_region=location_region, website=website, sort_by=sort_by
        ) if any([brand, model, trim, year, min_price, max_price, min_year, max_year, min_mileage, max_mileage, fuel_type, transmission_type, body_type, condition, color, seller_type, location_city, location_region, website, sort_by]) else None
        contributor_filter = build_contributor_filter(seller_identifier)
        additional_filters, additional_params = build_search_filters_for_contributor(search) if search else ([], [])
        all_filters = [contributor_filter["filter"]] + additional_filters
        all_params = contributor_filter["params"] + additional_params
        where_clause = " AND ".join(all_filters)
        order_clause = get_order_by_clause(sort_by)
        query = (
            "SELECT l.ad_id, l.url, l.website, l.title, l.price, l.currency, l.brand, l.model, l.trim, l.year, l.mileage, l.mileage_unit, "
            "l.fuel_type, l.transmission_type, l.body_type, l.condition, l.color, l.seller, l.seller_type, "
            "l.location_city, l.location_region, l.image_url, l.number_of_images, l.post_date "
            "FROM listings l "
            "WHERE " + where_clause + " ORDER BY " + order_clause + " LIMIT %s OFFSET %s"
        )
        all_params.extend([limit, offset])
        cur.execute(query, tuple(all_params))
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        items = [Listing(**format_db_row(dict(zip(cols, row)))) for row in rows]
        # Get total count
        cur.execute(f"SELECT COUNT(*) FROM listings l WHERE {where_clause}", tuple(all_params[:-2]))
        total_count = cur.fetchone()[0]
        if meta:
            page_num = (offset // limit) + 1 if limit else 1
            return {
                "items": items,
                "total_count": total_count,
                "page": page_num,
                "items_per_page": limit
            }
        return items
    except Exception as e:
        logger.error(f"Error in contributor search: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to search contributor listings: {str(e)}")
    finally:
        cur.close()
        conn.close()

# Change /search/contributor/count from POST to GET and convert ListingSearch to query parameters
@app.get("/search/contributor/count")
def count_contributor_listings_with_filters(
    seller_identifier: str = Query(..., description="Seller/Agency identifier"),
    brand: str = Query(None),
    model: str = Query(None),
    trim: str = Query(None),
    year: int = Query(None),
    min_price: int = Query(None),
    max_price: int = Query(None),
    min_year: int = Query(None),
    max_year: int = Query(None),
    min_mileage: int = Query(None),
    max_mileage: int = Query(None),
    fuel_type: str = Query(None),
    transmission_type: str = Query(None),
    body_type: str = Query(None),
    condition: str = Query(None),
    color: str = Query(None),
    seller_type: str = Query(None),
    location_city: str = Query(None),
    location_region: str = Query(None),
    website: str = Query(None),
    sort_by: str = Query("post_date_desc")
):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        search = ListingSearch(
            brand=brand, model=model, trim=trim, year=year,
            min_price=min_price, max_price=max_price,
            min_year=min_year, max_year=max_year,
            min_mileage=min_mileage, max_mileage=max_mileage,
            fuel_type=fuel_type, transmission_type=transmission_type,
            body_type=body_type, condition=condition, color=color,
            seller_type=seller_type, location_city=location_city,
            location_region=location_region, website=website, sort_by=sort_by
        ) if any([brand, model, trim, year, min_price, max_price, min_year, max_year, min_mileage, max_mileage, fuel_type, transmission_type, body_type, condition, color, seller_type, location_city, location_region, website, sort_by]) else None
        contributor_filter = build_contributor_filter(seller_identifier)
        additional_filters, additional_params = build_search_filters_for_contributor(search) if search else ([], [])
        all_filters = [contributor_filter["filter"]] + additional_filters
        all_params = contributor_filter["params"] + additional_params
        where_clause = " AND ".join(all_filters)
        query = f"SELECT COUNT(*) FROM listings l WHERE {where_clause}"
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query, tuple(all_params))
        total = cur.fetchone()[0]
        return {"total": total}
    except Exception as e:
        logger.error(f"Error counting contributor listings with filters: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to count contributor listings: {str(e)}")
    finally:
        cur.close()
        conn.close()

# Filter option endpoints
# Helper for paginated meta response

def paginated_meta_response(items, total_count, limit, offset):
    page = (offset // limit) + 1 if limit else 1
    return {
        "items": items,
        "total_count": total_count,
        "page": page,
        "items_per_page": limit
    }

@app.get("/makes")
def get_all_makes(
    limit: int = Query(200, ge=1),
    offset: int = Query(0, ge=0, description="Number of items to skip (overridden by page if provided)"),
    page: int = Query(None, ge=1, description="Page number (1-based, overrides offset if provided)"),
    meta: bool = Query(False, description="Include pagination metadata in response")
):
    if page is not None:
        offset = (page - 1) * limit
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT brand FROM listings WHERE brand IS NOT NULL AND brand <> '' ORDER BY brand")
        results = [row[0] for row in cur.fetchall()]
        total_count = len(results)
        items = results[offset:offset+limit]
        if meta:
            page_num = (offset // limit) + 1 if limit else 1
            return {
                "items": items,
                "total_count": total_count,
                "page": page_num,
                "items_per_page": limit
            }
        return items
    finally:
        cur.close()
        conn.close()

@app.get("/models")
def get_all_models(
    limit: int = Query(200, ge=1),
    offset: int = Query(0, ge=0, description="Number of items to skip (overridden by page if provided)"),
    page: int = Query(None, ge=1, description="Page number (1-based, overrides offset if provided)"),
    meta: bool = Query(False, description="Include pagination metadata in response")
):
    if page is not None:
        offset = (page - 1) * limit
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT model FROM listings WHERE model IS NOT NULL AND model <> '' ORDER BY model")
        results = [row[0] for row in cur.fetchall()]
        total_count = len(results)
        items = results[offset:offset+limit]
        if meta:
            page_num = (offset // limit) + 1 if limit else 1
            return {
                "items": items,
                "total_count": total_count,
                "page": page_num,
                "items_per_page": limit
            }
        return items
    finally:
        cur.close()
        conn.close()

@app.get("/models/{brand}")
def get_models_by_brand(brand: str,
    limit: int = Query(100, ge=1),
    offset: int = Query(0, ge=0, description="Number of items to skip (overridden by page if provided)"),
    page: int = Query(None, ge=1, description="Page number (1-based, overrides offset if provided)"),
    meta: bool = Query(False, description="Include pagination metadata in response")
):
    if page is not None:
        offset = (page - 1) * limit
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT DISTINCT model FROM listings WHERE brand ILIKE %s AND model IS NOT NULL AND model <> '' ORDER BY model",
            (f"%{brand}%",)
        )
        results = [row[0] for row in cur.fetchall()]
        total_count = len(results)
        items = results[offset:offset+limit]
        if meta:
            page_num = (offset // limit) + 1 if limit else 1
            return {
                "items": items,
                "total_count": total_count,
                "page": page_num,
                "items_per_page": limit
            }
        return items
    finally:
        cur.close()
        conn.close()

@app.get("/trims/{brand}/{model}")
def get_trims_by_brand_model(brand: str, model: str, seller: str = Query(None, description="Filter trims by seller/agency"),
    limit: int = Query(100, ge=1),
    offset: int = Query(0, ge=0, description="Number of items to skip (overridden by page if provided)"),
    page: int = Query(None, ge=1, description="Page number (1-based, overrides offset if provided)"),
    meta: bool = Query(False, description="Include pagination metadata in response")
):
    if page is not None:
        offset = (page - 1) * limit
    if seller:
        contributor_filter = build_contributor_filter(seller)
        query = f"""
            SELECT DISTINCT l.trim 
            FROM listings l
            LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id
            WHERE l.brand ILIKE %s AND l.model ILIKE %s AND l.trim IS NOT NULL AND l.trim <> '' 
            AND ({contributor_filter['filter']})
            ORDER BY l.trim
        """
        params = [f"%{brand}%", f"%{model}%"] + contributor_filter['params']
        results = fetch_list(query, params)
    else:
        results = fetch_list(
            "SELECT DISTINCT trim FROM listings WHERE brand ILIKE %s AND model ILIKE %s AND trim IS NOT NULL AND trim <> '' ORDER BY trim",
            (f"%{brand}%", f"%{model}%")
        )
    total_count = len(results)
    items = results[offset:offset+limit]
    if meta:
        page_num = (offset // limit) + 1 if limit else 1
        return {
            "items": items,
            "total_count": total_count,
            "page": page_num,
            "items_per_page": limit
        }
    return items

@app.get("/years")
def get_year_range(
    limit: int = Query(100, ge=1),
    offset: int = Query(0, ge=0, description="Number of items to skip (overridden by page if provided)"),
    page: int = Query(None, ge=1, description="Page number (1-based, overrides offset if provided)"),
    meta: bool = Query(False, description="Include pagination metadata in response")
):
    if page is not None:
        offset = (page - 1) * limit
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        cur.execute("SELECT MIN(year), MAX(year) FROM listings WHERE year IS NOT NULL")
        min_year, max_year = cur.fetchone()
        all_years = list(range(min_year, max_year + 1))
        total_count = len(all_years)
        items = all_years[offset:offset+limit]
        if meta:
            page_num = (offset // limit) + 1 if limit else 1
            return {
                "items": items,
                "total_count": total_count,
                "page": page_num,
                "items_per_page": limit
            }
        return items
    finally:
        cur.close()
        conn.close()

@app.get("/years/{brand}/{model}", response_model=List[int])
def get_years_by_brand_model(brand: str, model: str):
    # Select all distinct years for the given brand and model, case-insensitive and trimmed
    result = fetch_list(
        "SELECT DISTINCT year FROM listings WHERE LOWER(TRIM(brand)) = LOWER(TRIM(%s)) AND LOWER(TRIM(model)) = LOWER(TRIM(%s)) AND year IS NOT NULL ORDER BY year DESC",
        [brand.strip(), model.strip()]
    )
    # Flatten the result and return as a list of years
    years = [row[0] if isinstance(row, (list, tuple)) else row for row in result]
    return years

@app.get("/locations")
def get_all_locations(
    limit: int = Query(100, ge=1),
    offset: int = Query(0, ge=0, description="Number of items to skip (overridden by page if provided)"),
    page: int = Query(None, ge=1, description="Page number (1-based, overrides offset if provided)"),
    meta: bool = Query(False, description="Include pagination metadata in response")
):
    if page is not None:
        offset = (page - 1) * limit
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT DISTINCT location_city FROM listings WHERE location_city IS NOT NULL AND location_city <> '' "
            "UNION SELECT DISTINCT location_region FROM listings WHERE location_region IS NOT NULL AND location_region <> '' "
            "ORDER BY 1"
        )
        results = [row[0] for row in cur.fetchall()]
        total_count = len(results)
        items = results[offset:offset+limit]
        if meta:
            page_num = (offset // limit) + 1 if limit else 1
            return {
                "items": items,
                "total_count": total_count,
                "page": page_num,
                "items_per_page": limit
            }
        return items
    finally:
        cur.close()
        conn.close()

@app.get("/fuel-types")
def get_fuel_types(
    limit: int = Query(100, ge=1),
    offset: int = Query(0, ge=0, description="Number of items to skip (overridden by page if provided)"),
    page: int = Query(None, ge=1, description="Page number (1-based, overrides offset if provided)"),
    meta: bool = Query(False, description="Include pagination metadata in response")
):
    if page is not None:
        offset = (page - 1) * limit
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT fuel_type FROM listings WHERE fuel_type IS NOT NULL AND fuel_type <> '' ORDER BY fuel_type")
        results = [row[0] for row in cur.fetchall()]
        total_count = len(results)
        items = results[offset:offset+limit]
        if meta:
            page_num = (offset // limit) + 1 if limit else 1
            return {
                "items": items,
                "total_count": total_count,
                "page": page_num,
                "items_per_page": limit
            }
        return items
    finally:
        cur.close()
        conn.close()

@app.get("/body-types")
def get_body_types(
    limit: int = Query(100, ge=1),
    offset: int = Query(0, ge=0, description="Number of items to skip (overridden by page if provided)"),
    page: int = Query(None, ge=1, description="Page number (1-based, overrides offset if provided)"),
    meta: bool = Query(False, description="Include pagination metadata in response")
):
    if page is not None:
        offset = (page - 1) * limit
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT body_type FROM listings WHERE body_type IS NOT NULL AND body_type <> '' ORDER BY body_type")
        results = [row[0] for row in cur.fetchall()]
        total_count = len(results)
        items = results[offset:offset+limit]
        if meta:
            page_num = (offset // limit) + 1 if limit else 1
            return {
                "items": items,
                "total_count": total_count,
                "page": page_num,
                "items_per_page": limit
            }
        return items
    finally:
        cur.close()
        conn.close()

@app.get("/transmission-types")
def get_transmission_types(
    limit: int = Query(100, ge=1),
    offset: int = Query(0, ge=0, description="Number of items to skip (overridden by page if provided)"),
    page: int = Query(None, ge=1, description="Page number (1-based, overrides offset if provided)"),
    meta: bool = Query(False, description="Include pagination metadata in response")
):
    if page is not None:
        offset = (page - 1) * limit
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT transmission_type FROM listings WHERE transmission_type IS NOT NULL AND transmission_type <> '' ORDER BY transmission_type")
        results = [row[0] for row in cur.fetchall()]
        total_count = len(results)
        items = results[offset:offset+limit]
        if meta:
            page_num = (offset // limit) + 1 if limit else 1
            return {
                "items": items,
                "total_count": total_count,
                "page": page_num,
                "items_per_page": limit
            }
        return items
    finally:
        cur.close()
        conn.close()

@app.get("/conditions")
def get_conditions(
    limit: int = Query(100, ge=1),
    offset: int = Query(0, ge=0, description="Number of items to skip (overridden by page if provided)"),
    page: int = Query(None, ge=1, description="Page number (1-based, overrides offset if provided)"),
    meta: bool = Query(False, description="Include pagination metadata in response")
):
    if page is not None:
        offset = (page - 1) * limit
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT condition FROM listings WHERE condition IS NOT NULL AND condition <> '' ORDER BY condition")
        results = [row[0] for row in cur.fetchall()]
        total_count = len(results)
        items = results[offset:offset+limit]
        if meta:
            page_num = (offset // limit) + 1 if limit else 1
            return {
                "items": items,
                "total_count": total_count,
                "page": page_num,
                "items_per_page": limit
            }
        return items
    finally:
        cur.close()
        conn.close()

@app.get("/colors")
def get_colors(
    limit: int = Query(100, ge=1),
    offset: int = Query(0, ge=0, description="Number of items to skip (overridden by page if provided)"),
    page: int = Query(None, ge=1, description="Page number (1-based, overrides offset if provided)"),
    meta: bool = Query(False, description="Include pagination metadata in response")
):
    if page is not None:
        offset = (page - 1) * limit
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT color FROM listings WHERE color IS NOT NULL AND color <> '' ORDER BY color")
        results = [row[0] for row in cur.fetchall()]
        total_count = len(results)
        items = results[offset:offset+limit]
        if meta:
            page_num = (offset // limit) + 1 if limit else 1
            return {
                "items": items,
                "total_count": total_count,
                "page": page_num,
                "items_per_page": limit
            }
        return items
    finally:
        cur.close()
        conn.close()

@app.get("/seller-types")
def get_seller_types(
    limit: int = Query(100, ge=1),
    offset: int = Query(0, ge=0, description="Number of items to skip (overridden by page if provided)"),
    page: int = Query(None, ge=1, description="Page number (1-based, overrides offset if provided)"),
    meta: bool = Query(False, description="Include pagination metadata in response")
):
    if page is not None:
        offset = (page - 1) * limit
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT seller_type FROM listings WHERE seller_type IS NOT NULL AND seller_type <> '' ORDER BY seller_type")
        results = [row[0] for row in cur.fetchall()]
        total_count = len(results)
        items = results[offset:offset+limit]
        if meta:
            page_num = (offset // limit) + 1 if limit else 1
            return {
                "items": items,
                "total_count": total_count,
                "page": page_num,
                "items_per_page": limit
            }
        return items
    finally:
        cur.close()
        conn.close()

@app.get("/websites")
def get_websites(seller: str = Query(None, description="Filter websites by seller/agency"),
    limit: int = Query(100, ge=1),
    offset: int = Query(0, ge=0, description="Number of items to skip (overridden by page if provided)"),
    page: int = Query(None, ge=1, description="Page number (1-based, overrides offset if provided)"),
    meta: bool = Query(False, description="Include pagination metadata in response")
):
    if page is not None:
        offset = (page - 1) * limit
    if seller:
        contributor_filter = build_contributor_filter(seller)
        query = f"""
            SELECT DISTINCT l.website 
            FROM listings l
            LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id
            WHERE l.website IS NOT NULL AND l.website <> '' 
            AND ({contributor_filter['filter']})
            ORDER BY l.website
        """
        results = fetch_list(query, contributor_filter['params'])
    else:
        results = fetch_list("SELECT DISTINCT website FROM listings WHERE website IS NOT NULL AND website <> '' ORDER BY website")
    total_count = len(results)
    items = results[offset:offset+limit]
    if meta:
        page_num = (offset // limit) + 1 if limit else 1
        return {
            "items": items,
            "total_count": total_count,
            "page": page_num,
            "items_per_page": limit
        }
    return items

@app.get("/filter-options", response_model=Dict[str, Any])
def get_all_filter_options():
    """Get all filter options for the frontend in a single call"""
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        filter_options = {}
        
        # Get brands
        cur.execute("SELECT DISTINCT brand FROM listings WHERE brand IS NOT NULL AND brand <> '' ORDER BY brand")
        filter_options["brands"] = [row[0] for row in cur.fetchall()]
        
        # Get years
        cur.execute("SELECT MIN(year), MAX(year) FROM listings WHERE year IS NOT NULL")
        min_year, max_year = cur.fetchone()
        filter_options["years"] = list(range(min_year, max_year + 1))
        
        # Get cities
        cur.execute("SELECT DISTINCT location_city FROM listings WHERE location_city IS NOT NULL AND location_city <> '' ORDER BY location_city")
        filter_options["cities"] = [row[0] for row in cur.fetchall()]
        
        # Get regions
        cur.execute("SELECT DISTINCT location_region FROM listings WHERE location_region IS NOT NULL AND location_region <> '' ORDER BY location_region")
        filter_options["regions"] = [row[0] for row in cur.fetchall()]
        
        # Get fuel types
        cur.execute("SELECT DISTINCT fuel_type FROM listings WHERE fuel_type IS NOT NULL AND fuel_type <> '' ORDER BY fuel_type")
        filter_options["fuel_types"] = [row[0] for row in cur.fetchall()]
        
        # Get body types
        cur.execute("SELECT DISTINCT body_type FROM listings WHERE body_type IS NOT NULL AND body_type <> '' ORDER BY body_type")
        filter_options["body_types"] = [row[0] for row in cur.fetchall()]
        
        # Get transmission types
        cur.execute("SELECT DISTINCT transmission_type FROM listings WHERE transmission_type IS NOT NULL AND transmission_type <> '' ORDER BY transmission_type")
        filter_options["transmission_types"] = [row[0] for row in cur.fetchall()]
        
        # Get conditions
        cur.execute("SELECT DISTINCT condition FROM listings WHERE condition IS NOT NULL AND condition <> '' ORDER BY condition")
        filter_options["conditions"] = [row[0] for row in cur.fetchall()]
        
        # Get colors
        cur.execute("SELECT DISTINCT color FROM listings WHERE color IS NOT NULL AND color <> '' ORDER BY color")
        filter_options["colors"] = [row[0] for row in cur.fetchall()]
        
        # Get seller types
        cur.execute("SELECT DISTINCT seller_type FROM listings WHERE seller_type IS NOT NULL AND seller_type <> '' ORDER BY seller_type")
        filter_options["seller_types"] = [row[0] for row in cur.fetchall()]
        
        # Get websites
        cur.execute("SELECT DISTINCT website FROM listings WHERE website IS NOT NULL AND website <> '' ORDER BY website")
        filter_options["websites"] = [row[0] for row in cur.fetchall()]
        
        return filter_options
    finally:
        cur.close()
        conn.close()

# Dubizzle details endpoints
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

@app.post("/dynamic-filter-options")
def get_dynamic_filter_options(current_filters: dict):
    """
    Get filter options that are available based on current filter selections.
    This ensures cascading filters - e.g., if you select Body Type "Pickup", 
    you only see makes that actually have pickup trucks available.
    """
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cur = conn.cursor()
        result = {}
        
        # Get available makes based on current filters (excluding make filter)
        where_clause, params = build_dynamic_filter_query(current_filters, exclude_field='brand')
        query = f"""
            SELECT DISTINCT l.brand 
            FROM listings l
            LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id
            {where_clause}
            AND l.brand IS NOT NULL AND l.brand <> ''
            ORDER BY l.brand
        """
        cur.execute(query, params)
        result['makes'] = [row[0] for row in cur.fetchall()]
        
        # Get available models based on current filters (excluding model filter)
        where_clause, params = build_dynamic_filter_query(current_filters, exclude_field='model')
        query = f"""
            SELECT DISTINCT l.model 
            FROM listings l
            LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id
            {where_clause}
            AND l.model IS NOT NULL AND l.model <> ''
            ORDER BY l.model
        """
        cur.execute(query, params)
        result['models'] = [row[0] for row in cur.fetchall()]

        # Get available trims based on current filters (excluding trim filter)
        where_clause, params = build_dynamic_filter_query(current_filters, exclude_field='trim')
        query = f"""
            SELECT DISTINCT l.trim 
            FROM listings l
            LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id
            {where_clause}
            AND l.trim IS NOT NULL AND l.trim <> ''
            ORDER BY l.trim
        """
        cur.execute(query, params)
        result['trims'] = [row[0] for row in cur.fetchall()]

        # Get available body types based on current filters
        where_clause, params = build_dynamic_filter_query(current_filters, exclude_field='body_type')
        query = f"""
            SELECT DISTINCT l.body_type 
            FROM listings l
            LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id
            {where_clause}
            AND l.body_type IS NOT NULL AND l.body_type <> ''
            ORDER BY l.body_type
        """
        cur.execute(query, params)
        result['bodyTypes'] = [row[0] for row in cur.fetchall()]
        
        # Get available transmission types based on current filters
        where_clause, params = build_dynamic_filter_query(current_filters, exclude_field='transmission_type')
        query = f"""
            SELECT DISTINCT l.transmission_type 
            FROM listings l
            LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id
            {where_clause}
            AND l.transmission_type IS NOT NULL AND l.transmission_type <> ''
            ORDER BY l.transmission_type
        """
        cur.execute(query, params)
        result['transmissionTypes'] = [row[0] for row in cur.fetchall()]
        
        # Get available colors based on current filters
        where_clause, params = build_dynamic_filter_query(current_filters, exclude_field='color')
        query = f"""
            SELECT DISTINCT l.color 
            FROM listings l
            LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id
            {where_clause}
            AND l.color IS NOT NULL AND l.color <> ''
            ORDER BY l.color
        """
        cur.execute(query, params)
        result['colors'] = [row[0] for row in cur.fetchall()]
        
        # Get available fuel types based on current filters
        where_clause, params = build_dynamic_filter_query(current_filters, exclude_field='fuel_type')
        query = f"""
            SELECT DISTINCT l.fuel_type 
            FROM listings l
            LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id
            {where_clause}
            AND l.fuel_type IS NOT NULL AND l.fuel_type <> ''
            ORDER BY l.fuel_type
        """
        cur.execute(query, params)
        result['fuelTypes'] = [row[0] for row in cur.fetchall()]
        
        # Get available seller types based on current filters
        where_clause, params = build_dynamic_filter_query(current_filters, exclude_field='seller_type')
        query = f"""
            SELECT DISTINCT l.seller_type 
            FROM listings l
            LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id
            {where_clause}
            AND l.seller_type IS NOT NULL AND l.seller_type <> ''
            ORDER BY l.seller_type
        """
        cur.execute(query, params)
        result['sellerTypes'] = [row[0] for row in cur.fetchall()]
        
        # Get available websites based on current filters
        where_clause, params = build_dynamic_filter_query(current_filters, exclude_field='website')
        query = f"""
            SELECT DISTINCT l.website 
            FROM listings l
            LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id
            {where_clause}
            AND l.website IS NOT NULL AND l.website <> ''
            ORDER BY l.website
        """
        cur.execute(query, params)
        result['websites'] = [row[0] for row in cur.fetchall()]
        
        # Get available years based on current filters
        where_clause, params = build_dynamic_filter_query(current_filters, exclude_field='year')
        query = f"""
            SELECT MIN(l.year), MAX(l.year) 
            FROM listings l
            LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id
            {where_clause}
            AND l.year IS NOT NULL
        """
        cur.execute(query, params)
        min_year, max_year = cur.fetchone()
        if min_year and max_year:
            result['years'] = list(range(min_year, max_year + 1))
        else:
            result['years'] = []
        
        # Get available locations based on current filters
        where_clause, params = build_dynamic_filter_query(current_filters, exclude_field='location')
        query = f"""
            SELECT DISTINCT l.location_city 
            FROM listings l
            LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id
            {where_clause}
            AND l.location_city IS NOT NULL AND l.location_city <> ''
            UNION 
            SELECT DISTINCT l.location_region 
            FROM listings l
            LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id
            {where_clause}
            AND l.location_region IS NOT NULL AND l.location_region <> ''
            ORDER BY 1
        """
        params_doubled = params + params  # Union requires params twice
        cur.execute(query, params_doubled)
        result['locations'] = [row[0] for row in cur.fetchall()]
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting dynamic filter options: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get dynamic filter options: {str(e)}")
    finally:
        cur.close()
        conn.close()

app.include_router(analytics_router)
