from scrapy import Spider
from .carswitch_template import CarSwitchTemplateSpider
class CarSwitchSpider(CarSwitchTemplateSpider):
    name     = "carswitch"
    base_api = "https://hd7x32pwz5l1k9frp-1.a1.typesense.net/collections/cars_prod/documents/search"
    api_key  = "Tv1qKAFwcLU5hFb3W2u4Xirp3IG6Ld"
    custom_settings = {
        **CarSwitchTemplateSpider.custom_settings,
        "FEEDS": {"carswitch.json": {"format": "json", "encoding": "utf8", "overwrite": True}},
        "ITEM_PIPELINES": {"scraper.pipelines.CarSwitchPostgresPipeline": 300},
    }
