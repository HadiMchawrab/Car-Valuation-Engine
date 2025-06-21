import re
import datetime as _dt
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scraper.items import DubizzleItem

class DubizzleSpider(CrawlSpider):
    name = "dubizzle"
    allowed_domains = ["dubizzle.sa"]
    start_urls = ["https://www.dubizzle.sa/en/vehicles/cars-for-sale/"]
    
    custom_settings = {
        # feed
        'FEEDS': {
            'data/dubizzle.json': {'format': 'json', 'encoding': 'utf8', 'overwrite': True},
        },

        # concurrency & throttling
        'COOKIES_ENABLED': True,
        'CONCURRENT_REQUESTS': 32,
        'CONCURRENT_REQUESTS_PER_IP': 4,
        'DOWNLOAD_DELAY': 0.5,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'AUTOTHROTTLE_ENABLED': False,

        # retry on errors + stub pages
        'RETRY_ENABLED': True,
        'RETRY_TIMES': 10,
        'RETRY_HTTP_CODES': [429,500,502,503,504,408],

        # middleware chain
     'DOWNLOADER_MIDDLEWARES' : {
    'scraper.middlewares.SingleCookieMiddleware':        50,
    'scraper.middlewares.BrowserHeaderMiddleware':       90,
    'scraper.middlewares.FreeProxyMiddleware':          100,
    'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 110,
    'scraper.middlewares.EmptyPageRetryMiddleware':     150,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware':         200,
    'scrapy_user_agents.middlewares.RandomUserAgentMiddleware':   300,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
}
    }

    rules = (
        # follow “?page=N” links for pagination
        Rule(
            LinkExtractor(allow=r'/en/vehicles/cars-for-sale/\?page=\d+'),
            follow=True
        ),
        # parse individual ad pages
        Rule(
            LinkExtractor(allow=r'/en/ad/'),
            callback='parse_ad',
            follow=False
        ),
    )

    def parse_ad(self, response):
        item = DubizzleItem()
        item['url'] = response.url
        m = re.search(r'-ID(\d+)\.html', response.url)
        item['ad_id'] = m.group(1) if m else None
        item['image_url'] = response.css(
            "img[role='presentation'][aria-label='Cover photo']::attr(src)"
        ).get()
        item['title'] = response.css('h1::text').get(default='').strip()

        # price and currency
        price_text = response.xpath(
            "//span[@aria-label='Price']/text()|//span[contains(text(),'SR')]/text()"
        ).get()
        if price_text:
            price_text = price_text.strip()
            item['price'] = price_text
            m = re.match(r"([\d,\.]+)\s*([^\d,\.]+)|([^\d,\.]+)\s*([\d,\.]+)",
                         price_text)
            if m:
                parts = [p for p in m.groups() if p]
                if len(parts) == 2:
                    if re.match(r"^[\d,\.]+$", parts[0]):
                        item['cost'], item['currency'] = parts
                    else:
                        item['currency'], item['cost'] = parts

        # location from dataLayer
        script = response.xpath(
            "//script[contains(text(),'dataLayer')]//text()"
        ).get(default='')
        loc = re.search(r'"loc_name"\s*:\s*"([^"]+)"', script)
        loc1 = re.search(r'"loc_1_name"\s*:\s*"([^"]+)"', script)
        if loc:
            item['location'] = loc.group(1) + (f", {loc1.group(1)}" if loc1 else '')

        # seller name
        seller = response.xpath(
            "//div[span[contains(text(),'Member since')]]"
            "/preceding-sibling::div[1]/span/text()"
        ).get()
        item['seller_name'] = seller.strip() if seller else None

        # creation date parse
        created = response.xpath(
            "//span[@aria-label='Creation date']/following-sibling::span/text()"
        ).get()
        if created:
            created = created.strip().lower()
            now = _dt.datetime.now()
            if 'day' in created:
                days = int(re.search(r"(\d+)", created).group(1))
                item['time_created'] = (now - _dt.timedelta(days=days)).isoformat()
            elif 'hour' in created:
                hrs = int(re.search(r"(\d+)", created).group(1))
                item['time_created'] = (now - _dt.timedelta(hours=hrs)).isoformat()
            else:
                item['time_created'] = now.isoformat()

        # other attributes
        attrs = {
            "Kilometers": "kilometers",
            "Condition": "condition",
            "Year": "year",
            "Fuel Type": "fuel_type",
            "Transmission Type": "transmission_type",
            "Brand": "brand",
            "Body Type": "body_type",
            "Model": "model",
            "Color": "color"
        }
        for label, key in attrs.items():
            val = response.xpath(
                f"//span[contains(text(),'{label}')]/following-sibling::span/text()"
            ).get()
            if val:
                item[key] = val.strip()

        # description
        desc = response.css(
            "div[aria-label='Description'] span::text"
        ).getall()
        item['description'] = ' '.join(p.strip() for p in desc if p.strip()) or None

        yield item

#TODO: ADD AD ID