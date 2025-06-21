# Scrapers Service

This directory contains web scrapers for collecting data from various sources.

## Running with Docker

You can run the scrapers using Docker:

```bash
# To build and run the scrapers service
docker-compose up scrapers

# To build and run in detached mode
docker-compose up -d scrapers

# To run with a specific command
docker-compose run scrapers scrapy crawl dubizzle
```

## Environment Setup

Make sure your `.env` file contains the necessary API keys:

```
SCRAPEOPS_API_KEY=your_api_key_here
```

## Output

The scraped data will be saved to the `./data` directory, which is mounted as a volume in the Docker container.

## Available Spiders

- `dubizzle`: Scrapes car listings from dubizzle.sa

To run a specific spider:

```bash
docker-compose run scrapers scrapy crawl dubizzle
```
