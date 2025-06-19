import json
import scrapy
from scrapy.crawler import CrawlerProcess
from pathlib import Path
import sys
import os
import subprocess


class DubizzleLinkSpider(scrapy.Spider):
    name = 'dubizzle_link_spider'
    base_url = 'https://www.dubizzle.sa/en/vehicles/cars-for-sale/'
    
    def __init__(self, max_pages=5, *args, **kwargs):
        super(DubizzleLinkSpider, self).__init__(*args, **kwargs)
        self.ad_links = set()
        self.max_pages = int(max_pages)
        
    def start_requests(self):        
        yield scrapy.Request(url=self.base_url, callback=self.parse)
        for page in range(2, self.max_pages + 1):
            page_url = f"{self.base_url}?page={page}"
            self.logger.info(f"Adding page to queue: {page_url}")
            yield scrapy.Request(url=page_url, callback=self.parse)
    
    def parse(self, response):
        current_page = "1"      
        if "page=" in response.url:
            current_page = response.url.split("page=")[1].split("&")[0]
        
        self.logger.info(f"Processing page {current_page}")
        
        links_found_on_page = 0
        for link in response.css('a::attr(href)').getall():
            if link and '/ad/' in link:
                full_url = response.urljoin(link)
                if full_url not in self.ad_links:
                    self.ad_links.add(full_url)
                    links_found_on_page += 1
                    self.logger.info(f"Found ad link on page {current_page}: {full_url}")
                    yield {'ad_link': full_url}
        
        self.logger.info(f"Found {links_found_on_page} new links on page {current_page}")
        self.logger.info(f"Running total: {len(self.ad_links)} unique ad links found so far")


class DubizzleDetailSpider(scrapy.Spider):
    name = 'dubizzle_detail_spider'
    
    def __init__(self, links_file=None, *args, **kwargs):
        super(DubizzleDetailSpider, self).__init__(*args, **kwargs)
        links = []
        try:
            with open(links_file, 'r') as f:
                data = json.load(f)
                links = [item['ad_link'] for item in data] if isinstance(data[0], dict) else data
        except (FileNotFoundError, json.JSONDecodeError, IndexError) as e:
            self.logger.error(f"Error loading links file: {e}")
        
        self.start_urls = links
    
    def start_requests(self):
        total = len(self.start_urls)
        for idx, url in enumerate(self.start_urls):
            self.logger.info(f"Processing link {idx+1}/{total}: {url}")
            yield scrapy.Request(url, callback=self.parse, meta={'url': url})
    
    def parse(self, response):
        ad_details = {
            "url": response.meta.get('url'),
            "image_url": None,
            "title": None,
            "price": None,
            "location": None,
            "seller_name": None,
            "creation_date": None,
            "kilometers": None,
            "condition": None,
            "year": None,
            "fuel_type": None,
            "transmission_type": None,
            "brand": None,
            "body_type": None,
            "seller_type": None,
            "model": None,
            "color": None,
            "description": None
        }
        try:
            image = response.css("img[role='presentation'][aria-label='Cover photo']::attr(src)").get()
            if image:
                ad_details["image_url"] = image
                
            title = response.css("h1::text").get()
            if title:
                ad_details["title"] = title.strip()
            price = response.xpath("//span[@aria-label='Price']/text()").get()
              # Fallback to other methods if not found
            if not price:
                price = response.xpath("//span[contains(text(), 'USD')]/text()").get()
            
            if price:
                ad_details["price"] = price.strip()
        except Exception as e:
            self.logger.error(f"Error extracting basic details: {e}")
          # Extract location
        try:
            location = (
                response.xpath("//div[@aria-label='Location']//div[contains(@class, '_1ee53078') and contains(normalize-space(), ',') and string-length(normalize-space()) > 3]/text()").get() or

                response.xpath("//div[@aria-label='Location']//div[not(*) and contains(normalize-space(), ',') and string-length(normalize-space()) > 3]/text()").get() or
                
                response.xpath("""
                    //div[@aria-label='Description']/following-sibling::div[@aria-label='Location']
                        [descendant::img[@alt='Map placeholder']]
                        //div[
                            not(*) and 
                            contains(normalize-space(), ',') and 
                            string-length(normalize-space()) > 3
                        ][1]/text()
                """).get()
            )
            
            if location:
                ad_details["location"] = location.strip()
        except Exception as e:
            self.logger.error(f"Error extracting location: {e}")
            location = None
            
        # Extract seller name
        try:
            # Try to find seller name using the structure you described
            seller = response.xpath("//div[./span[contains(text(), 'Member since')]]/preceding-sibling::div[1]/span/text()").get()
                
            if seller:
                ad_details["seller_name"] = seller.strip()
        except Exception as e:
            self.logger.error(f"Error extracting seller name: {e}")
        
        # Extract creation date
        try:
            creation_date = (
                response.xpath("//span[@aria-label='Creation date']/following-sibling::span/text()").get() or
                response.xpath("//span[contains(text(), 'days ago') or contains(text(), 'hour ago') or contains(text(), 'day ago') or contains(text(), 'hours ago') or contains(text(), 'minute ago') or contains(text(), 'now') or contains(text(), 'minutes ago')]/text()").get() or
                response.xpath("//span[text()='Posted:']/following-sibling::span/text()").get()
            )
            if creation_date:
                ad_details["creation_date"] = creation_date.strip()
        except Exception as e:
            self.logger.error(f"Error extracting creation date: {e}")
        
        # Extract various attributes using a helper function
        attributes = [
            ("kilometers", "Kilometers"),
            ("condition", "Condition"),
            ("year", "Year"),
            ("fuel_type", "Fuel Type"),
            ("transmission_type", "Transmission Type"),
            ("brand", "Brand"),
            ("body_type", "Body Type"),
            ("model", "Model"),
            ("color", "Color")
        ]
        
        for attr_key, attr_label in attributes:
            try:
                value = response.xpath(f"//span[contains(text(), '{attr_label}')]/following-sibling::span/text()").get()
                if value:
                    ad_details[attr_key] = value.strip()
            except Exception:
                pass
        
        # Extract description
        try:
            description = (
                response.xpath("//div[@aria-label='Description']/div[contains(@class, 'e0e9974e')]/div[contains(@class, '_472fbef')]//span/text()").get() or
                response.xpath("//div[@aria-label='Description']//span/text()").get() or
                response.css("div._472fbef span::text").get()
            )
            
            if not description:
                # Try to find larger text blocks that might contain the description
                desc_paragraphs = response.xpath("//p/text()").getall()
                if desc_paragraphs:
                    # Join paragraphs with spaces
                    description = ' '.join([p.strip() for p in desc_paragraphs if len(p.strip()) > 0])
            
            if description:
                ad_details["description"] = description.strip()
        except Exception as e:
            self.logger.error(f"Error extracting description: {e}")
            
        return ad_details


def run_scraper(max_pages=1):
    """Run the complete scraper"""
    links_file = 'links.json'
    details_file = 'All_Info.json'
    settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'LOG_LEVEL': 'INFO',
        'COOKIES_ENABLED': False,
        'CONCURRENT_REQUESTS': 8,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 8,
        'DOWNLOAD_DELAY': 0.5,
    }
    
    process = CrawlerProcess(settings={
        **settings,
        'FEEDS': {
            links_file: {
                'format': 'json',
                'overwrite': True,
            },
        },
    })
    
    process.crawl(DubizzleLinkSpider, max_pages=max_pages)
    process.start()
    
    links_count = 0
    if Path(links_file).exists():
        with open(links_file, 'r') as f:
            data = json.load(f)
            links_count = len(data)
    
    print(f"\nTotal unique ad links found: {links_count}")
    
    print("\nStarting detail scraper in a new process...")
    python_executable = sys.executable
    script_path = os.path.abspath(__file__)
    subprocess.call([python_executable, script_path, 'details'])


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == 'details':
            details_file = 'All_Info.json'
            links_file = 'links.json'
            settings = {
                'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'LOG_LEVEL': 'INFO',
                'COOKIES_ENABLED': False,
                'CONCURRENT_REQUESTS': 8,
                'CONCURRENT_REQUESTS_PER_DOMAIN': 8,
                'DOWNLOAD_DELAY': 1,
                'DOWNLOADER_MIDDLEWARES': {
                    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,
                },
                'RETRY_TIMES': 3,
                'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429],
                'FEEDS': {
                    details_file: {
                        'format': 'json',
                        'overwrite': True,
                        'encoding': 'utf-8',
                        'indent': 4,
                    },
                },
            }
            
            process = CrawlerProcess(settings=settings)
            process.crawl(DubizzleDetailSpider, links_file=links_file)
            process.start()
            
            details_count = links_count = 0
            
            if Path(details_file).exists():
                with open(details_file, 'r', encoding='utf-8') as f:
                    details_count = len(json.load(f))
            
            if Path(links_file).exists():
                with open(links_file, 'r') as f:
                    links_count = len(json.load(f))
            
            print(f"Completed scraping {details_count} ads out of {links_count}")
        elif sys.argv[1].isdigit():
            run_scraper(max_pages=int(sys.argv[1]))
        else:
            print("Usage:")
            print("  python main.py                  - Run scraper (5 pages)")
            print("  python main.py <number>         - Run with specified number of pages")
    else:
        run_scraper()
