from .syarah_template import SyarahTemplateSpider


class SyarahSpider(SyarahTemplateSpider):
  name = 'syarah'
  custom_settings = {

      "FEEDS": {"syarah.json": {"format": "json", "encoding": "utf8", "overwrite": True}},
       "ITEM_PIPELINES": {"scraper.pipelines.SyarahPostgresPipeline": 300},
  }
