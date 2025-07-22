
import re
import json

from urllib.parse       import urlparse, parse_qs
from scrapy             import Request
from scrapy.exceptions  import CloseSpider

from .dubizzle_template import DubizzleTemplateSpider

class DubizzleDailySpider(DubizzleTemplateSpider):
    name = "dubizzle_daily"
    custom_settings = {

         "FEEDS": {
            "dubizzle_daily.json": {"format": "json", "encoding": "utf8", "overwrite": True}
        },
        "ITEM_PIPELINES": {
            "scraper.pipelines.LoadSeenIDsPipeline":      100,
            "scraper.pipelines.TrimInferencePipeline":   200,
            "scraper.pipelines.DubizzlePostgresPipeline":300,
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seen_ids     = set()  # populated by LoadSeenIDsPipeline
        self.no_new_pages = 0
        self.page         = 1
        self.logger.info("🕷️ DubizzleDailySpider initialized")

    def start_requests(self):
        start_url = f"https://www.dubizzle.sa/en/vehicles/cars-for-sale/?page={self.page}"
        self.logger.info(f"🚀 Starting crawl at page {self.page}")
        yield Request(start_url, callback=self.parse_page, errback=self.errback_page)

    def parse_page(self, response):
        self.logger.info(f"📄 Parsing page {self.page}: {response.url}")
        links = response.css(
            'li[aria-label="Listing"] a[href*="/en/ad/"]::attr(href)'
        ).getall()
        total_links = len(links)
        unique = list(dict.fromkeys(links)) # removes duplicates while preserving order
        self.logger.info(f"🔍 Found {total_links} links, {len(unique)} unique")

        new = []
        for href in unique:
            rid = href.split('-ID')[-1].split('.')[0]
            if rid not in self.seen_ids:
                self.seen_ids.add(rid)
                new.append(href)

        self.logger.info(f"✨ {len(new)} new ads on this page")
        if not new:
            self.no_new_pages += 1
            self.logger.info(f"⏭️ No new ads—counter: {self.no_new_pages}/2")
            if self.no_new_pages >= 2:
                self.logger.info("🔚 Reached 2 consecutive pages with no new ads. Stopping crawl.")
                raise CloseSpider("no_more_new_ads")
        else:
            self.no_new_pages = 0
            for href in new:
                yield response.follow(href, callback=self.parse_ad, errback=self.errback_ad)

        # queue next page
        self.page += 1
        next_url = f"https://www.dubizzle.sa/en/vehicles/cars-for-sale/?page={self.page}"
        self.logger.info(f"➡ Scheduling next page: {self.page}")
        yield Request(next_url, callback=self.parse_page, errback=self.errback_page)

