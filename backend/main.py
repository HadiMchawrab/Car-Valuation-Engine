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

# Helper function to format datetime objects
def format_db_row(row_dict):
    for key, value in row_dict.items():
        if isinstance(value, datetime):
            row_dict[key] = value.isoformat()
    return row_dict

def build_search_filters(search: ListingSearch):
    """Shared function to build filters and params for search queries"""
    filters = []
    params = []
    
    if search.brand:
        filters.append("brand ILIKE %s"); params.append(f"%{search.brand}%")
        logger.info(f"Adding brand filter: {search.brand}")
    if search.model:
        filters.append("model ILIKE %s"); params.append(f"%{search.model}%")
        logger.info(f"Adding model filter: {search.model}")
    if search.min_year is not None:
        filters.append("year >= %s"); params.append(search.min_year)
        logger.info(f"Adding min_year filter: {search.min_year}")
    if search.max_year is not None:
        filters.append("year <= %s"); params.append(search.max_year)
        logger.info(f"Adding max_year filter: {search.max_year}")
    if search.min_price is not None:
        filters.append("price >= %s"); params.append(search.min_price)
        logger.info(f"Adding min_price filter: {search.min_price}")
    if search.max_price is not None:
        filters.append("price <= %s"); params.append(search.max_price)
        logger.info(f"Adding max_price filter: {search.max_price}")
    if search.location_city:
        filters.append("location_city ILIKE %s"); params.append(f"%{search.location_city}%")
        logger.info(f"Adding location_city filter: {search.location_city}")
    if search.location_region:
        filters.append("location_region ILIKE %s"); params.append(f"%{search.location_region}%")
        logger.info(f"Adding location_region filter: {search.location_region}")
    if search.min_mileage is not None:
        filters.append("mileage >= %s"); params.append(search.min_mileage)
        logger.info(f"Adding min_mileage filter: {search.min_mileage}")        
    if search.max_mileage is not None:
        filters.append("mileage <= %s"); params.append(search.max_mileage)
        logger.info(f"Adding max_mileage filter: {search.max_mileage}")
    if search.is_new is not None:
        if search.is_new:
            filters.append("(mileage = 0 OR mileage IS NULL)")
            logger.info("Adding filter for new vehicles (mileage = 0 or NULL)")
        else:
            filters.append("mileage > 0")
            logger.info("Adding filter for used vehicles (mileage > 0)")
    if search.fuel_type:
        filters.append("fuel_type ILIKE %s"); params.append(f"%{search.fuel_type}%")
        logger.info(f"Adding fuel_type filter: {search.fuel_type}")
    if search.transmission_type:
        filters.append("transmission_type ILIKE %s"); params.append(f"%{search.transmission_type}%")
        logger.info(f"Adding transmission_type filter: {search.transmission_type}")
    if search.body_type:
        filters.append("body_type ILIKE %s"); params.append(f"%{search.body_type}%")
        logger.info(f"Adding body_type filter: {search.body_type}")
    if search.condition:
        filters.append("condition ILIKE %s"); params.append(f"%{search.condition}%")
        logger.info(f"Adding condition filter: {search.condition}")
    if search.color:
        filters.append("color ILIKE %s"); params.append(f"%{search.color}%")
        logger.info(f"Adding color filter: {search.color}")
    if search.seller_type:
        filters.append("seller_type ILIKE %s"); params.append(f"%{search.seller_type}%")
        logger.info(f"Adding seller_type filter: {search.seller_type}")
    if search.seller:
        filters.append("(l.seller ILIKE %s OR dd.agency_name ILIKE %s)"); 
        params.append(f"%{search.seller}%")
        params.append(f"%{search.seller}%")
        logger.info(f"Adding seller filter: {search.seller}")
    if search.website:
        filters.append("website ILIKE %s"); params.append(f"%{search.website}%")
        logger.info(f"Adding website filter: {search.website}")
    if search.websites and len(search.websites) > 0:
        website_conditions = []
        for website in search.websites:
            website_conditions.append("website ILIKE %s")
            params.append(f"%{website}%")
        filters.append(f"({' OR '.join(website_conditions)})")
        logger.info(f"Adding websites filter: {search.websites}")
    if search.min_post_date is not None:
        filters.append("post_date >= %s"); params.append(search.min_post_date)
        logger.info(f"Adding min_post_date filter: {search.min_post_date}")
    if search.max_post_date is not None:
        filters.append("post_date <= %s"); params.append(search.max_post_date)
        logger.info(f"Adding max_post_date filter: {search.max_post_date}")
    
    return filters, params

def get_order_by_clause(sort_by: str = "post_date_desc"):
    """Convert sort_by parameter to SQL ORDER BY clause"""
    sort_mappings = {
        "post_date_desc": "post_date DESC",
        "post_date_asc": "post_date ASC", 
        "price_asc": "price ASC NULLS LAST",
        "price_desc": "price DESC NULLS LAST",
        "year_desc": "year DESC NULLS LAST",
        "year_asc": "year ASC NULLS LAST",
        "verified_seller": "COALESCE(dd.seller_verified, false) DESC, post_date DESC"
    }
    
    order_clause = sort_mappings.get(sort_by, "post_date DESC")
    logger.info(f"Using ORDER BY clause: {order_clause}")
    return order_clause

def requires_dubizzle_join(sort_by: str = "post_date_desc"):
    """Check if the sort requires joining with dubizzle_details table"""
    return sort_by == "verified_seller"

# Root endpoint
@app.get("/", response_model=Dict[str, str])
def root():
    return {"message": "Welcome to the Markaba API!"}

# Basic listing endpoints
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

# API endpoint aliases for frontend compatibility
@app.get("/api/listings", response_model=List[Listing])
def get_all_listings_api(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """API alias for /listings endpoint"""
    return get_all_listings(limit=limit, offset=offset)

# Search endpoints
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
        # Log search parameters for debugging
        logger.info(f"Search parameters: {search.dict()}")
        
        cur = conn.cursor()
        filters, params = build_search_filters(search)
        
        where_clause = " AND ".join(filters) if filters else "1=1"
        order_clause = get_order_by_clause(search.sort_by)
        
        # Always join with dubizzle_details to get agency_name and seller_verified
        query = (
            "SELECT l.ad_id, l.url, l.website, l.title, l.price, l.currency, l.brand, l.model, l.year, l.mileage, l.mileage_unit, "
            "l.fuel_type, l.transmission_type, l.body_type, l.condition, l.color, l.seller, l.seller_type, "
            "l.location_city, l.location_region, l.image_url, l.number_of_images, l.post_date, "
            "dd.agency_name, dd.seller_verified "
            "FROM listings l LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id "
            "WHERE " + where_clause + " ORDER BY " + order_clause + " LIMIT %s OFFSET %s"
        )
            
        params.extend([limit, offset])
        logger.info(f"Executing query: {query}")
        logger.info(f"With parameters: {params}")
        
        cur.execute(query, tuple(params))
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        
        logger.info(f"Found {len(rows)} listings")
        if rows:
            logger.info(f"First listing: ad_id={rows[0][0]}, post_date={rows[0][-3]}")
            logger.info(f"Last listing: ad_id={rows[-1][0]}, post_date={rows[-1][-3]}")
        
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
        filters, params = build_search_filters(search)
            
        where_clause = " AND ".join(filters) if filters else "1=1"
        cur.execute(f"SELECT COUNT(*) FROM listings WHERE {where_clause}", tuple(params))
        total = cur.fetchone()[0]
        return {"total": total}
    finally:
        cur.close()
        conn.close()

# Filter option endpoints
@app.get("/makes", response_model=List[str])
def get_all_makes():
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

@app.get("/models", response_model=List[str])
def get_all_models():
    """Get all distinct models"""
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT model FROM listings WHERE model IS NOT NULL AND model <> '' ORDER BY model")
        return [row[0] for row in cur.fetchall()]
    finally:
        cur.close()
        conn.close()

@app.get("/models/{brand}", response_model=List[str])
def get_models_by_brand(brand: str):
    """Get models filtered by brand"""
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT DISTINCT model FROM listings WHERE brand ILIKE %s AND model IS NOT NULL AND model <> '' ORDER BY model",
            (f"%{brand}%",)
        )
        return [row[0] for row in cur.fetchall()]
    finally:
        cur.close()
        conn.close()

@app.get("/years", response_model=List[int])
def get_year_range():
    """Get all years from min to max for the frontend filter"""
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        cur.execute("SELECT MIN(year), MAX(year) FROM listings WHERE year IS NOT NULL")
        min_year, max_year = cur.fetchone()
        # Generate a list of all years from min to max to match frontend expectation
        return list(range(min_year, max_year + 1))
    finally:
        cur.close()
        conn.close()

@app.get("/locations", response_model=List[str])
def get_all_locations():
    """Get all distinct locations (city + region)"""
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
        return [row[0] for row in cur.fetchall()]
    finally:
        cur.close()
        conn.close()

@app.get("/fuel-types", response_model=List[str])
def get_fuel_types():
    """Get all distinct fuel types"""
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT fuel_type FROM listings WHERE fuel_type IS NOT NULL AND fuel_type <> '' ORDER BY fuel_type")
        return [row[0] for row in cur.fetchall()]
    finally:
        cur.close()
        conn.close()

@app.get("/body-types", response_model=List[str])
def get_body_types():
    """Get all distinct body types"""
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT body_type FROM listings WHERE body_type IS NOT NULL AND body_type <> '' ORDER BY body_type")
        return [row[0] for row in cur.fetchall()]
    finally:
        cur.close()
        conn.close()

@app.get("/transmission-types", response_model=List[str])
def get_transmission_types():
    """Get all distinct transmission types"""
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT transmission_type FROM listings WHERE transmission_type IS NOT NULL AND transmission_type <> '' ORDER BY transmission_type")
        return [row[0] for row in cur.fetchall()]
    finally:
        cur.close()
        conn.close()

@app.get("/conditions", response_model=List[str])
def get_conditions():
    """Get all distinct condition values"""
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT condition FROM listings WHERE condition IS NOT NULL AND condition <> '' ORDER BY condition")
        return [row[0] for row in cur.fetchall()]
    finally:
        cur.close()
        conn.close()

@app.get("/colors", response_model=List[str])
def get_colors():
    """Get all distinct color values"""
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT color FROM listings WHERE color IS NOT NULL AND color <> '' ORDER BY color")
        return [row[0] for row in cur.fetchall()]
    finally:
        cur.close()
        conn.close()

@app.get("/seller-types", response_model=List[str])
def get_seller_types():
    """Get all distinct seller types"""
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT seller_type FROM listings WHERE seller_type IS NOT NULL AND seller_type <> '' ORDER BY seller_type")
        return [row[0] for row in cur.fetchall()]
    finally:
        cur.close()
        conn.close()

@app.get("/websites", response_model=List[str])
def get_websites():
    """Get all distinct website values"""
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT website FROM listings WHERE website IS NOT NULL AND website <> '' ORDER BY website")
        return [row[0] for row in cur.fetchall()]
    finally:
        cur.close()
        conn.close()

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

# Analytics endpoints
@app.get("/api/analytics/contributors")
@app.post("/api/analytics/contributors")
def get_top_contributors(limit: int = Query(20, ge=1, le=100), search: ListingSearch = None):
    """Get top contributors with seller statistics and optional filtering"""
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        
        # Build filters if search is provided
        filters = []
        params = []
        if search:
            search_filters, search_params = build_search_filters(search)
            filters.extend(search_filters)
            params.extend(search_params)
        
        # Build WHERE clause - include both individual sellers and agencies
        base_filters = ["(l.seller IS NOT NULL AND l.seller != '') OR (dd.agency_name IS NOT NULL AND dd.agency_name != '')"]
        if filters:
            base_filters.extend(filters)
        where_clause = " AND ".join(base_filters)
        
        # Updated query to handle both individual sellers and agencies
        query = f"""
        SELECT 
            COALESCE(NULLIF(l.seller, ''), dd.agency_name) as seller_name,
            COALESCE(dd.seller_id, l.seller) as seller_id,
            dd.agency_name,
            COUNT(*) as total_listings,
            AVG(l.price) as average_price,
            SUM(l.price) as total_value,
            MIN(l.post_date) as first_listing_date,
            MAX(l.post_date) as last_listing_date,
            COUNT(CASE WHEN l.post_date >= CURRENT_DATE - INTERVAL '1 day' THEN 1 END) as listings_per_day,
            COUNT(CASE WHEN l.post_date >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as listings_per_week,
            COUNT(CASE WHEN l.post_date >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as listings_per_month,
            array_agg(l.post_date ORDER BY l.post_date) as all_post_dates,
            CASE 
                WHEN l.seller IS NOT NULL AND l.seller != '' THEN 'individual_seller'
                WHEN dd.agency_name IS NOT NULL AND dd.agency_name != '' THEN 'agency'
                ELSE 'unknown'
            END as contributor_type
        FROM listings l
        LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id
        WHERE {where_clause}
        GROUP BY l.seller, dd.seller_id, dd.agency_name, CASE 
            WHEN l.seller IS NOT NULL AND l.seller != '' THEN 'individual_seller'
            WHEN dd.agency_name IS NOT NULL AND dd.agency_name != '' THEN 'agency'
            ELSE 'unknown'
        END
        ORDER BY total_listings DESC
        LIMIT %s
        """
        
        params.append(limit)
        cur.execute(query, tuple(params))
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        
        contributors = []
        for row in rows:
            row_dict = dict(zip(cols, row))
            # Format datetime objects
            row_dict = format_db_row(row_dict)
            contributors.append(row_dict)
        
        return {
            "contributors": contributors,
            "total_count": len(contributors)
        }
    except Exception as e:
        logger.error(f"Error getting contributors: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get contributors: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.get("/api/analytics/contributor/{seller_identifier}")
def get_contributor_details(seller_identifier: str):
    """Get detailed analytics for a specific contributor using seller name or seller_id"""
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        
        # Search by seller name, seller_id, or agency_name
        query = """
        SELECT 
            COALESCE(NULLIF(l.seller, ''), dd.agency_name) as seller_name,
            COALESCE(dd.seller_id, l.seller) as seller_id,
            dd.agency_name,
            dd.agency_id,
            COUNT(*) as total_listings,
            AVG(l.price) as average_price,
            SUM(l.price) as total_value,
            MIN(l.post_date) as first_listing_date,
            MAX(l.post_date) as last_listing_date,
            array_agg(l.post_date ORDER BY l.post_date) as all_post_dates,
            array_agg(l.price ORDER BY l.post_date) as all_prices,
            array_agg(l.brand ORDER BY l.post_date) as all_brands,
            array_agg(l.model ORDER BY l.post_date) as all_models,
            CASE 
                WHEN l.seller IS NOT NULL AND l.seller != '' THEN 'individual_seller'
                WHEN dd.agency_name IS NOT NULL AND dd.agency_name != '' THEN 'agency'
                ELSE 'unknown'
            END as contributor_type
        FROM listings l
        LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id
        WHERE (l.seller = %s OR dd.seller_id = %s OR dd.agency_name = %s)
        GROUP BY l.seller, dd.seller_id, dd.agency_name, dd.agency_id, CASE 
            WHEN l.seller IS NOT NULL AND l.seller != '' THEN 'individual_seller'
            WHEN dd.agency_name IS NOT NULL AND dd.agency_name != '' THEN 'agency'
            ELSE 'unknown'
        END
        """
        
        cur.execute(query, (seller_identifier, seller_identifier, seller_identifier))
        row = cur.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Contributor '{seller_identifier}' not found")
        
        cols = [d[0] for d in cur.description]
        contributor_data = format_db_row(dict(zip(cols, row)))
        
        # Get daily distribution for charts
        daily_query = """
        SELECT 
            DATE_TRUNC('day', l.post_date) as day,
            COUNT(*) as listings_count,
            AVG(l.price) as avg_price
        FROM listings l
        LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id
        WHERE (l.seller = %s OR dd.seller_id = %s OR dd.agency_name = %s)
        GROUP BY DATE_TRUNC('day', l.post_date)
        ORDER BY day
        """
        
        cur.execute(daily_query, (seller_identifier, seller_identifier, seller_identifier))
        daily_rows = cur.fetchall()
        daily_cols = [d[0] for d in cur.description]
        daily_data = [format_db_row(dict(zip(daily_cols, row))) for row in daily_rows]
        
        # Get brand distribution
        brand_query = """
        SELECT 
            l.brand,
            COUNT(*) as count
        FROM listings l
        LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id
        WHERE (l.seller = %s OR dd.seller_id = %s OR dd.agency_name = %s)
        GROUP BY l.brand
        ORDER BY count DESC
        """
        
        cur.execute(brand_query, (seller_identifier, seller_identifier, seller_identifier))
        brand_rows = cur.fetchall()
        brand_data = [{"brand": row[0], "count": row[1]} for row in brand_rows]
        
        return {
            "contributor": contributor_data,
            "daily_distribution": daily_data,
            "brand_distribution": brand_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting contributor details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get contributor details: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.get("/api/analytics/stats")
@app.post("/api/analytics/stats")
def get_analytics_stats(search: ListingSearch = None):
    """Get general analytics statistics with optional filtering"""
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        
        # Build filters if search is provided
        filters = []
        params = []
        if search:
            search_filters, search_params = build_search_filters(search)
            filters.extend(search_filters)
            params.extend(search_params)
        
        # Build WHERE clause - include all listings, not just those with sellers
        where_clause = " AND ".join(filters) if filters else "1=1"
        
        # Get overall statistics
        stats_query = f"""
        SELECT 
            COUNT(*) as total_listings,
            COUNT(DISTINCT CASE WHEN l.seller IS NOT NULL AND l.seller != '' THEN l.seller END) as total_sellers,
            AVG(l.price) as average_price,
            COUNT(CASE WHEN l.post_date >= CURRENT_DATE - INTERVAL '1 day' THEN 1 END) as listings_today,
            COUNT(CASE WHEN l.post_date >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as listings_this_week,
            COUNT(CASE WHEN l.post_date >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as listings_this_month
        FROM listings l
        WHERE {where_clause}
        """
        
        cur.execute(stats_query, tuple(params))
        row = cur.fetchone()
        cols = [d[0] for d in cur.description]
        stats = format_db_row(dict(zip(cols, row)))
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting analytics stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics stats: {str(e)}")
    finally:
        cur.close()
        conn.close()

# Enhanced listing detail endpoint with seller information
@app.get("/api/listings/{ad_id}/enhanced", response_model=Dict[str, Any])
def get_enhanced_listing_details(ad_id: str):
    """Get listing details with enhanced seller information from dubizzle_details"""
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        
        # Get listing with seller details
        query = """
        SELECT 
            l.*,
            dd.seller_id,
            dd.agency_name,
            dd.agency_id,
            dd.seller_verified,
            dd.is_agent,
            dd.description,
            dd.image_urls
        FROM listings l
        LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id
        WHERE l.ad_id = %s
        """
        
        cur.execute(query, (ad_id,))
        row = cur.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Listing {ad_id} not found")
        
        cols = [d[0] for d in cur.description]
        listing_data = format_db_row(dict(zip(cols, row)))
        
        # Get seller statistics if seller_id is available
        seller_stats = None
        if listing_data.get('seller_id'):
            stats_query = """
            SELECT 
                COUNT(*) as total_listings,
                AVG(l.price) as average_price,
                MIN(l.post_date) as first_listing_date,
                MAX(l.post_date) as last_listing_date,
                COUNT(CASE WHEN l.post_date >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as recent_listings
            FROM listings l
            LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id
            WHERE dd.seller_id = %s
            """
            
            cur.execute(stats_query, (listing_data['seller_id'],))
            stats_row = cur.fetchone()
            if stats_row:
                stats_cols = [d[0] for d in cur.description]
                seller_stats = format_db_row(dict(zip(stats_cols, stats_row)))
        
        return {
            "listing": listing_data,
            "seller_stats": seller_stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting enhanced listing details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get enhanced listing details: {str(e)}")
    finally:
        cur.close()
        conn.close()
