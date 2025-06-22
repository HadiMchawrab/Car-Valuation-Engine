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
      # Core identifiers
    ad_id            = scrapy.Field()
    url              = scrapy.Field()
    image_url        = scrapy.Field()

    # Basic info
    title            = scrapy.Field()
    description      = scrapy.Field()
    price            = scrapy.Field()
    currency         = scrapy.Field()
    cost             = scrapy.Field()   # if you still use this from your regex

    # Location & seller
    location         = scrapy.Field()
    seller_type      = scrapy.Field()
    time_created     = scrapy.Field()   # if you’re still computing this

    # Specs
    brand            = scrapy.Field()
    model            = scrapy.Field()
    year             = scrapy.Field()
    body_type        = scrapy.Field()
    condition        = scrapy.Field()
    new_used         = scrapy.Field()

    # Powertrain
    fuel_type        = scrapy.Field()
    transmission_type= scrapy.Field()

    # Usage
    kilometers       = scrapy.Field()

    # More details from dataLayer
    doors            = scrapy.Field()
    seats            = scrapy.Field()
    owners           = scrapy.Field()
    color            = scrapy.Field()
    interior         = scrapy.Field()
    air_con          = scrapy.Field()
    source           = scrapy.Field()

    # Images array
    images           = scrapy.Field()
