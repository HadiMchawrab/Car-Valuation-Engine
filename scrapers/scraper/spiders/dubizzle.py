from __future__ import annotations

import datetime as _dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

import scrapy
from scrapy.crawler import CrawlerProcess


# Optional dependency: python‑dateutil (improves date parsing)

try:
    import dateutil.parser 

    HAS_DATEUTIL = True
except ImportError:
    HAS_DATEUTIL = False
    print(
        "Warning: python‑dateutil package not found. Date parsing will be limited.\n"
        "Consider installing with: pip install python‑dateutil"
    )

# Link Spider – collects advertisement URLs

class DubizzleLinkSpider(scrapy.Spider):
    """Crawl car listings pages and record every unique ad link."""

    name = "dubizzle_link_spider"
    base_url = "https://www.dubizzle.sa/en/vehicles/cars-for-sale/"

    # Initialisation
    def __init__(self, max_pages: int = 5, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.max_pages: int = int(max_pages)
        self.ad_links: Set[str] = set()


    # Requests pipeline
    def start_requests(self):
        # Page 1
        yield scrapy.Request(url=self.base_url, callback=self.parse)

        # Subsequent pages – ?page=2,3,…
        for page in range(2, self.max_pages + 1):
            page_url = f"{self.base_url}?page={page}"
            self.logger.info("Adding page to queue: %s", page_url)
            yield scrapy.Request(url=page_url, callback=self.parse)


    # Parse listing page – extract /ad/ links

    def parse(self, response: scrapy.http.Response):
        current_page = response.url.split("page=")[-1] if "page=" in response.url else "1"
        self.logger.info("Processing page %s", current_page)

        links_found = 0
        for href in response.css("a::attr(href)").getall():
            if href and "/ad/" in href:
                url = response.urljoin(href)
                if url not in self.ad_links:
                    self.ad_links.add(url)
                    links_found += 1
                    self.logger.info("Found ad link on page %s: %s", current_page, url)
                    yield {"ad_link": url}

        self.logger.info(
            "Found %d new links on page %s (total unique: %d)",
            links_found,
            current_page,
            len(self.ad_links),
        )



# Detail Spider – extract metadata from each advertisement page

class DubizzleDetailSpider(scrapy.Spider):
    """Visit saved ad URLs and scrape detailed fields."""

    name = "dubizzle_detail_spider"


    def __init__(self, links_file: str | None = None, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        links: List[str] = []
        if links_file:
            try:
                with open(links_file, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                    links = [item["ad_link"] for item in data] if isinstance(data[0], dict) else data
            except (FileNotFoundError, json.JSONDecodeError, IndexError) as exc:
                self.logger.error("Error loading links file '%s': %s", links_file, exc)

        self.start_urls: List[str] = links


    def start_requests(self):
        total = len(self.start_urls)
        for idx, url in enumerate(self.start_urls, start=1):
            self.logger.info("Processing link %d/%d: %s", idx, total, url)
            yield scrapy.Request(url, callback=self.parse, meta={"url": url})


    @staticmethod
    def _scrape_text(response: scrapy.http.Response, xpath_expr: str) -> str | None:
        """Helper – get and clean a single text node via XPath."""
        value = response.xpath(xpath_expr).get()
        return value.strip() if value else None


    def parse(self, response: scrapy.http.Response) -> Dict[str, Any]:
        ad: Dict[str, Any] = {
            "url": response.meta.get("url"),
            "image_url": None,
            "title": None,
            "price": None,
            "currency": None,
            "cost": None,
            "location": None,
            "seller_name": None,
            "creation_date": None,
            "time_created": None,
            "kilometers": None,
            "condition": None,
            "year": None,
            "fuel_type": None,
            "transmission_type": None,
            "brand": None,
            "body_type": None,
            "model": None,
            "color": None,
            "description": None,
        }


        # Basic details (image, title, price)

        try:
            ad["image_url"] = response.css("img[role='presentation'][aria-label='Cover photo']::attr(src)").get()
            title = response.css("h1::text").get()
            ad["title"] = title.strip() if title else None

            price_text = (
                response.xpath("//span[@aria-label='Price']/text()").get()
                or response.xpath("//span[contains(text(), 'USD')]/text()").get()
            )
            if price_text:
                ad["price"] = price_text.strip()
                # Split into currency / cost (handles "34,000 SR" and "SR 34,000")
                m = re.match(r"([^\d,]+)\s*([\d,]+)", price_text) or re.match(r"([\d,]+)\s*([^\d,]+)", price_text)
                if m:
                    first, second = m.groups()
                    if first.replace(",", "").isdigit():
                        ad["cost"], ad["currency"] = first.strip(), second.strip()
                    else:
                        ad["currency"], ad["cost"] = first.strip(), second.strip()
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Error extracting basic details: %s", exc)        # Location (from window.dataLayer JSON inside <script>)

        try:
            script_with_datalayer = response.xpath(
                "//script[contains(text(), 'window[\'dataLayer\']') and contains(text(), 'loc_name')]"
            ).get()
            
            if script_with_datalayer:
                loc_name_match = re.search(r'"loc_name"\s*:\s*"([^"]+)"', script_with_datalayer)
                loc_1_name_match = re.search(r'"loc_1_name"\s*:\s*"([^"]+)"', script_with_datalayer)
                
                loc_name = loc_name_match.group(1) if loc_name_match else ""
                loc_1_name = loc_1_name_match.group(1) if loc_1_name_match else ""
                
                if loc_name and loc_1_name:
                    ad["location"] = f"{loc_name}, {loc_1_name}"
                elif loc_name:
                    ad["location"] = loc_name
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Error extracting location: %s", exc)


        # Seller

        try:
            seller = response.xpath(
                "//div[./span[contains(text(), 'Member since')]]/preceding-sibling::div[1]/span/text()"
            ).get()
            ad["seller_name"] = seller.strip() if seller else None
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Error extracting seller name: %s", exc)


        # Creation date – relative → absolute ISO‑timestamp

        try:
            creation_raw = (
                response.xpath("//span[@aria-label='Creation date']/following-sibling::span/text()").get()
                or response.xpath(
                    "//span[contains(text(), 'days ago') or contains(text(), 'hour ago') or contains(text(), 'day ago') or "
                    "contains(text(), 'hours ago') or contains(text(), 'minute ago') or contains(text(), 'minutes ago') or "
                    "contains(text(), 'now')]/text()"
                ).get()
                or response.xpath("//span[text()='Posted:']/following-sibling::span/text()").get()
            )

            if creation_raw:
                creation_raw = creation_raw.strip()
                ad["creation_date"] = creation_raw
                now = _dt.datetime.now()

                # Relative patterns
                rel_patterns = {
                    "days": re.search(r"(\d+)\s*days?\s*ago", creation_raw, re.I),
                    "hours": re.search(r"(\d+)\s*hours?\s*ago", creation_raw, re.I),
                    "minutes": re.search(r"(\d+)\s*minutes?\s*ago", creation_raw, re.I),
                    "yesterday": re.search(r"yesterday|1\s*day\s*ago", creation_raw, re.I),
                }

                if rel_patterns["days"]:
                    ad["time_created"] = (now - _dt.timedelta(days=int(rel_patterns["days"].group(1)))).isoformat()
                elif rel_patterns["hours"]:
                    ad["time_created"] = (now - _dt.timedelta(hours=int(rel_patterns["hours"].group(1)))).isoformat()
                elif rel_patterns["minutes"]:
                    ad["time_created"] = (now - _dt.timedelta(minutes=int(rel_patterns["minutes"].group(1)))).isoformat()
                elif rel_patterns["yesterday"]:
                    ad["time_created"] = (now - _dt.timedelta(days=1)).isoformat()
                elif any(term in creation_raw.lower() for term in ("few seconds", "just now", "now")):
                    ad["time_created"] = now.isoformat()
                else:
                    # Absolute date parsing
                    if HAS_DATEUTIL:
                        try:
                            ad["time_created"] = dateutil.parser.parse(creation_raw).isoformat()
                        except Exception:  # noqa: BLE001
                            self.logger.warning("Could not parse creation date: %s", creation_raw)
                    else:
                        for fmt in ("%d %b %Y", "%d %B %Y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
                            try:
                                ad["time_created"] = _dt.datetime.strptime(creation_raw, fmt).isoformat()
                                break
                            except ValueError:
                                continue
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Error extracting creation date: %s", exc)

        # Structured attributes (kilometers, condition, …)

        attributes = {
            "kilometers": "Kilometers",
            "condition": "Condition",
            "year": "Year",
            "fuel_type": "Fuel Type",
            "transmission_type": "Transmission Type",
            "brand": "Brand",
            "body_type": "Body Type",
            "model": "Model",
            "color": "Color",
        }
        for key, label in attributes.items():
            try:
                val = self._scrape_text(response, f"//span[contains(text(), '{label}')]/following-sibling::span/text()")
                if val:
                    ad[key] = val
            except Exception:  # noqa: BLE001
                pass

        # Description – best‑effort extraction

        try:
            description = (
                response.xpath(
                    "//div[@aria-label='Description']/div[contains(@class, 'e0e9974e')]/div[contains(@class, '_472fbef')]//span/text()"
                ).get()
                or response.xpath("//div[@aria-label='Description']//span/text()").get()
                or response.css("div._472fbef span::text").get()
            )
            if not description:
                paras = [p.strip() for p in response.xpath("//p/text()").getall() if p.strip()]
                description = " ".join(paras) if paras else None
            ad["description"] = description.strip() if description else None
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Error extracting description: %s", exc)

        return ad


# Orchestrator helper – run link spider then detail spider

def run_scraper(max_pages: int = 5):  # noqa: D401 – simple helper
    """Run the two‑phase crawler (link collection ➜ detail extraction)."""

    links_file = "links.json"
    details_file = "All_Info.json"



    # Phase 1 – collect links

    link_settings: Dict[str, Any] = {
        "USER_AGENT": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        ),
        "LOG_LEVEL": "INFO",
        "COOKIES_ENABLED": False,
        "CONCURRENT_REQUESTS": 8,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 8,
        "DOWNLOAD_DELAY": 0.5,
        "FEEDS": {links_file: {"format": "json", "overwrite": True}},
    }

    process = CrawlerProcess(settings=link_settings)
    process.crawl(DubizzleLinkSpider, max_pages=max_pages)
    process.start()

    # Get number of links
    links_count = 0
    if Path(links_file).exists():
        with open(links_file, "r", encoding="utf-8") as fh:
            links_count = len(json.load(fh))
    print(f"\nTotal unique ad links found: {links_count}")

    # Phase 2 – scrape details (separate Scrapy process)
    print("\nStarting detail scraper in a new process…")
    python_exe = sys.executable
    subprocess.call([python_exe, os.path.abspath(__file__), "details"])





if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "details":
        # --------------------------------------------------------------
        # Detail‑only run (invoked by run_scraper)
        # --------------------------------------------------------------
        details_file = "All_Info.json"
        links_file = "links.json"

        detail_settings: Dict[str, Any] = {
            "USER_AGENT": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            ),
            "LOG_LEVEL": "INFO",
            "COOKIES_ENABLED": False,
            "CONCURRENT_REQUESTS": 8,
            "CONCURRENT_REQUESTS_PER_DOMAIN": 8,
            "DOWNLOAD_DELAY": 1,
            "DOWNLOADER_MIDDLEWARES": {"scrapy.downloadermiddlewares.retry.RetryMiddleware": 90},
            "RETRY_TIMES": 3,
            "RETRY_HTTP_CODES": [500, 502, 503, 504, 408, 429],
            "FEEDS": {
                details_file: {"format": "json", "overwrite": True, "encoding": "utf-8", "indent": 4}
            },
        }

        process = CrawlerProcess(settings=detail_settings)
        process.crawl(DubizzleDetailSpider, links_file=links_file)
        process.start()

        # Summary statistics
        links_total = details_total = 0
        if Path(links_file).exists():
            with open(links_file, "r", encoding="utf-8") as fh:
                links_total = len(json.load(fh))
        if Path("All_Info.json").exists():
            with open("All_Info.json", "r", encoding="utf-8") as fh:
                details_total = len(json.load(fh))
        print(f"Completed scraping {details_total} ads out of {links_total}")

    elif len(sys.argv) > 1 and sys.argv[1].isdigit():
        run_scraper(max_pages=int(sys.argv[1]))
    else:
        run_scraper()