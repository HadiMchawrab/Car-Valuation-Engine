# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ScraperItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass



class DubizzleItem(scrapy.Item):
    ad_id = scrapy.Field()
    url = scrapy.Field()
    image_url = scrapy.Field()
    title = scrapy.Field()
    price = scrapy.Field()
    currency = scrapy.Field()
    cost = scrapy.Field()
    location = scrapy.Field()
    seller_name = scrapy.Field()
    time_created = scrapy.Field()
    kilometers = scrapy.Field()
    condition = scrapy.Field()
    year = scrapy.Field()
    fuel_type = scrapy.Field()
    transmission_type = scrapy.Field()
    brand = scrapy.Field()
    body_type = scrapy.Field()
    model = scrapy.Field()
    color = scrapy.Field()
    description = scrapy.Field()