
import scrapy
from urllib.parse import urlparse, parse_qs
import json
from .opensooq_template import OpenSooqTemplateSpider



class OpenSooqSpider(OpenSooqTemplateSpider):
    name = "opensooq"
    allowed_domains = ["opensooq.sa", "sa.opensooq.com"]
    custom_settings = {
        **OpenSooqTemplateSpider.custom_settings,
         "FEEDS": {
            "opensooq.json": {"format": "json", "encoding": "utf8", "overwrite": True}
        },
        "ITEM_PIPELINES": {
           "scraper.pipelines.OpenSooqPostgresPipeline":300,
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.page_count = 0
        self.total_ads = 0

    def start_requests(self):
        total_pages = 75
        for p in range(1, total_pages + 1):
            url = f"https://sa.opensooq.com/en/cars/cars-for-sale?page={p}"
            self.logger.info(f"[Loading🚀] Page {p} → {url}")
            yield scrapy.Request(
                url=url,
                callback=self.parse_page,
                errback=self.errback_page
            )


    def parse_page(self, response):
      # 1) Log which page we loaded
      self.page_count += 1
      qs = parse_qs(urlparse(response.url).query)
      current_page = int(qs.get("page", ["1"])[0])
      self.logger.info(f"[Loaded📄] Page #{current_page} → {response.url}")

      # 2) Grab & parse the __NEXT_DATA__ blob
      blob = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
      if not blob:
          self.logger.error("⛔ __NEXT_DATA__ missing")
          return
      data = json.loads(blob)

      # 3) Navigate into the SERP API response
      serp = data["props"]["pageProps"]["serpApiResponse"]

      listings = serp['listings']
      items = listings['items']
      # serp_data = (data["props"]["pageProps"].get("serpApiResponse", {}).get("data", {}))

      # 4) Pull out the 30-item listings list
      # listings_wrap = serp_data.get("listings", {})
      self.logger.info(f"[Progress] Found {len(items)} listings in JSON")

      # 5) (Optional) inspect the meta if you need paging info
      # meta = listings_wrap.get("meta", {})

      # 6) Enqueue each detail page
      for ad in items:
          ad_url = ad['post_url']
          if not ad_url:
              continue
          self.total_ads += 1
          self.logger.info(f"[Progress] Scraping AD #{self.total_ads}: {response.url}")
          yield response.follow(
              f"/en{ad_url}",
              callback=self.parse_ad,
              errback=self.errback_ad
          )

