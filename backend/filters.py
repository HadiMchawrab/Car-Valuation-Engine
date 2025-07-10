from typing import List, Dict, Any
from database_connection_service.db_connection import get_connection
from database_connection_service.classes_input import ListingSearch
import logging

logger = logging.getLogger(__name__)

def build_contributor_filter(seller_identifier: str) -> Dict[str, Any]:
    """
    Smart contributor filtering that detects if the identifier is:
    1. Individual seller (use seller field)
    2. Agency (use agency_name, agency_id, or seller_id fields)
    Returns a dict with 'filter' (SQL string) and 'params' (list of params).
    """
    conn = get_connection()
    if not conn:
        return {
            "filter": "(l.seller ILIKE %s OR dd.agency_id = %s OR dd.agency_name ILIKE %s OR dd.seller_id = %s)",
            "params": [f"%{seller_identifier}%", seller_identifier, f"%{seller_identifier}%", seller_identifier]
        }
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM dubizzle_details WHERE agency_id = %s", (seller_identifier,))
        agency_id_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM dubizzle_details WHERE agency_name = %s", (seller_identifier,))
        agency_name_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM dubizzle_details WHERE seller_id = %s", (seller_identifier,))
        seller_id_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM listings WHERE seller = %s", (seller_identifier,))
        individual_seller_count = cur.fetchone()[0]
        if agency_id_count > 0:
            return {"filter": "dd.agency_id = %s", "params": [seller_identifier]}
        elif agency_name_count > 0:
            return {"filter": "dd.agency_name = %s", "params": [seller_identifier]}
        elif seller_id_count > 0:
            return {"filter": "dd.seller_id = %s", "params": [seller_identifier]}
        elif individual_seller_count > 0:
            return {"filter": "l.seller = %s", "params": [seller_identifier]}
        else:
            return {
                "filter": "(l.seller ILIKE %s OR dd.agency_id = %s OR dd.agency_name ILIKE %s OR dd.seller_id = %s)",
                "params": [f"%{seller_identifier}%", seller_identifier, f"%{seller_identifier}%", seller_identifier]
            }
    except Exception as e:
        logger.error(f"Error in contributor detection: {str(e)}")
        return {
            "filter": "(l.seller ILIKE %s OR dd.agency_id = %s OR dd.agency_name ILIKE %s OR dd.seller_id = %s)",
            "params": [f"%{seller_identifier}%", seller_identifier, f"%{seller_identifier}%", seller_identifier]
        }
    finally:
        cur.close()
        conn.close()

def build_search_filters_for_contributor(search: ListingSearch):
    """
    Build filters for contributor searches - excludes seller and seller_type filters
    since we're already filtering by a specific contributor.
    Returns (filters, params)
    """
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

def build_search_filters(search: ListingSearch):
    """
    Shared function to build filters and params for search queries.
    Returns (filters, params)
    """
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
    if search.seller_type:
        filters.append("l.seller_type = %s"); params.append(search.seller_type)
    if search.seller:
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

def build_dynamic_filter_query(current_filters: dict, exclude_field: str = None):
    """
    Build a query that filters data based on current filters, excluding the specified field
    to get available options for that field.
    Returns (where_clause, params)
    """
    filters = []
    params = []
    if current_filters.get('seller'):
        contributor_filter = build_contributor_filter(current_filters['seller'])
        filters.append(f"({contributor_filter['filter']})")
        params.extend(contributor_filter['params'])
    elif exclude_field != 'seller_type' and current_filters.get('seller_type'):
        filters.append("l.seller_type = %s")
        params.append(current_filters['seller_type'])
    if exclude_field != 'brand' and current_filters.get('brand'):
        filters.append("l.brand ILIKE %s")
        params.append(f"%{current_filters['brand']}%")
    if exclude_field != 'model' and current_filters.get('model'):
        filters.append("l.model ILIKE %s")
        params.append(f"%{current_filters['model']}%")
    if exclude_field != 'trim' and current_filters.get('trim'):
        filters.append("l.trim ILIKE %s")
        params.append(f"%{current_filters['trim']}%")
    if exclude_field != 'body_type' and current_filters.get('body_type'):
        filters.append("l.body_type = %s")
        params.append(current_filters['body_type'])
    if exclude_field != 'transmission_type' and current_filters.get('transmission_type'):
        filters.append("l.transmission_type = %s")
        params.append(current_filters['transmission_type'])
    if exclude_field != 'color' and current_filters.get('color'):
        filters.append("l.color = %s")
        params.append(current_filters['color'])
    if exclude_field != 'fuel_type' and current_filters.get('fuel_type'):
        filters.append("l.fuel_type = %s")
        params.append(current_filters['fuel_type'])
    if exclude_field != 'year' and current_filters.get('min_year'):
        filters.append("l.year >= %s")
        params.append(int(current_filters['min_year']))
    if exclude_field != 'year' and current_filters.get('max_year'):
        filters.append("l.year <= %s")
        params.append(int(current_filters['max_year']))
    if exclude_field != 'price' and current_filters.get('min_price'):
        filters.append("l.price >= %s")
        params.append(float(current_filters['min_price']))
    if exclude_field != 'price' and current_filters.get('max_price'):
        filters.append("l.price <= %s")
        params.append(float(current_filters['max_price']))
    if exclude_field != 'location' and current_filters.get('location_city'):
        filters.append("l.location_city ILIKE %s")
        params.append(f"%{current_filters['location_city']}%")
    if exclude_field != 'location' and current_filters.get('location_region'):
        filters.append("l.location_region ILIKE %s")
        params.append(f"%{current_filters['location_region']}%")
    if exclude_field != 'condition' and current_filters.get('is_new') is not None:
        if current_filters['is_new']:
            filters.append("(l.mileage = 0 OR l.mileage IS NULL)")
        else:
            filters.append("l.mileage > 0")
    where_clause = ''
    if filters:
        where_clause = 'WHERE ' + ' AND '.join(filters)
    return where_clause, params 