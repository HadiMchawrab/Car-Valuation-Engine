import re
import json
import scrapy

from datetime import datetime
from scraper.items import DubizzleItem
from scrapy import Spider
from urllib.parse import urlparse, parse_qs

class DubizzleSpider(Spider):
    name = "dubizzle"
    allowed_domains = ["dubizzle.sa"]

    custom_settings = {
        "FEEDS": {"dubizzle.json": {"format": "json", "encoding": "utf8", "overwrite": True}},
        "COOKIES_ENABLED": True,
        "CONCURRENT_REQUESTS": 34,
        "CONCURRENT_REQUESTS_PER_IP": 8,
        "DOWNLOAD_DELAY": 1,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 0.5,
        "AUTOTHROTTLE_MAX_DELAY": 10,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 2.0,
        "RETRY_ENABLED": True,
        "RETRY_TIMES": 30,
        "RETRY_HTTP_CODES": [429, 500, 502, 503, 504, 408, 401, 403],
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.page_count = 0
        self.total_ads = 0

    def start_requests(self):
        # Begin at the first listings page
        yield scrapy.Request(
            url="https://www.dubizzle.sa/en/vehicles/cars-for-sale/?page=1",
            callback=self.parse_page,
            errback=self.errback_page
        )

    def parse_page(self, response):
        # Track page count and number
        self.page_count += 1
        qs = parse_qs(urlparse(response.url).query)
        current_page = int(qs.get('page', ['1'])[0])
        self.logger.info(f"[Progress] Scraping LISTINGS page {self.page_count} (#{current_page}): {response.url}")

        # Extract all ad URLs
        links = response.css('a[href*="/en/ad/"]::attr(href)').getall()
        self.logger.info(f"[Progress] Found {len(links)} ad links on page {current_page}")

        seen = set()
        for href in links:
            if href in seen:
                continue
            seen.add(href)
            yield response.follow(href, callback=self.parse_ad, errback=self.errback_ad)

        # Follow the "Next" button via the inner <div title="Next"> element
        next_href = response.xpath('//div[@title="Next"]/parent::a/@href').get()
        if next_href:
            yield response.follow(next_href, callback=self.parse_page, errback=self.errback_page)
        else:
            self.logger.info(f"[Progress] No more pages after {current_page}. Crawl complete.")

    def parse_ad(self, response):
        self.total_ads += 1
        self.logger.info(f"[Progress] Scraping AD #{self.total_ads}: {response.url}")

        item = DubizzleItem()
        raw_id = response.url.split('-ID')[-1].split('.')[0]
        item['ad_id'] = raw_id
        item['url']   = response.url
        item['website'] = 'Dubizzle'

        # JSON-LD fallback
        ld_txt = response.xpath("//script[@type='application/ld+json']/text()").get()
        try:
            schema = json.loads(ld_txt) if ld_txt else {}
        except json.JSONDecodeError:
            schema = {}

        preload = response.css("link[rel=preload][as=image]::attr(href)").get()
        og      = response.xpath("//meta[@property='og:image']/@content").get()
        ld_img  = schema.get('image') if isinstance(schema.get('image'), str) else None
        item['image_url'] = preload or og or ld_img

        def to_int(v):
            try: return int(float(v))
            except: return None

        item.update({
            'name': schema.get('name'),
            'sku': schema.get('sku'),
            'description': schema.get('description'),
            'price_valid_until': schema.get('priceValidUntil'),
            'fuel_type': schema.get('fuelType'),
            'image_urls': ([schema['image']] if isinstance(schema.get('image'), str) else schema.get('image', [])),
            'title': schema.get('name'),
            'brand': schema.get('brand'),
            'model': schema.get('model'),
            'year': to_int(schema.get('modelDate')),
            'color': schema.get('color'),
        })

        # DataLayer overrides
        dl = {}
        m = re.search(r"window\['dataLayer'\]\.push\((\{[\s\S]*?\})\)", response.text)
        if m:
            blob = re.sub(r',\s*([}\]])', r'\1', m.group(1))
            try: dl = json.loads(blob)
            except: pass

        def pick(*keys):
            for k in keys:
                v = dl.get(k)
                if v not in (None, "", []): return v

        item.update({
            'price': pick('price'),
            'currency': pick('currency_unit'),
            'condition': pick('ad_condition'),
            'new_used': pick('new_used'),
            'transmission_type': pick('transmission'),
            'mileage': pick('mileage'),
            'mileage_unit': dl.get('area_unit'),
            'body_type': pick('body_type'),
            'price_type': pick('price_type'),
            'seats': pick('seats'),
            'owners': pick('owners'),
            'interior': pick('interior'),
            'air_con': pick('air_con'),
            'deliverable': pick('deliverable'),
            'has_video': pick('video'),
            'has_panorama': pick('panorama'),
            'seller_type': pick('seller_type'),
            'seller_verified': pick('seller_verified'),
            'seller_id': pick('seller_id'),
            'agency_id': pick('agency_id', 'company_ids'),
            'agency_name': pick('agency_name'),
            'is_agent': pick('is_agent'),
            'location_city': pick('loc_name'),
            'location_region': pick('loc_2_name', 'loc_1_name'),
            'loc_id': pick('loc_id'),
            'loc_breadcrumb': pick('loc_breadcrumb'),
            'category_1_id': pick('category_1_id'),
            'category_1_name': pick('category_1_name'),
            'category_2_id': pick('category_2_id'),
            'category_2_name': pick('category_2_name'),
            'number_of_images': pick('number_of_photos'),
            'ownership_type': pick('ownership_type'),
            'page_type': pick('page_type')
        })

        # window.state timestamps
        state = {}
        m_s = re.search(r"window\.state\s*=\s*(\{[\s\S]*?\});", response.text)
        if m_s:
            raw = re.sub(r',\s*([}\]])', r'\1', m_s.group(1))
            try: state = json.loads(raw)
            except: pass

        ad_data = state.get('sellerProfile', {}).get('data', {})
        created = ad_data.get('createdAt')
        item['post_date'] = datetime.fromisoformat(created) if created else None
        item['seller'] = ad_data.get('name')

        def clean_doors(v):
            if not v: return None
            try:
                if '-' in v:
                    nums = [int(x) for x in v.split('-') if x.isdigit()]
                    return max(nums) if nums else None
                return int(v)
            except:
                return None
        item['doors'] = clean_doors(pick('doors'))

        yield item

    def closed(self, reason):
        self.logger.info(f"[Summary] Crawl finished: {self.page_count} pages scraped, {self.total_ads} ads scraped. Reason: {reason}")

    def errback_page(self, failure):
        self.logger.error(f"[Error] Page failed: {failure.request.url}")

    def errback_ad(self, failure):
        self.logger.error(f"[Error] Ad failed: {failure.request.url}")
