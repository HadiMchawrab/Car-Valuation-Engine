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
        "verified_seller": "COALESCE(dd.seller_verified, false) DESC, post_date DESC",
        "price_desc": "price DESC NULLS LAST",
        "price_asc": "price ASC NULLS LAST"
    }
    
    return sort_mappings.get(sort_by, "post_date DESC")

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
            "SELECT ad_id, url, website, title, price, currency, brand, model,trim, year, mileage, mileage_unit, "
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
            "SELECT l.ad_id, l.url, l.website, l.title, l.price, l.currency, l.brand, l.model,l.trim, l.year, l.mileage, l.mileage_unit, "
            "l.fuel_type, l.transmission_type, l.body_type, l.condition, l.color, "
            "CASE "
            "WHEN l.seller IS NULL OR l.seller = '' OR l.seller = 'N/A' "
            "THEN COALESCE(NULLIF(dd.agency_name, ''), 'Individual Seller') "
            "ELSE l.seller "
            "END as seller, "
            "l.seller_type, "
            "l.location_city, l.location_region, l.image_url, l.number_of_images, l.post_date, l.date_scraped "
            "FROM listings l LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id WHERE l.ad_id = %s", (ad_id,)
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Listing {ad_id} not found")
        cols = [d[0] for d in cur.description]
        return Listing(**format_db_row(dict(zip(cols, row))))
    finally:
        cur.close()
        conn.close()

@app.get("/api/listings", response_model=List[Listing])
def get_api_listings(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """API endpoint for listings - matches frontend expectations"""
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
        cur = conn.cursor()
        filters, params = build_search_filters(search)
        
        where_clause = " AND ".join(filters) if filters else "1=1"
        order_clause = get_order_by_clause(search.sort_by)
        
        # Always join with dubizzle_details to get agency_name and seller_verified
        query = (
            "SELECT l.ad_id, l.url, l.website, l.title, l.price, l.currency, l.brand, l.model, l.trim, l.year, l.mileage, l.mileage_unit, "
            "l.fuel_type, l.transmission_type, l.body_type, l.condition, l.color, "
            "CASE "
            "WHEN l.seller IS NULL OR l.seller = '' OR l.seller = 'N/A' "
            "THEN COALESCE(NULLIF(dd.agency_name, ''), 'Individual Seller') "
            "ELSE l.seller "
            "END as seller, "
            "l.seller_type, "
            "l.location_city, l.location_region, l.image_url, l.number_of_images, l.post_date, l.date_scraped, "
            "dd.agency_name, dd.seller_verified "
            "FROM listings l LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id "
            "WHERE " + where_clause + " ORDER BY " + order_clause + " LIMIT %s OFFSET %s"
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
        filters, params = build_search_filters(search)
            
        where_clause = " AND ".join(filters) if filters else "1=1"
        
        # Use same table structure as search query to match aliases
        query = f"SELECT COUNT(*) FROM listings l LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id WHERE {where_clause}"
        cur.execute(query, tuple(params))
        total = cur.fetchone()[0]
        return {"total": total}
    finally:
        cur.close()
        conn.close()

# Enhanced Contributor Search Endpoints
@app.post("/search/contributor")
def search_contributor_listings(
    seller_identifier: str = Query(..., description="Seller/Agency identifier"),
    search: ListingSearch = None,
    limit: int = Query(40, ge=1, le=100), 
    offset: int = Query(0, ge=0)
):
    """
    Enhanced contributor search that combines contributor filtering with additional filters.
    This properly handles agency searches using agency_id from dubizzle_details.
    """
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
        
    try:
        cur = conn.cursor()
        
        # Build contributor-specific filter
        contributor_filter = build_contributor_filter(seller_identifier)
        
        # Build additional filters if provided (excludes seller_type to avoid conflicts)
        additional_filters, additional_params = build_search_filters_for_contributor(search) if search else ([], [])
        
        # Combine all filters
        all_filters = [contributor_filter["filter"]] + additional_filters
        all_params = contributor_filter["params"] + additional_params
        
        where_clause = " AND ".join(all_filters)
        order_clause = get_order_by_clause(search.sort_by if search else None)
        
        query = (
            "SELECT l.ad_id, l.url, l.website, l.title, l.price, l.currency, l.brand, l.model, l.trim, l.year, l.mileage, l.mileage_unit, "
            "l.fuel_type, l.transmission_type, l.body_type, l.condition, l.color, l.seller, l.seller_type, "
            "l.location_city, l.location_region, l.image_url, l.number_of_images, l.post_date, "
            "dd.agency_name, dd.seller_verified "
            "FROM listings l LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id "
            "WHERE " + where_clause + " ORDER BY " + order_clause + " LIMIT %s OFFSET %s"
        )
        
        all_params.extend([limit, offset])
        
        cur.execute(query, tuple(all_params))
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        
        return [Listing(**format_db_row(dict(zip(cols, row)))) for row in rows]
        
    except Exception as e:
        logger.error(f"Error in contributor search: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to search contributor listings: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.post("/search/contributor/count")
def count_contributor_listings_with_filters(
    seller_identifier: str = Query(..., description="Seller/Agency identifier"),
    search: ListingSearch = None
):
    """Count contributor listings with additional filters"""
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
        
    try:
        cur = conn.cursor()
        
        # Build contributor-specific filter
        contributor_filter = build_contributor_filter(seller_identifier)
        
        # Build additional filters if provided (excludes seller_type to avoid conflicts)
        additional_filters, additional_params = build_search_filters_for_contributor(search) if search else ([], [])
        
        # Combine all filters
        all_filters = [contributor_filter["filter"]] + additional_filters
        all_params = contributor_filter["params"] + additional_params
        
        where_clause = " AND ".join(all_filters)
        query = f"SELECT COUNT(*) FROM listings l LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id WHERE {where_clause}"
        
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
@app.get("/makes", response_model=List[str])
def get_all_makes(seller: str = Query(None, description="Filter makes by seller/agency")):
    if seller:
        contributor_filter = build_contributor_filter(seller)
        query = f"""
            SELECT DISTINCT l.brand 
            FROM listings l
            LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id
            WHERE l.brand IS NOT NULL AND l.brand <> '' 
            AND ({contributor_filter['filter']})
            ORDER BY l.brand
        """
        return fetch_list(query, contributor_filter['params'])
    else:
        return fetch_list("SELECT DISTINCT brand FROM listings WHERE brand IS NOT NULL AND brand <> '' ORDER BY brand")

@app.get("/models", response_model=List[str])
def get_all_models(seller: str = Query(None, description="Filter models by seller/agency")):
    if seller:
        contributor_filter = build_contributor_filter(seller)
        query = f"""
            SELECT DISTINCT l.model 
            FROM listings l
            LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id
            WHERE l.model IS NOT NULL AND l.model <> '' 
            AND ({contributor_filter['filter']})
            ORDER BY l.model
        """
        return fetch_list(query, contributor_filter['params'])
    else:
        return fetch_list("SELECT DISTINCT model FROM listings WHERE model IS NOT NULL AND model <> '' ORDER BY model")

@app.get("/models/{brand}", response_model=List[str])
def get_models_by_brand(brand: str, seller: str = Query(None, description="Filter models by seller/agency")):
    if seller:
        contributor_filter = build_contributor_filter(seller)
        query = f"""
            SELECT DISTINCT l.model 
            FROM listings l
            LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id
            WHERE l.brand ILIKE %s AND l.model IS NOT NULL AND l.model <> '' 
            AND ({contributor_filter['filter']})
            ORDER BY l.model
        """
        params = [f"%{brand}%"] + contributor_filter['params']
        return fetch_list(query, params)
    else:
        return fetch_list(
            "SELECT DISTINCT model FROM listings WHERE brand ILIKE %s AND model IS NOT NULL AND model <> '' ORDER BY model",
            (f"%{brand}%",)
        )

@app.get("/trims/{brand}/{model}", response_model=List[str])
def get_trims_by_brand_model(brand: str, model: str, seller: str = Query(None, description="Filter trims by seller/agency")):
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
        return fetch_list(query, params)
    else:
        return fetch_list(
            "SELECT DISTINCT trim FROM listings WHERE brand ILIKE %s AND model ILIKE %s AND trim IS NOT NULL AND trim <> '' ORDER BY trim",
            (f"%{brand}%", f"%{model}%")
        )

@app.get("/years", response_model=List[int])
def get_year_range(seller: str = Query(None, description="Filter years by seller/agency")):
    if seller:
        contributor_filter = build_contributor_filter(seller)
        query = f"""
            SELECT MIN(l.year), MAX(l.year) 
            FROM listings l
            LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id
            WHERE l.year IS NOT NULL 
            AND ({contributor_filter['filter']})
        """
        result = fetch_list(query, contributor_filter['params'])
    else:
        result = fetch_list("SELECT MIN(year), MAX(year) FROM listings WHERE year IS NOT NULL")
    # Defensive unpacking
    if result and len(result) > 0:
        # fetch_list likely returns a list of rows, so get the first row
        row = result[0] if isinstance(result[0], (list, tuple)) else result
        if row and len(row) == 2:
            min_year, max_year = row
        else:
            min_year, max_year = None, None
    else:
        min_year, max_year = None, None
    if min_year and max_year:
        return list(range(min_year, max_year + 1))
    else:
        return []

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

@app.get("/locations", response_model=List[str])
def get_all_locations(seller: str = Query(None, description="Filter locations by seller/agency")):
    if seller:
        contributor_filter = build_contributor_filter(seller)
        query = f"""
            SELECT DISTINCT l.location_city 
            FROM listings l
            LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id
            WHERE l.location_city IS NOT NULL AND l.location_city <> '' 
            AND ({contributor_filter['filter']})
            UNION 
            SELECT DISTINCT l.location_region 
            FROM listings l
            LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id
            WHERE l.location_region IS NOT NULL AND l.location_region <> '' 
            AND ({contributor_filter['filter']})
            ORDER BY 1
        """
        params = contributor_filter['params'] + contributor_filter['params']
        return fetch_list(query, params)
    else:
        return fetch_list(
            "SELECT DISTINCT location_city FROM listings WHERE location_city IS NOT NULL AND location_city <> '' "
            "UNION SELECT DISTINCT location_region FROM listings WHERE location_region IS NOT NULL AND location_region <> '' "
            "ORDER BY 1"
        )

@app.get("/fuel-types", response_model=List[str])
def get_fuel_types(seller: str = Query(None, description="Filter fuel types by seller/agency")):
    if seller:
        contributor_filter = build_contributor_filter(seller)
        query = f"""
            SELECT DISTINCT l.fuel_type 
            FROM listings l
            LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id
            WHERE l.fuel_type IS NOT NULL AND l.fuel_type <> '' 
            AND ({contributor_filter['filter']})
            ORDER BY l.fuel_type
        """
        return fetch_list(query, contributor_filter['params'])
    else:
        return fetch_list("SELECT DISTINCT fuel_type FROM listings WHERE fuel_type IS NOT NULL AND fuel_type <> '' ORDER BY fuel_type")

@app.get("/body-types", response_model=List[str])
def get_body_types(seller: str = Query(None, description="Filter body types by seller/agency")):
    if seller:
        contributor_filter = build_contributor_filter(seller)
        query = f"""
            SELECT DISTINCT l.body_type 
            FROM listings l
            LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id
            WHERE l.body_type IS NOT NULL AND l.body_type <> '' 
            AND ({contributor_filter['filter']})
            ORDER BY l.body_type
        """
        return fetch_list(query, contributor_filter['params'])
    else:
        return fetch_list("SELECT DISTINCT body_type FROM listings WHERE body_type IS NOT NULL AND body_type <> '' ORDER BY body_type")

@app.get("/transmission-types", response_model=List[str])
def get_transmission_types(seller: str = Query(None, description="Filter transmission types by seller/agency")):
    if seller:
        contributor_filter = build_contributor_filter(seller)
        query = f"""
            SELECT DISTINCT l.transmission_type 
            FROM listings l
            LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id
            WHERE l.transmission_type IS NOT NULL AND l.transmission_type <> '' 
            AND ({contributor_filter['filter']})
            ORDER BY l.transmission_type
        """
        return fetch_list(query, contributor_filter['params'])
    else:
        return fetch_list("SELECT DISTINCT transmission_type FROM listings WHERE transmission_type IS NOT NULL AND transmission_type <> '' ORDER BY transmission_type")

@app.get("/conditions", response_model=List[str])
def get_conditions():
    return fetch_list("SELECT DISTINCT condition FROM listings WHERE condition IS NOT NULL AND condition <> '' ORDER BY condition")

@app.get("/colors", response_model=List[str])
def get_colors(seller: str = Query(None, description="Filter colors by seller/agency")):
    if seller:
        contributor_filter = build_contributor_filter(seller)
        query = f"""
            SELECT DISTINCT l.color 
            FROM listings l
            LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id
            WHERE l.color IS NOT NULL AND l.color <> '' 
            AND ({contributor_filter['filter']})
            ORDER BY l.color
        """
        return fetch_list(query, contributor_filter['params'])
    else:
        return fetch_list("SELECT DISTINCT color FROM listings WHERE color IS NOT NULL AND color <> '' ORDER BY color")

@app.get("/seller-types", response_model=List[str])
def get_seller_types(seller: str = Query(None, description="Filter seller types by seller/agency")):
    if seller:
        contributor_filter = build_contributor_filter(seller)
        query = f"""
            SELECT DISTINCT l.seller_type 
            FROM listings l
            LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id
            WHERE l.seller_type IS NOT NULL AND l.seller_type <> '' 
            AND ({contributor_filter['filter']})
            ORDER BY l.seller_type
        """
        return fetch_list(query, contributor_filter['params'])
    else:
        return fetch_list("SELECT DISTINCT seller_type FROM listings WHERE seller_type IS NOT NULL AND seller_type <> '' ORDER BY seller_type")

@app.get("/websites", response_model=List[str])
def get_websites(seller: str = Query(None, description="Filter websites by seller/agency")):
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
        return fetch_list(query, contributor_filter['params'])
    else:
        return fetch_list("SELECT DISTINCT website FROM listings WHERE website IS NOT NULL AND website <> '' ORDER BY website")

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
@app.post("/api/analytics/stats")
async def get_analytics_stats(filters: Dict[str, Any] = None):
    """Get analytics statistics with optional filters"""
    try:
        conn = get_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        cursor = conn.cursor()
        
        # Build base query with filters
        base_conditions = []
        params = []
        
        if filters:
            filter_result = build_search_filters(filters)
            if filter_result["conditions"]:
                base_conditions.extend(filter_result["conditions"])
                params.extend(filter_result["params"])
        
        where_clause = " AND ".join(base_conditions) if base_conditions else "1=1"
        
        # Query for total listings
        total_query = f"""
            SELECT COUNT(*) as total_listings
            FROM listings l
            LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id
            WHERE {where_clause}
        """
        cursor.execute(total_query, params)
        total_result = cursor.fetchone()
        
        # Query for this month's listings (PostgreSQL syntax)
        month_query = f"""
            SELECT COUNT(*) as listings_this_month
            FROM listings l
            LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id
            WHERE {where_clause} AND EXTRACT(MONTH FROM l.post_date) = EXTRACT(MONTH FROM CURRENT_DATE) 
            AND EXTRACT(YEAR FROM l.post_date) = EXTRACT(YEAR FROM CURRENT_DATE)
        """
        cursor.execute(month_query, params)
        month_result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return {
            "total_listings": total_result[0] if total_result else 0,
            "listings_this_month": month_result[0] if month_result else 0
        }
        
    except Exception as e:
        logger.error(f"Error fetching analytics stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch analytics stats")

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
            CASE 
                WHEN l.seller IS NULL OR l.seller = '' OR l.seller = 'N/A' 
                THEN COALESCE(dd.agency_name, 'Unknown')
                ELSE COALESCE(NULLIF(l.seller, ''), dd.agency_name, 'Unknown') 
            END as seller_name,
            CASE 
                WHEN l.seller IS NULL OR l.seller = '' OR l.seller = 'N/A' 
                THEN COALESCE(dd.seller_id, 'Unknown')
                ELSE COALESCE(dd.seller_id, l.seller, 'Unknown')
            END as seller_id,
            dd.agency_name,
            COUNT(*) as total_listings,
            CASE 
                WHEN (l.seller IS NOT NULL AND l.seller != '' AND l.seller != 'N/A') THEN 'individual_seller'
                WHEN dd.agency_name IS NOT NULL AND dd.agency_name != '' THEN 'agency'
                ELSE 'unknown'
            END as contributor_type
        FROM listings l
        LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id
        WHERE {where_clause}
        GROUP BY 
            l.seller,
            dd.seller_id, 
            dd.agency_name,
            CASE 
                WHEN l.seller IS NULL OR l.seller = '' OR l.seller = 'N/A' 
                THEN COALESCE(dd.agency_name, 'Unknown')
                ELSE COALESCE(NULLIF(l.seller, ''), dd.agency_name, 'Unknown') 
            END,
            CASE 
                WHEN (l.seller IS NOT NULL AND l.seller != '' AND l.seller != 'N/A') THEN 'individual_seller'
                WHEN dd.agency_name IS NOT NULL AND dd.agency_name != '' THEN 'agency'
                ELSE 'unknown'
            END
        HAVING COUNT(*) > 0
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
        
        # Search by seller name, seller_id, agency_id, or agency_name
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
        WHERE (l.seller = %s OR dd.seller_id = %s OR dd.agency_id = %s OR dd.agency_name = %s)
        GROUP BY l.seller, dd.seller_id, dd.agency_name, dd.agency_id, CASE 
            WHEN l.seller IS NOT NULL AND l.seller != '' THEN 'individual_seller'
            WHEN dd.agency_name IS NOT NULL AND dd.agency_name != '' THEN 'agency'
            ELSE 'unknown'
        END
        """
        
        cur.execute(query, (seller_identifier, seller_identifier, seller_identifier, seller_identifier))
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
        WHERE (l.seller = %s OR dd.seller_id = %s OR dd.agency_id = %s OR dd.agency_name = %s)
        GROUP BY DATE_TRUNC('day', l.post_date)
        ORDER BY day
        """
        
        cur.execute(daily_query, (seller_identifier, seller_identifier, seller_identifier, seller_identifier))
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
        WHERE (l.seller = %s OR dd.seller_id = %s OR dd.agency_id = %s OR dd.agency_name = %s)
        GROUP BY l.brand
        ORDER BY count DESC
        """
        
        cur.execute(brand_query, (seller_identifier, seller_identifier, seller_identifier, seller_identifier))
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

@app.get("/api/analytics/depreciation")
def get_depreciation_analysis(make: str = Query(...), model: str = Query(...)):
    """Get depreciation analysis for a specific make and model"""
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        
        # Get yearly average prices for the make/model combination
        yearly_query = """
        SELECT 
            year,
            AVG(price) as average_price,
            COUNT(*) as listing_count,
            MIN(price) as min_price,
            MAX(price) as max_price
        FROM listings 
        WHERE brand ILIKE %s 
        AND model ILIKE %s 
        AND price IS NOT NULL 
        AND price > 0
        AND year IS NOT NULL
        GROUP BY year
        HAVING COUNT(*) >= 3  -- At least 3 listings per year for meaningful average
        ORDER BY year
        """
        
        cur.execute(yearly_query, (f"%{make}%", f"%{model}%"))
        yearly_rows = cur.fetchall()
        
        if not yearly_rows:
            raise HTTPException(status_code=404, detail=f"No sufficient data found for {make} {model}")
        
        yearly_cols = [d[0] for d in cur.description]
        yearly_data = [format_db_row(dict(zip(yearly_cols, row))) for row in yearly_rows]
        
        # Calculate depreciation metrics
        prices = [float(item['average_price']) for item in yearly_data]
        years = [item['year'] for item in yearly_data]
        
        if len(prices) < 2:
            raise HTTPException(status_code=400, detail="Insufficient data for depreciation analysis")
        
        # Find highest and current (most recent) prices
        highest_price = max(prices)
        current_price = prices[-1]  # Most recent year
        oldest_year = years[0]
        newest_year = years[-1]
        
        # Calculate total depreciation
        total_depreciation = ((highest_price - current_price) / highest_price) * 100 if highest_price > 0 else 0
        
        # Calculate annual depreciation rate
        years_span = newest_year - oldest_year
        annual_depreciation = total_depreciation / years_span if years_span > 0 else 0
        
        return {
            "make": make,
            "model": model,
            "yearly_data": yearly_data,
            "current_avg_price": current_price,
            "highest_avg_price": highest_price,
            "total_depreciation_percentage": round(total_depreciation, 2),
            "annual_depreciation_rate": round(annual_depreciation, 2),
            "analysis_period": f"{oldest_year} - {newest_year}",
            "data_points": len(yearly_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting depreciation analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get depreciation analysis: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.get("/api/analytics/price-spread")
def get_price_spread_analysis(make: str = Query(...), model: str = Query(...),  year: int = Query(...)):
    """Get price spread analysis for a specific make, model, and year"""
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        
        # Get all listings for the specific make/model/year
        listings_query = """
        SELECT 
            ad_id,
            url,
            title,
            price,
            mileage,
            location_city,
            seller,
            post_date
        FROM listings 
        WHERE brand ILIKE %s 
        AND model ILIKE %s 
        AND year = %s
        AND price IS NOT NULL 
        AND price > 0
        ORDER BY price
        """
        cur.execute(listings_query, (f"%{make}%", f"%{model}%", year))
        listings_rows = cur.fetchall()
        
        if not listings_rows:
            raise HTTPException(status_code=404, detail=f"No data found for {make} {model} {year}")

        listings_cols = [d[0] for d in cur.description]
        listings_data = [format_db_row(dict(zip(listings_cols, row))) for row in listings_rows]
        
        # Calculate statistical measures
        prices = [float(item['price']) for item in listings_data]
        
        # Basic statistics
        mean_price = sum(prices) / len(prices)
        median_price = prices[len(prices) // 2] if len(prices) % 2 == 1 else (prices[len(prices) // 2 - 1] + prices[len(prices) // 2]) / 2
        min_price = min(prices)
        max_price = max(prices)
        
        # Standard deviation
        variance = sum((x - mean_price) ** 2 for x in prices) / len(prices)
        std_dev = variance ** 0.5
        
        # Coefficient of variation
        coeff_variation = (std_dev / mean_price) * 100 if mean_price > 0 else 0
        
        return {
            "make": make,
            "model": model,
            "year": year,
            "total_listings": len(listings_data),
            "listings": listings_data,
            "average_price": round(mean_price, 2),
            "median_price": round(median_price, 2),
            "min_price": min_price,
            "max_price": max_price,
            "standard_deviation": round(std_dev, 2),
            "coefficient_of_variation": round(coeff_variation, 2)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting price spread analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get price spread analysis: {str(e)}")
    finally:
        cur.close()
        conn.close()

# Dynamic filtering endpoints - these return options based on current filter state

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
