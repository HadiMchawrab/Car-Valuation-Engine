from fastapi import APIRouter, Query, HTTPException
from typing import List, Dict, Any
from database_connection_service.db_connection import get_connection
import logging
from filters import build_search_filters, build_dynamic_filter_query
from utils import format_db_row

router = APIRouter(prefix="/api/analytics", tags=["analytics"])
logger = logging.getLogger(__name__)

@router.get("/stats")
def get_analytics_stats(
    websites: str = Query(None, description="Comma-separated list of websites to filter by")
):
    """Get analytics statistics with optional website filtering"""
    try:
        conn = get_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")
        cursor = conn.cursor()
        
        filters = []
        params = []
        
        # Handle website filtering
        if websites:
            website_list = [w.strip() for w in websites.split(',') if w.strip()]
            if website_list:
                placeholders = ', '.join(['%s'] * len(website_list))
                filters.append(f"l.website IN ({placeholders})")
                params.extend(website_list)
        
        where_clause = " AND ".join(filters) if filters else "1=1"
        
        total_query = f"""
            SELECT COUNT(*) as total_listings
            FROM listings l
            WHERE {where_clause}
        """
        cursor.execute(total_query, params)
        total_result = cursor.fetchone()
        
        month_query = f"""
            SELECT COUNT(*) as listings_this_month
            FROM listings l
            WHERE {where_clause} AND EXTRACT(MONTH FROM l.post_date) = EXTRACT(MONTH FROM CURRENT_DATE) 
            AND EXTRACT(YEAR FROM l.post_date) = EXTRACT(YEAR FROM CURRENT_DATE)
        """
        cursor.execute(month_query, params)
        month_result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return {
            "total_listings": total_result[0] if total_result else 0,
            "listings_this_month": month_result[0] if month_result else 0,
            "applied_filters": {"websites": website_list if websites else []}
        }
    except Exception as e:
        logger.error(f"Error fetching analytics stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch analytics stats")

@router.get("/contributors")
def get_top_contributors(
    limit: int = Query(20, ge=1, le=100),
    websites: str = Query(None, description="Comma-separated list of websites to filter by")
):
    """Get top contributors with seller statistics and optional filtering"""
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        
        filters = []
        params = []
        
        # Handle website filtering from query parameter
        website_list = []
        if websites:
            website_list = [w.strip() for w in websites.split(',') if w.strip()]
            if website_list:
                placeholders = ', '.join(['%s'] * len(website_list))
                filters.append(f"l.website IN ({placeholders})")
                params.extend(website_list)
                logger.info(f"Contributors endpoint - filtering by websites: {website_list}")
        
        # Check if we need to join dubizzle_details (for Dubizzle website or when showing all websites)
        need_dubizzle_join = not website_list or any('dubizzle' in w.lower() for w in website_list)
        
        # Base filters for valid sellers - this is the key fix
        if need_dubizzle_join:
            # For Dubizzle, we want agency contributors OR individual sellers
            base_filters = []  # No additional base filters, website filter is already applied above
        else:
            # For other websites, just filter by seller existence
            base_filters = ["(l.seller IS NOT NULL AND l.seller != '')"]
        
        if filters:
            base_filters.extend(filters)
        
        # Ensure we always have a valid WHERE clause
        where_clause = " AND ".join(base_filters) if base_filters else "1=1"
        logger.info(f"Contributors endpoint - WHERE clause: {where_clause}")
        logger.info(f"Contributors endpoint - Parameters: {params}")
        
        # Build query with conditional JOIN
        if need_dubizzle_join:
            query = f"""
            SELECT 
                CASE 
                    WHEN l.seller IS NULL OR l.seller = '' OR l.seller = 'N/A'
                    THEN COALESCE(dd.agency_name, 'Unknown Agency')
                    ELSE l.seller
                END as seller_name,
                CASE 
                    WHEN l.seller IS NULL OR l.seller = '' OR l.seller = 'N/A'
                    THEN COALESCE(dd.agency_id, 'unknown')
                    ELSE l.seller
                END as seller_id,
                dd.agency_name,
                l.website,
                COUNT(*) as total_listings,
                CASE 
                    WHEN l.seller IS NULL OR l.seller = '' OR l.seller = 'N/A'
                    THEN 'agency'
                    ELSE 'individual_seller'
                END as contributor_type
            FROM listings l
            LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id
            WHERE {where_clause}
            GROUP BY 
                l.seller,
                dd.agency_id,
                dd.agency_name,
                l.website
            HAVING COUNT(*) > 0 
                AND NOT (l.seller IS NULL OR l.seller = '' OR l.seller = 'N/A') OR dd.agency_name IS NOT NULL
            ORDER BY total_listings DESC
            LIMIT %s
            """
        else:
            query = f"""
            SELECT 
                l.seller as seller_name,
                l.seller as seller_id,
                NULL as agency_name,
                l.website,
                COUNT(*) as total_listings,
                l.seller_type as contributor_type
            FROM listings l
            WHERE {where_clause}
            GROUP BY 
                l.seller,
                l.website,
                l.seller_type
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

@router.get("/contributor/{seller_identifier}")
def get_contributor_details(seller_identifier: str):
    """Get detailed analytics for a specific contributor using seller name or agency name"""
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        
        # First try to find as individual seller
        query = """
        SELECT 
            l.seller as seller_name,
            l.seller as seller_id,
            'individual_seller' as contributor_type,
            COUNT(*) as total_listings,
            AVG(l.price) as average_price,
            SUM(l.price) as total_value,
            MIN(l.post_date) as first_listing_date,
            MAX(l.post_date) as last_listing_date,
            array_agg(l.post_date ORDER BY l.post_date) as all_post_dates,
            array_agg(l.price ORDER BY l.post_date) as all_prices,
            array_agg(l.brand ORDER BY l.post_date) as all_brands,
            array_agg(l.model ORDER BY l.post_date) as all_models
        FROM listings l
        WHERE l.seller = %s
        GROUP BY l.seller
        """
        cur.execute(query, (seller_identifier,))
        row = cur.fetchone()
        
        # If not found as individual seller, try as agency (Dubizzle)
        if not row:
            query = """
            SELECT 
                dd.agency_name as seller_name,
                dd.agency_id as seller_id,
                'agency' as contributor_type,
                COUNT(*) as total_listings,
                AVG(l.price) as average_price,
                SUM(l.price) as total_value,
                MIN(l.post_date) as first_listing_date,
                MAX(l.post_date) as last_listing_date,
                array_agg(l.post_date ORDER BY l.post_date) as all_post_dates,
                array_agg(l.price ORDER BY l.post_date) as all_prices,
                array_agg(l.brand ORDER BY l.post_date) as all_brands,
                array_agg(l.model ORDER BY l.post_date) as all_models
            FROM listings l
            LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id
            WHERE dd.agency_name = %s AND (l.seller IS NULL OR l.seller = '' OR l.seller = 'N/A')
            GROUP BY dd.agency_name, dd.agency_id
            """
            cur.execute(query, (seller_identifier,))
            row = cur.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Contributor '{seller_identifier}' not found")
        
        cols = [d[0] for d in cur.description]
        contributor_data = format_db_row(dict(zip(cols, row)))
        
        # For daily and brand queries, we need to use the same logic
        if contributor_data['contributor_type'] == 'individual_seller':
            # Individual seller daily query
            daily_query = """
            SELECT 
                DATE_TRUNC('day', l.post_date) as day,
                COUNT(*) as listings_count,
                AVG(l.price) as avg_price
            FROM listings l
            WHERE l.seller = %s
            GROUP BY DATE_TRUNC('day', l.post_date)
            ORDER BY day
            """
            cur.execute(daily_query, (seller_identifier,))
            daily_rows = cur.fetchall()
            daily_cols = [d[0] for d in cur.description]
            daily_data = [format_db_row(dict(zip(daily_cols, row))) for row in daily_rows]
            
            # Individual seller brand query
            brand_query = """
            SELECT 
                l.brand,
                COUNT(*) as count
            FROM listings l
            WHERE l.seller = %s
            GROUP BY l.brand
            ORDER BY count DESC
            """
            cur.execute(brand_query, (seller_identifier,))
            brand_rows = cur.fetchall()
        else:
            # Agency daily query
            daily_query = """
            SELECT 
                DATE_TRUNC('day', l.post_date) as day,
                COUNT(*) as listings_count,
                AVG(l.price) as avg_price
            FROM listings l
            LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id
            WHERE dd.agency_name = %s AND (l.seller IS NULL OR l.seller = '' OR l.seller = 'N/A')
            GROUP BY DATE_TRUNC('day', l.post_date)
            ORDER BY day
            """
            cur.execute(daily_query, (seller_identifier,))
            daily_rows = cur.fetchall()
            daily_cols = [d[0] for d in cur.description]
            daily_data = [format_db_row(dict(zip(daily_cols, row))) for row in daily_rows]
            
            # Agency brand query
            brand_query = """
            SELECT 
                l.brand,
                COUNT(*) as count
            FROM listings l
            LEFT JOIN dubizzle_details dd ON l.ad_id = dd.ad_id
            WHERE dd.agency_name = %s AND (l.seller IS NULL OR l.seller = '' OR l.seller = 'N/A')
            GROUP BY l.brand
            ORDER BY count DESC
            """
            cur.execute(brand_query, (seller_identifier,))
            brand_rows = cur.fetchall()
        
        # Process brand data  
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

@router.get("/depreciation")
def get_depreciation_analysis(
    make: str = Query(...),
    model: str = Query(...),
    trim: str = Query(None),
    websites: str = Query(None, description="Comma-separated list of websites to filter by")
):
    """Get depreciation analysis for a specific make and model with optional trim and websites"""
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        # Build the WHERE clause with optional trim and websites filter
        where_conditions = [
            "brand ILIKE %s",
            "model ILIKE %s",
            "price IS NOT NULL",
            "price > 0",
            "year IS NOT NULL"
        ]
        params = [f"%{make}%", f"%{model}%"]
        if trim and trim.strip():
            where_conditions.append("trim ILIKE %s")
            params.append(f"%{trim}%")
        if websites:
            website_list = [w.strip() for w in websites.split(",") if w.strip()]
            if website_list:
                where_conditions.append("(" + " OR ".join(["website ILIKE %s"] * len(website_list)) + ")")
                params.extend([f"%{w}%" for w in website_list])
        where_clause = " AND ".join(where_conditions)
        min_listings = 1 if trim and trim.strip() else 3
        yearly_query = f"""
        SELECT 
            year,
            AVG(price) as average_price,
            COUNT(*) as listing_count,
            MIN(price) as min_price,
            MAX(price) as max_price
        FROM listings 
        WHERE {where_clause}
        GROUP BY year
        HAVING COUNT(*) >= {min_listings}
        ORDER BY year
        """
        cur.execute(yearly_query, tuple(params))
        yearly_rows = cur.fetchall()
        if not yearly_rows:
            trim_text = f" {trim}" if trim and trim.strip() else ""
            raise HTTPException(status_code=404, detail=f"No sufficient data found for {make} {model}{trim_text}")
        yearly_cols = [d[0] for d in cur.description]
        yearly_data = [format_db_row(dict(zip(yearly_cols, row))) for row in yearly_rows]
        prices = [float(item['average_price']) for item in yearly_data]
        years = [item['year'] for item in yearly_data]
        if len(prices) < 2:
            raise HTTPException(status_code=400, detail="Insufficient data for depreciation analysis")
        highest_price = max(prices)
        current_price = prices[-1]
        oldest_year = years[0]
        newest_year = years[-1]
        total_depreciation = ((highest_price - current_price) / highest_price) * 100 if highest_price > 0 else 0
        years_span = newest_year - oldest_year
        annual_depreciation = total_depreciation / years_span if years_span > 0 else 0
        return {
            "make": make,
            "model": model,
            "trim": trim,
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

@router.get("/price-spread")
def get_price_spread_analysis(
    make: str = Query(...),
    model: str = Query(...),
    year: int = Query(...),
    trim: str = Query(None),
    websites: str = Query(None, description="Comma-separated list of websites to filter by")
):
    """Get price spread analysis for a specific make, model, year with optional trim and websites"""
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        where_conditions = [
            "brand ILIKE %s",
            "model ILIKE %s",
            "year = %s",
            "price IS NOT NULL",
            "price > 0"
        ]
        params = [f"%{make}%", f"%{model}%", year]
        if trim and trim.strip():
            where_conditions.append("trim ILIKE %s")
            params.append(f"%{trim}%")
        if websites:
            website_list = [w.strip() for w in websites.split(",") if w.strip()]
            if website_list:
                where_conditions.append("(" + " OR ".join(["website ILIKE %s"] * len(website_list)) + ")")
                params.extend([f"%{w}%" for w in website_list])
        where_clause = " AND ".join(where_conditions)
        listings_query = f"""
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
        WHERE {where_clause}
        ORDER BY price
        """
        cur.execute(listings_query, tuple(params))
        listings_rows = cur.fetchall()
        if not listings_rows:
            trim_text = f" {trim}" if trim and trim.strip() else ""
            raise HTTPException(status_code=404, detail=f"No data found for {make} {model}{trim_text} {year}")
        listings_cols = [d[0] for d in cur.description]
        listings_data = [format_db_row(dict(zip(listings_cols, row))) for row in listings_rows]
        prices = [float(item['price']) for item in listings_data]
        mean_price = sum(prices) / len(prices)
        median_price = prices[len(prices) // 2] if len(prices) % 2 == 1 else (prices[len(prices) // 2 - 1] + prices[len(prices) // 2]) / 2
        min_price = min(prices)
        max_price = max(prices)
        variance = sum((x - mean_price) ** 2 for x in prices) / len(prices)
        std_dev = variance ** 0.5
        coeff_variation = (std_dev / mean_price) * 100 if mean_price > 0 else 0
        return {
            "make": make,
            "model": model,
            "trim": trim,
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

@router.get("/years")
def get_years(make: str = Query(...), model: str = Query(...)):
    """Get the range of years for a specific make and model"""
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        query = """
        SELECT 
            MIN(year) as min_year,
            MAX(year) as max_year
        FROM listings 
        WHERE brand ILIKE %s 
        AND model ILIKE %s 
        AND year IS NOT NULL
        """
        cur.execute(query, (f"%{make}%", f"%{model}%"))
        result = cur.fetchone()

        if result and len(result) == 2:
            min_year, max_year = result
        else:
            min_year, max_year = None, None
        return {
            "min_year": min_year,
            "max_year": max_year
        }
    except Exception as e:
        logger.error(f"Error getting years: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get years: {str(e)}")
    finally:
        cur.close()
        conn.close()