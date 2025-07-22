import re
import json
import scrapy

from datetime import datetime, timezone

from urllib.parse import urlparse, parse_qs

from scraper.items import DubizzleItem
from .dubizzle_template import DubizzleTemplateSpider


class DubizzleSpider(DubizzleTemplateSpider):
    name = "dubizzle"
    allowed_domains = ["dubizzle.sa"]

    custom_settings = {

         "FEEDS": {
            "dubizzle_daily.json": {"format": "json", "encoding": "utf8", "overwrite": True}
        },
        "ITEM_PIPELINES": {
           # "scraper.pipelines.LoadSeenIDsPipeline":      100,
            "scraper.pipelines.TrimInferencePipeline":   200,
            "scraper.pipelines.DubizzlePostgresPipeline":300,
        },
      }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.page_count = 0
        self.total_ads = 0

    def start_requests(self):
        total_pages = 199
        for p in range(1, total_pages + 1):
            url = f"https://www.dubizzle.sa/en/vehicles/cars-for-sale/?page={p}"
            self.logger.info(f"[Loading🚀] Page {p} → {url}")
            yield scrapy.Request(
                url=url,
                callback=self.parse_page,
                errback=self.errback_page
            )

    def parse_page(self, response):
        self.page_count += 1
        qs = parse_qs(urlparse(response.url).query)
        current_page = int(qs.get("page", ["1"])[0])
        self.logger.info(f"[Loaded📄] Page #{current_page} → {response.url}")

        # Extract ad links under the aria-label="Listing" items
        links = response.css(
            'li[aria-label="Listing"] a[href*="/en/ad/"]::attr(href)'
        ).getall()
        links = list(dict.fromkeys(links))  # dedupe
        self.logger.info(f"[Progress] Found {len(links)} ad links on page {current_page}")

        for href in links:
            yield response.follow(href, callback=self.parse_ad, errback=self.errback_ad)

        # No pagination here—start_requests handles page iteration

