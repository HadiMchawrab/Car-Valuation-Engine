from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from psycopg2.extras import RealDictCursor
from database_connection_service.db_connection import get_connection
from database_connection_service.classes_input import *
from typing import List
import os

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

@app.get("/")
def root():
    return {"message": "Welcome to the Markaba API!"}


@app.get("/listings", response_model=List[Listing])
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


@app.get("/listings/{listing_id}", response_model=Listing)
def get_listing_by_id(listing_id: int):
    conn = get_connection()
    if not conn:
        raise HTTPException(500, "Database connection failed")
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM listings WHERE id = %s", (listing_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Listing not found")
        return row
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        cur.close()
        conn.close()


@app.post("/search", response_model=List[Listing])
def search_listings(search_params: ListingSearch):
    conn = get_connection()
    if not conn:
        raise HTTPException(500, "Database connection failed")
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        clauses, params = [], []
        if search_params.make:
            clauses.append("make ILIKE %s")
            params.append(f"%{search_params.make}%")
        if search_params.model:
            clauses.append("model ILIKE %s")
            params.append(f"%{search_params.model}%")
        if search_params.min_year:
            clauses.append("year_ >= %s")
            params.append(search_params.min_year)
        if search_params.max_year:
            clauses.append("year_ <= %s")
            params.append(search_params.max_year)
        if search_params.min_price:
            clauses.append("price >= %s")
            params.append(search_params.min_price)
        if search_params.max_price:
            clauses.append("price <= %s")
            params.append(search_params.max_price)
        if search_params.location:
            clauses.append("loc ILIKE %s")
            params.append(f"%{search_params.location}%")

        where = " AND ".join(clauses) or "TRUE"
        query = f"SELECT * FROM listings WHERE {where}"
        cur.execute(query, tuple(params))
        return cur.fetchall()
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        cur.close()
        conn.close()


@app.get("/makes", response_model=List[str])
def get_all_makes():
    conn = get_connection()
    if not conn:
        raise HTTPException(500, "DB connection failed")
    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT make FROM listings ORDER BY make")
        return [r[0] for r in cur.fetchall()]
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        cur.close()
        conn.close()


@app.get("/models/{make}", response_model=List[str])
def get_models_by_make(make: str):
    conn = get_connection()
    if not conn:
        raise HTTPException(500, "DB connection failed")
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT DISTINCT model FROM listings WHERE make ILIKE %s ORDER BY model",
            (f"%{make}%",)
        )
        return [r[0] for r in cur.fetchall()]
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        cur.close()
        conn.close()


@app.get("/years", response_model=List[int])
def get_all_years():
    conn = get_connection()
    if not conn:
        raise HTTPException(500, "DB connection failed")
    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT year_ FROM listings ORDER BY year_ DESC")
        return [r[0] for r in cur.fetchall()]
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        cur.close()
        conn.close()


@app.get("/locations", response_model=List[str])
def get_all_locations():
    conn = get_connection()
    if not conn:
        raise HTTPException(500, "DB connection failed")
    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT loc FROM listings WHERE loc IS NOT NULL ORDER BY loc")
        return [r[0] for r in cur.fetchall()]
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        cur.close()
        conn.close()


@app.get("/stats/price_range")
def get_price_range():
    conn = get_connection()
    if not conn:
        raise HTTPException(500, "DB connection failed")
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


@app.get("/stats/count_by_make")
def get_count_by_make():
    conn = get_connection()
    if not conn:
        raise HTTPException(500, "DB connection failed")
    try:
        cur = conn.cursor()
        cur.execute("SELECT make, COUNT(*) FROM listings GROUP BY make ORDER BY COUNT(*) DESC")
        return [{"make": row[0], "count": row[1]} for row in cur.fetchall()]
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        cur.close()
        conn.close()


@app.post("/listings", response_model=Listing, status_code=201)
def create_listing(listing: ListingCreate):
    conn = get_connection()
    if not conn:
        raise HTTPException(500, "DB connection failed")
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        query = """
            INSERT INTO listings (
                website, web_url, title, kilometers, price,
                currency, year_oM, make, model, loc, created_at, image_urls
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        params = (
            listing.website, listing.web_url, listing.title,
            listing.kilometers, listing.price, listing.currency,
            listing.year_oM, listing.make, listing.model,
            listing.loc, listing.created_at, listing.image_urls
        )
        cur.execute(query, params)
        new_id = cur.fetchone()["id"]
        conn.commit()
        return {**listing.dict(), "id": new_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(500, f"Error creating listing: {e}")
    finally:
        cur.close()
        conn.close()
