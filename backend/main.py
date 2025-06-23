from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from psycopg2.extras import RealDictCursor
from database_connection_service.db_connection import get_connection


# -------------------------------
# Pydantic models aligned to your Postgres schema
# -------------------------------
class ListingBase(BaseModel):
    url: str
    website: str
    title: Optional[str] = None
    price: Optional[Decimal] = None
    currency: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
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
    post_date: Optional[datetime] = None


class ListingCreate(ListingBase):
    ad_id: str


class Listing(ListingBase):
    ad_id: str


class ListingSearch(BaseModel):
    brand: Optional[str] = None
    model: Optional[str] = None
    min_year: Optional[int] = None
    max_year: Optional[int] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    location_city: Optional[str] = None


# -------------------------------
# FastAPI application
# -------------------------------
app = FastAPI(
    title="Markaba API",
    description="API for the Markaba car listings database",
    version="1.0.0"
)

# CORS (open to all origins for now – tighten in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
def root():
    return {"message": "Welcome to the Markaba API!"}


@app.get("/listings", response_model=List[Listing], tags=["Listings"])
def get_all_listings(limit: int = Query(100, ge=1, le=1000)):
    conn = get_connection()
    if not conn:
        raise HTTPException(500, "Database connection failed")
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM listings LIMIT %s", (limit,))
        return cur.fetchall()
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        cur.close()
        conn.close()


@app.get("/listings/{ad_id}", response_model=Listing, tags=["Listings"])
def get_listing_by_id(ad_id: str):
    conn = get_connection()
    if not conn:
        raise HTTPException(500, "Database connection failed")
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM listings WHERE ad_id = %s", (ad_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Listing not found")
        return row
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        cur.close()
        conn.close()


@app.post("/search", response_model=List[Listing], tags=["Search"])
def search_listings(search_params: ListingSearch):
    conn = get_connection()
    if not conn:
        raise HTTPException(500, "Database connection failed")
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        clauses: List[str] = []
        params: List = []

        if search_params.brand:
            clauses.append("brand ILIKE %s")
            params.append(f"%{search_params.brand}%")
        if search_params.model:
            clauses.append("model ILIKE %s")
            params.append(f"%{search_params.model}%")
        if search_params.min_year is not None:
            clauses.append("year >= %s")
            params.append(search_params.min_year)
        if search_params.max_year is not None:
            clauses.append("year <= %s")
            params.append(search_params.max_year)
        if search_params.min_price is not None:
            clauses.append("price >= %s")
            params.append(search_params.min_price)
        if search_params.max_price is not None:
            clauses.append("price <= %s")
            params.append(search_params.max_price)
        if search_params.location_city:
            clauses.append("location_city ILIKE %s")
            params.append(f"%{search_params.location_city}%")

        where_clause = " AND ".join(clauses) if clauses else "TRUE"
        query = f"SELECT * FROM listings WHERE {where_clause}"
        cur.execute(query, tuple(params))
        return cur.fetchall()
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        cur.close()
        conn.close()


@app.get("/brands", response_model=List[str], tags=["Listings"])
def get_all_brands():
    conn = get_connection()
    if not conn:
        raise HTTPException(500, "Database connection failed")
    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT brand FROM listings ORDER BY brand")
        return [r[0] for r in cur.fetchall()]
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        cur.close()
        conn.close()


@app.get("/models/{brand}", response_model=List[str], tags=["Listings"])
def get_models_by_brand(brand: str):
    conn = get_connection()
    if not conn:
        raise HTTPException(500, "Database connection failed")
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT DISTINCT model FROM listings WHERE brand ILIKE %s ORDER BY model",
            (f"%{brand}%",)
        )
        return [r[0] for r in cur.fetchall()]
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        cur.close()
        conn.close()


@app.get("/years", response_model=List[int], tags=["Listings"])
def get_all_years():
    conn = get_connection()
    if not conn:
        raise HTTPException(500, "Database connection failed")
    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT year FROM listings ORDER BY year DESC")
        return [r[0] for r in cur.fetchall()]
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        cur.close()
        conn.close()


@app.get("/locations", response_model=List[str], tags=["Listings"])
def get_all_locations():
    conn = get_connection()
    if not conn:
        raise HTTPException(500, "Database connection failed")
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT DISTINCT location_city FROM listings WHERE location_city IS NOT NULL ORDER BY location_city"
        )
        return [r[0] for r in cur.fetchall()]
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        cur.close()
        conn.close()


@app.get("/stats/price_range", tags=["Stats"])
def get_price_range():
    conn = get_connection()
    if not conn:
        raise HTTPException(500, "Database connection failed")
    try:
        cur = conn.cursor()
        cur.execute("SELECT MIN(price), MAX(price) FROM listings")
        min_price, max_price = cur.fetchone()
        return {"min_price": min_price, "max_price": max_price}
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        cur.close()
        conn.close()


@app.get("/stats/count_by_brand", tags=["Stats"])
def get_count_by_brand():
    conn = get_connection()
    if not conn:
        raise HTTPException(500, "Database connection failed")
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT brand, COUNT(*) FROM listings GROUP BY brand ORDER BY COUNT(*) DESC"
        )
        return [{"brand": row[0], "count": row[1]} for row in cur.fetchall()]
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        cur.close()
        conn.close()


@app.post("/listings", response_model=Listing, status_code=201, tags=["Listings"])
def create_listing(listing: ListingCreate):
    conn = get_connection()
    if not conn:
        raise HTTPException(500, "Database connection failed")
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        query = f"""
            INSERT INTO listings (
                ad_id, url, website, title, price,
                currency, brand, model, year, mileage,
                mileage_unit, fuel_type, transmission_type,
                body_type, condition, color, seller,
                seller_type, location_city, location_region,
                image_url, number_of_images, post_date
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s
            ) RETURNING *
        """
        params = (
            listing.ad_id, listing.url, listing.website, listing.title,
            listing.price, listing.currency, listing.brand, listing.model,
            listing.year, listing.mileage, listing.mileage_unit,
            listing.fuel_type, listing.transmission_type,
            listing.body_type, listing.condition, listing.color,
            listing.seller, listing.seller_type,
            listing.location_city, listing.location_region,
            listing.image_url, listing.number_of_images,
            listing.post_date
        )
        cur.execute(query, params)
        new = cur.fetchone()
        conn.commit()
        return new
    except Exception as e:
        conn.rollback()
        raise HTTPException(500, f"Error creating listing: {e}")
    finally:
        cur.close()
        conn.close()
