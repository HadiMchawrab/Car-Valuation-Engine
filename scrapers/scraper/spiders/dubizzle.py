import re
import json
import scrapy
from scraper.items import DubizzleItem

class DubizzleSpider(scrapy.Spider):
    name = "dubizzle"
    allowed_domains = ["dubizzle.sa"]
    # how many listing pages to crawl
    max_pages = 199

    custom_settings = {
        "FEEDS": {
            "dubizzle.json": {"format": "json", "encoding": "utf8", "overwrite": True},
        },
        "COOKIES_ENABLED": True,
        "CONCURRENT_REQUESTS": 32,
        "CONCURRENT_REQUESTS_PER_IP": 8,
        "DOWNLOAD_DELAY": 1,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 0.5,
        "AUTOTHROTTLE_MAX_DELAY": 10,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 2.0,
        "RETRY_ENABLED": True,
        "RETRY_TIMES": 8,
        "RETRY_HTTP_CODES": [429, 500, 502, 503, 504, 408, 401],
        "DOWNLOAD_HANDLERS": {
            "http":  "scrapy_impersonate.ImpersonateDownloadHandler",
            "https": "scrapy_impersonate.ImpersonateDownloadHandler",
        },
        "DOWNLOADER_MIDDLEWARES": {
            "scrapy_impersonate.ImpersonateDownloadHandler":        250,
            "scraper.middlewares.MixedHeadersRetryMiddleware":      300,
            "scraper.middlewares.FreeProxyMiddleware":              200,
            "scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware": 210,
            "scraper.middlewares.PageChangeLoggingMiddleware":      400,
            "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware":   None,
            "scrapy_user_agents.middlewares.RandomUserAgentMiddleware":     500,
        },
        "USER_AGENT": None,
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "IMPERSONATE_BROWSER": "firefox133",
        "BACKOFF_BASE_DELAY":   1.0,
        "BACKOFF_MAX_DELAY":    60.0,
        "BACKOFF_JITTER":       0.5,
        "HUMAN_THINK_CHANCE":   0.05,
        "HUMAN_THINK_MIN":      0.1,
        "HUMAN_THINK_MAX":      0.5,
    }

    def start_requests(self):
        """Generate one request per listing page up to max_pages."""
        for page in range(1, self.max_pages + 1):
            url = f"https://www.dubizzle.sa/en/vehicles/cars-for-sale/?page={page}"
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        """Parse a listings page: follow each unique ad link."""
        self.logger.info(f"[Page] scraping listings page: {response.url}")
        seen = set()
        for href in response.css('article a[href*="/en/ad/"]::attr(href)').getall():
            if href in seen:
                continue
            seen.add(href)
            yield response.follow(href, callback=self.parse_ad)

    def parse_ad(self, response):
        """Scrape the details of an individual ad."""
        self.logger.info(f"[Item] scraping ad {response.url}")
        item = DubizzleItem()

        # required core fields
        item['ad_id']         = response.url.split('-ID')[-1].split('.')[0]
        item['url']           = response.url
        item['image_url']     = response.css("img[role='presentation']::attr(src)").get()

        # JSON-LD extraction
        ld_txt = response.xpath("//script[@type='application/ld+json']/text()").get()
        try:
            schema = json.loads(ld_txt) if ld_txt else {}
        except json.JSONDecodeError:
            schema = {}

        def to_int(v):
            try: return int(float(v))
            except: return None

        item['title']   = schema.get('name')
        item['description'] = schema.get('description')
        offers = schema.get('offers') or []
        offer = offers[0] if isinstance(offers, list) and offers else {}
        item['price']      = offer.get('price')
        item['currency']   = offer.get('priceCurrency')
        od = schema.get('mileageFromOdometer') or {}
        item['kilometers'] = to_int(od.get('value'))
        item['brand']      = schema.get('brand')
        item['model']      = schema.get('model')
        item['year']       = schema.get('modelDate')
        imgs = schema.get('image')
        item['images']     = [imgs] if isinstance(imgs, str) else (imgs or [])

        # dataLayer fallback
        dl = {}
        m = re.search(r"window\['dataLayer'\]\.push\(\s*({.*?})\s*\);",
                      response.text, flags=re.DOTALL)
        if m:
            blob = re.sub(r",\s*([}\]])", r"\1", m.group(1))
            try:
                dl = json.loads(blob)
            except:
                dl = {}

        def pick(*keys):
            for k in keys:
                v = dl.get(k)
                if v not in (None, "", []):
                    return v

        item['cost']             = pick('cost')
        item['location']         = pick('loc_name', 'loc_1_name', 'loc_2_name')
        item['seller_type']      = pick('seller_type')
        item['time_created']     = pick('time_created')
        item['condition']        = pick('condition')
        item['new_used']         = pick('new_used')
        item['body_type']        = pick('body_type')
        item['fuel_type']        = pick('fuel_type')
        item['transmission_type']= pick('transmission_type', 'transmission')
        item['doors']            = pick('doors')
        item['seats']            = pick('seats')
        item['owners']           = pick('owners')
        item['color']            = pick('color')
        item['interior']         = pick('interior')
        item['air_con']          = pick('air_con')
        item['source']           = pick('source')

        yield item
