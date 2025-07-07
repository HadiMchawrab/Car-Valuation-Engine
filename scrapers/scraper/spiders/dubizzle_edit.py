import re
import json
from collections import deque
from datetime import datetime, timezone
from urllib.parse       import urlparse, parse_qs
from scrapy             import Spider, Request
from scrapy.exceptions  import CloseSpider
from scraper.items      import DubizzleItem



class DubizzleEditSpider(Spider):

    name = "dubizzle_edit"
    custom_settings = {
        "FEEDS": {
            "dubizzle_edit.json": {"format": "json", "encoding": "utf8", "overwrite": True}
        },
        "COOKIES_ENABLED": True,
        "CONCURRENT_REQUESTS": 34,
        "CONCURRENT_REQUESTS_PER_IP": 10,
        "DOWNLOAD_DELAY": 1,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 0.5,
        "AUTOTHROTTLE_MAX_DELAY": 10,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 2.0,
        "RETRY_ENABLED": True,
        "RETRY_TIMES": 36,
        "RETRY_HTTP_CODES": [429, 500, 502, 503, 504, 408, 401, 403],
        "DOWNLOAD_HANDLERS": {
            "http":  "scrapy_impersonate.ImpersonateDownloadHandler",
            "https": "scrapy_impersonate.ImpersonateDownloadHandler",
        },
        "DOWNLOADER_MIDDLEWARES": {
            "scrapy_impersonate.ImpersonateDownloadHandler":          250,
            "scraper.middlewares.MixedHeadersRetryMiddleware":        300,
            "scraper.middlewares.FreeProxyMiddleware":                200,
            "scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware": 210,
            "scraper.middlewares.PageChangeLoggingMiddleware":        400,
            "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware":   None,
            "scrapy_user_agents.middlewares.RandomUserAgentMiddleware":     500,
        },
        "ITEM_PIPELINES": {
            "scraper.pipelines.LoadAllURLsPipeline":      100,
            "scraper.pipelines.TrimInferencePipeline" : 200,
            "scraper.pipelines.DubizzlePostgresPipeline": 300,
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

    def __init__(self, name = None, **kwargs):
        super().__init__(name, **kwargs)
        self.urls = deque()
        self.link_no = 0;




    def start_requests(self):
        self.logger.info(f"🚀 Starting edit crawl: {len(self.urls)} URLs to refresh")
        while self.urls:
            url = self.urls.popleft()
            self.link_no += 1
            yield Request(
                url,
                callback=self.parse_ad,
                errback=self.errback_ad,
                meta={'link_no': self.link_no}
            )

    def parse_ad(self, response):
        link_no = response.meta['link_no']
        self.logger.info(f"[{link_no}/{self.link_no}] Refreshing {response.url}")

        item = DubizzleItem()
        # — Core identifiers —
        raw_id = response.url.split("-ID")[-1].split(".")[0]
        item["ad_id"]   = raw_id
        item["url"]     = response.url
        item["website"] = "Dubizzle"

        # — JSON-LD & preload/og image fallback —
        ld_txt = response.xpath("//script[@type='application/ld+json']/text()").get()
        try:
            schema = json.loads(ld_txt) if ld_txt else {}
        except json.JSONDecodeError:
            schema = {}

        preload = response.css("link[rel=preload][as=image]::attr(href)").get()
        og      = response.xpath("//meta[@property='og:image']/@content").get()
        ld_img  = schema.get("image") if isinstance(schema.get("image"), str) else None
        item["image_url"]  = preload or og or ld_img
        item["image_urls"] = (
            [schema["image"]]
            if isinstance(schema.get("image"), str)
            else schema.get("image", [])
        )

        # — Basic schema fields —
        def to_int(v):
            try:
                return int(float(v))
            except:
                return None

        item.update({
            "name":               schema.get("name"),
            "sku":                schema.get("sku"),
            "description":        schema.get("description"),
            "price_valid_until":  schema.get("priceValidUntil"),
            "fuel_type":          schema.get("fuelType"),
            "title":              schema.get("name"),
            "brand":              schema.get("brand"),
            "model":              schema.get("model"),
            "year":               to_int(schema.get("modelDate")),

        })

        # — DataLayer overrides —
        dl = {}
        m = re.search(r"window\['dataLayer'\]\.push\((\{[\s\S]*?\})\)", response.text)
        if m:
            blob = re.sub(r',\s*([}\]])', r'\1', m.group(1))
            try:
                dl = json.loads(blob)
            except:
                pass

        def pick(*keys):
            for k in keys:
                v = dl.get(k)
                if v not in (None, "", []):
                    return v

        item.update({
            "price":             pick("price"),
            "currency":          pick("currency_unit"),
            "condition":         pick("ad_condition"),
            "new_used":          pick("new_used"),
            "transmission_type": pick("transmission"),
            "mileage":           pick("mileage"),
            "mileage_unit":      dl.get("area_unit"),
            "body_type":         pick("body_type"),
            "price_type":        pick("price_type"),
            "seats":             pick("seats"),
            "owners":            pick("owners"),
            "interior":          pick("interior"),
            "air_con":           pick("air_con"),
            "deliverable":       pick("deliverable"),
            "has_video":         pick("video"),
            "has_panorama":      pick("panorama"),
            "seller_type":       pick("seller_type"),
            "seller_verified":   pick("seller_verified"),
            "seller_id":         pick("seller_id"),
            "agency_id":         pick("agency_id", "company_ids"),
            "agency_name":       pick("agency_name"),
            "is_agent":          pick("is_agent"),
            "location_city":     pick("loc_name"),
            "location_region":   pick("loc_2_name", "loc_1_name"),
            "loc_id":            pick("loc_id"),
            "loc_breadcrumb":    pick("loc_breadcrumb"),
            "category_1_id":     pick("category_1_id"),
            "category_1_name":   pick("category_1_name"),
            "category_2_id":     pick("category_2_id"),
            "category_2_name":   pick("category_2_name"),
            "number_of_images":  pick("number_of_photos"),
            "ownership_type":    pick("ownership_type"),
            "page_type":         pick("page_type"),
            "color": pick("color"),
            "source":            pick("source")
        })

        # — Timestamp from window.state —
        created_dt = None
        m_s = re.search(r"window\.state\s*=\s*(\{[\s\S]*?\});", response.text)
        if m_s:
            raw = re.sub(r',\s*([}\]])', r'\1', m_s.group(1))
            try:
                state = json.loads(raw)
                unix_ts = state.get("ad", {}).get("data", {}).get("timestamp")
                if unix_ts is not None:
                    created_dt = datetime.fromtimestamp(unix_ts, tz=timezone.utc)
            except:
                pass

        item["post_date"] = created_dt
        item["seller"]    = state.get("ad", {}).get("data", {}).get("name")
        trim_obj = state.get("ad", {}).get("data", {}).get("extraFields", {}).get("version", {})
        item["trim"] = None if not trim_obj else trim_obj

        # — Clean up doors field —
        def clean_doors(v):
            if not v:
                return None
            try:
                if "-" in v:
                    nums = [int(x) for x in v.split("-") if x.isdigit()]
                    return max(nums) if nums else None
                return int(v)
            except:
                return None

        item["doors"] = clean_doors(pick("doors"))
        item["date_scraped"] = datetime.now()

        yield item

    def closed(self, reason):
        self.logger.info(
            f"[Summary] Crawl finished: {self.link_no} ads. Reason: {reason}"
        )

    def errback_page(self, failure):
        self.logger.error(f"[Error❌] Failed to load page: {failure.request.url}")

    def errback_ad(self, failure):
        self.logger.error(f"[Error❌] Failed to load ad: {failure.request.url}")



