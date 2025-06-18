import scrapy

class UsedCarsSpider(scrapy.Spider):
    name = "used_cars"
    allowed_domains = ["dubizzle.sa"]
    start_urls = ["https://www.dubizzle.sa/en/vehicles/cars-for-sale/"]

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS": 16,
        "DOWNLOAD_DELAY": 1,
        "AUTOTHROTTLE_ENABLED": True,
        "FEEDS": {
            "listings.csv": {
                 # TODO: NEED TO CHANGE METHOD OF STORAGE
                "format": "csv",
                 # TODO: ADD more Fields
                "fields": [
                    "title", "price", "link", "brand",
                    "model", "subtitle", "description",
                    "features", "location"
                ],
            },
        },
    }

    def parse(self, response):
        for card in response.css("article._63a946ba"):
            href = card.css("a::attr(href)").get()
            link = response.urljoin(href) if href else None

            summary = {
                "title":    self.safe_get(card.css("a::attr(title)")),
                "price":    self.safe_get(card.css("[aria-label=Price]::text")),
                "link":     link,
                "brand":    self.safe_get(card.xpath(
                    ".//div[@aria-label='Details']//span[text()='Brand']"
                    "/following-sibling::span/text()"
                )),
                "model":    self.safe_get(card.xpath(
                    ".//div[@aria-label='Details']//span[text()='Model']"
                    "/following-sibling::span/text()"
                )),
                "subtitle": self.safe_get(card.css("[aria-label=Subtitle]::text")),
            }

            if link:
                yield scrapy.Request(
                    link, callback=self.parse_detail, meta={"item": summary}
                )
            else:
                yield summary

    def parse_detail(self, response):
        item = response.meta["item"]

        desc_nodes = response.xpath("//div[@aria-label='Description']//text()").getall()
        desc = " ".join(t.strip() for t in desc_nodes if t.strip()) or None
        item["description"] = desc

        
        feats = response.xpath("//div[@aria-label='Features']//li/text()").getall()
        item["features"] = feats or None

        # TODO: COLLECT MORE INFORMATION
        loc_nodes = response.xpath("//div[@aria-label='Location']//text()").getall()
        locs = [t.strip() for t in loc_nodes if t.strip() and t.strip() != "Location"]
        item["location"] = locs[0] if locs else None

        yield item

    def safe_get(self, selector):
        """
        selector: a SelectorList from .css(...) or .xpath(...)
        returns stripped text or None if empty/missing.
        """
        v = selector.get(default=None)
        return v.strip() if v and v.strip() else None
