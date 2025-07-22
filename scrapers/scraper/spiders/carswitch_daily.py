from .carswitch_template import CarSwitchTemplateSpider
from scrapy import Request
from scrapy.exceptions import CloseSpider
import json


class CarSwitchDailySpider(CarSwitchTemplateSpider):
    name = "carswitch_daily"
    custom_settings = {

        "FEEDS": {
            "carswitch_daily.json": {"format": "json", "encoding": "utf8", "overwrite": True}
        },
        "ITEM_PIPELINES": {
            "scraper.pipelines.LoadSeenIDsPipeline": 100,
            "scraper.pipelines.CarSwitchPostgresPipeline": 300,
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seen_ids = set()
        self.no_new_pages = 0
        self.page = 1
        self.logger.info("🕷️ CarSwitchDailySpider initialized")

    def parse_page(self, response):
        # Override to filter already-seen ads
        page = response.meta['page']
        data = json.loads(response.text)
        hits = data.get('hits', [])
        if not hits:
            self.logger.info(f"[Done] No more results at page {page}")
            return

        urls = [self.build_listing_url(hit['document']) for hit in hits]
        new_urls = []
        for url in urls:
            ad_id = url.rstrip('/').split('/')[-1]
            if ad_id not in self.seen_ids:
                self.seen_ids.add(ad_id)
                new_urls.append(url)

        if not new_urls:
            self.no_new_pages += 1
            if self.no_new_pages >= 6:
                self.logger.info("🔚 No new ads in 2 pages—stopping.")
                raise CloseSpider("no_more_new_ads")
        else:
            self.no_new_pages = 0
            for url in new_urls:
                yield Request(url, callback=self.parse_ad, errback=self.errback_ad)

        # Schedule next page
        next_page = page + 1
        self.page = next_page
        yield Request(
            url=self._api_url(next_page),
            callback=self.parse_page,
            meta={"page": next_page},
            dont_filter=True,
        )
