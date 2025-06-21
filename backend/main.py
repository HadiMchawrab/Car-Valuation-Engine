from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from database_connection_service.db_connection import get_connection
from database_connection_service.classes_input import *
from typing import List, Optional
import os

app = FastAPI(title="Markaba API", 
              description="API for the Markaba car listings database",
              version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to restrict origins in production
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods, including OPTIONS
    allow_headers=["*"],
)

@app.get("/")
def root():
    """
    Root endpoint that returns a welcome message.
    """
    return {"message": "Welcome to the Markaba API!"}

@app.get("/listings", response_model=List[Listing])
def get_all_listings(limit: int = Query(100, ge=1, le=1000)):
    """
    Get all car listings with pagination.
    """
    connection = get_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM listings LIMIT {limit}")
        columns = [desc[0] for desc in cursor.description]
        listings = []
        for row in cursor.fetchall():
            listing = dict(zip(columns, row))
            # Convert column names to match the model (removing underscores)
            listings.append(listing)
        return listings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()

@app.get("/listings/{listing_id}", response_model=Listing)
def get_listing_by_id(listing_id: int):
    """
    Get a specific car listing by its ID.
    """
    connection = get_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM listings WHERE id = %s", (listing_id,))
        columns = [desc[0] for desc in cursor.description]
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Listing not found")
        
        listing = dict(zip(columns, row))
        # Convert column names to match the model (removing underscores)
        return listing
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()

@app.post("/search", response_model=List[Listing])
def search_listings(search_params: ListingSearch):
    """
    Search for car listings based on various criteria.
    """
    connection = get_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cursor = connection.cursor()
        
        # Build the dynamic query
        query = "SELECT * FROM listings WHERE 1=1"
        params = []
        
        if search_params.make:
            query += " AND make LIKE %s"
            params.append(f"%{search_params.make}%")
        
        if search_params.model:
            query += " AND model LIKE %s"
            params.append(f"%{search_params.model}%")
        
        if search_params.min_year:
            query += " AND year_ >= %s"
            params.append(search_params.min_year)
        
        if search_params.max_year:
            query += " AND year_ <= %s"
            params.append(search_params.max_year)
        
        if search_params.min_price:
            query += " AND price >= %s"
            params.append(search_params.min_price)
        
        if search_params.max_price:
            query += " AND price <= %s"
            params.append(search_params.max_price)
        
        if search_params.location:
            query += " AND loc LIKE %s"
            params.append(f"%{search_params.location}%")
        
        cursor.execute(query, tuple(params))
        columns = [desc[0] for desc in cursor.description]
        listings = []
        
        for row in cursor.fetchall():
            listing = dict(zip(columns, row))
            # Convert column names to match the model (removing underscores)
            listings.append(listing)
        
        return listings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()

@app.get("/makes", response_model=List[str])
def get_all_makes():
    """
    Get a list of all car makes in the database.
    """
    connection = get_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT make FROM listings ORDER BY make")
        makes = [row[0] for row in cursor.fetchall()]
        return makes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()

@app.get("/models/{make}", response_model=List[str])
def get_models_by_make(make: str):
    """
    Get a list of all car models for a specific make.
    """
    connection = get_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT model FROM listings WHERE make LIKE %s ORDER BY model", (f"%{make}%",))
        models = [row[0] for row in cursor.fetchall()]
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()

@app.get("/years", response_model=List[int])
def get_all_years():
    """
    Get a list of all car years in the database, ordered newest to oldest.
    """
    connection = get_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT year_ FROM listings ORDER BY year_ DESC")
        years = [row[0] for row in cursor.fetchall()]
        return years
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()

@app.get("/locations", response_model=List[str])
def get_all_locations():
    """
    Get a list of all locations in the database.
    """
    connection = get_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT loc FROM listings WHERE loc IS NOT NULL ORDER BY loc")
        locations = [row[0] for row in cursor.fetchall()]
        return locations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()

@app.get("/stats/price_range")
def get_price_range():
    """
    Get the minimum and maximum prices in the database.
    """
    connection = get_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT MIN(price), MAX(price) FROM listings")
        min_price, max_price = cursor.fetchone()
        return {"min_price": min_price, "max_price": max_price}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()

@app.get("/stats/count_by_make")
def get_count_by_make():
    """
    Get the count of listings for each make.
    """
    connection = get_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT make, COUNT(*) as count FROM listings GROUP BY make ORDER BY count DESC")
        results = [{"make": row[0], "count": row[1]} for row in cursor.fetchall()]
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()

@app.post("/insert", response_model=Listing)
def insert_listing(listing: ListingCreate):
    """
    Insert a new car listing after checking for duplicates based on web_url.
    Returns the inserted listing with its generated ID.
    """
    connection = get_connection()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cursor = connection.cursor()
        
        # Check if a listing with the same web_url already exists
        cursor.execute("SELECT id FROM listings WHERE web_url = %s", (listing.web_url,))
        existing = cursor.fetchone()
        
        if existing:
            raise HTTPException(status_code=409, detail="Listing with this web_url already exists")
        
        # Prepare the insert query
        columns = ", ".join([
            "website", "web_url", "title", "kilometers", "price", 
            "currency", "year_oM", "make", "model", "loc", 
            "created_at", "image_urls"
        ])
        
        placeholders = ", ".join(["%s"] * 12)  # 12 fields to insert
        
        query = f"INSERT INTO listings ({columns}) VALUES ({placeholders})"
        
        # Prepare values for insertion
        values = (
            listing.website,
            listing.web_url,
            listing.title,
            listing.kilometers,
            listing.price,
            listing.currency,
            listing.year_oM,
            listing.make,
            listing.model,
            listing.loc,
            listing.created_at,
            listing.image_urls
        )
        
        cursor.execute(query, values)
        connection.commit()
        
        # Get the ID of the newly inserted record
        new_id = cursor.lastrowid
        
        # Return the complete listing with its ID
        return {**listing.model_dump(), "id": new_id}
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()
