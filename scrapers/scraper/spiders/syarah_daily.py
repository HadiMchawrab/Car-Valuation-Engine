from .syarah_template import SyarahTemplateSpider
from scrapy.exceptions import CloseSpider
from scrapy import Request
class SyarahDailySpider(SyarahTemplateSpider):
  name = 'syarah_daily'
  custom_settings = {
    **SyarahTemplateSpider.custom_settings,
      "FEEDS": {"syarah_daily.json": {"format": "json", "encoding": "utf8", "overwrite": True}},
       "ITEM_PIPELINES": {
            "scraper.pipelines.LoadSeenIDsPipeline": 100,
            "scraper.pipelines.SyarahPostgresPipeline": 300,
        },
  }

  def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seen_ids = set()
        self.no_new_pages = 0
        self.logger.info("🕷️ SyarahDailySpider initialized")


  def parse_search(self, response, page: int):
        data     = response.json().get('data', {}) or {}
        products = data.get('products', []) or []

        # CHANGED: stop immediately on empty page
        if not products:
            self.logger.info(f"[Done] No more results at page {page}")
            raise CloseSpider("no_more_new_ads")

        # CHANGED: filter out already-seen products
        new_prods = []
        for prod in products:
            ad_id = prod.get('id')
            if ad_id and ad_id not in self.seen_ids:
                self.seen_ids.add(ad_id)
                new_prods.append(prod)

        # CHANGED: enforce consecutive empty-page stop
        if not new_prods:
            self.no_new_pages += 1
            self.logger.info(f"[Done] No new ads on page {page} (count={self.no_new_pages})")
            if self.no_new_pages >= 6:
                raise CloseSpider("no_more_new_ads")
        else:
            self.no_new_pages = 0

        # enqueue only the new products
        for prod in new_prods:
            yield from self.schedule_detail(prod)

        # CHANGED: continue pagination via template logic
        meta      = data.get('meta', {}) or {}
        last_page = meta.get('last_page')
        if last_page and page < last_page:
            yield from self.request_search_page(page + 1)
        elif len(products) == self.page_size:
            yield from self.request_search_page(page + 1)
        else:
            self.logger.info(f'Completed {self.page_count} pages and {self.total_ads} ads')








