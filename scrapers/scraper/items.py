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
    # ——— Core identifiers ———
    ad_id                = scrapy.Field()  # Dubizzle’s ID (e.g. “110465826”)
    url                  = scrapy.Field()
    website              = scrapy.Field()  # “dubizzle”

    # ——— JSON-LD fields ———
    name                 = scrapy.Field()  # JSON-LD “name”
    sku                  = scrapy.Field()  # JSON-LD “sku”
    description          = scrapy.Field()
    image_urls           = scrapy.Field()  # list of JSON-LD “image” URLs
    price                = scrapy.Field()
    currency             = scrapy.Field()  # “SAR”
    price_valid_until    = scrapy.Field()  # ISO timestamp from offers.priceValidUntil
   

    # ——— Basic info & specs ———
    title                = scrapy.Field()
    brand                = scrapy.Field()
    model                = scrapy.Field()
    trim                 = scrapy.Field()
    
    year                 = scrapy.Field()
    mileage              = scrapy.Field()  # from mileageFromOdometer.value
    mileage_unit         = scrapy.Field()  # from mileageFromOdometer.unitCode
    fuel_type            = scrapy.Field()
    transmission_type    = scrapy.Field()
    body_type            = scrapy.Field()
    condition            = scrapy.Field()  # e.g. “used”/“new”
    new_used             = scrapy.Field()  # same as condition
    color                = scrapy.Field()
    source               = scrapy.Field()

    # ——— Usage & ownership ———
    kilometers           = scrapy.Field()  # duplicate of mileage
    doors                = scrapy.Field()
    seats                = scrapy.Field()
    owners               = scrapy.Field()
    interior             = scrapy.Field()
    air_con              = scrapy.Field()
    ownership_type       = scrapy.Field()  # “freehold” / “non-freehold”

    # ——— Price breakdown ———
    
    price_type           = scrapy.Field()  # “price” / “rental”

    # ——— Seller & agency ———
    seller               = scrapy.Field()  # e.g. “OLX user”
    seller_type          = scrapy.Field()  # “private” / “business”
    seller_verified      = scrapy.Field()  # yes/no
    seller_id            = scrapy.Field()
    agency_id            = scrapy.Field()
    agency_name          = scrapy.Field()
    is_agent             = scrapy.Field()  # from dataLayer

    # ——— Location ———
    location_city        = scrapy.Field()  # “Riyadh”
    location_region      = scrapy.Field()  # e.g. governorate/neighborhood
    loc_id               = scrapy.Field()  # “2-74”
    loc_name             = scrapy.Field()  # same as city
    loc_breadcrumb       = scrapy.Field()  # raw “;0-1;1-62;2-74;”
    loc_1_id             = scrapy.Field()
    loc_1_name           = scrapy.Field()
    loc_2_id             = scrapy.Field()
    loc_2_name           = scrapy.Field()

    # ——— Category & page meta ———
    category_1_id        = scrapy.Field()
    category_1_name      = scrapy.Field()
    category_2_id        = scrapy.Field()
    category_2_name      = scrapy.Field()
    page_type            = scrapy.Field()  # “offerdetail”
    website_section      = scrapy.Field()  # “main_site”

    # ——— Media & extras ———
    image_url            = scrapy.Field()  # first/thumb
    number_of_images     = scrapy.Field()  # count of photos
    has_video            = scrapy.Field()  # yes/no
    has_panorama         = scrapy.Field()  # yes/no
    deliverable          = scrapy.Field()  # yes/no
    delivery_option      = scrapy.Field()  # raw value if any

    # ——— Timing ———
    post_date            = scrapy.Field()  # from JSON-LD or dataLayer
    date_scraped = scrapy.Field()

