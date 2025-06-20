This application is designed to scrape multiple car websites, aggregate their listings, and display them on a unified platform. The backend uses Scrapy for web scraping and SQLite for the database. Flask is used for the frontend and dashboard.

Features:
- Scrape car listings from various websites using Scrapy
- Store data in a local SQLite database
- Display all cars, with comparison and filtering options (planned)

Setup Instructions:
1. Create a virtual environment:
    python -m venv venv

2. Activate the virtual environment:
    .\venv\Scripts\Activate

3. Install dependencies:
    pip install -r requirements.txt

4. Run the scraper:
    python main.py
    
    This will:
    - Extract ad links from Dubizzle
    - Save the links to a file named links.json
    - Print the number of unique links found

Note: The application now uses Scrapy instead of Selenium for more efficient web scraping.