import scrapy
from scraper.items import DubizzleItem
import re
import json
from datetime import datetime, timezone




class DubizzleTemplateSpider(scrapy.Spider):

   def parse_ad(self, response):
        raw_id = response.url.split("-ID")[-1].split(".")[0]
        self.logger.info(f"✏️ Scraping ad {raw_id}")
        item = DubizzleItem()
        item["ad_id"]   = raw_id
        item["url"]     = response.url
        item["website"] = "Dubizzle"

        # — JSON-LD & image fallback —
        ld_txt = response.xpath("//script[@type='application/ld+json']/text()").get()
        try:
            schema = json.loads(ld_txt) if ld_txt else {}
        except json.JSONDecodeError:
            schema = {}
        preload = response.css("link[rel=preload][as=image]::attr(href)").get()
        og      = response.xpath("//meta[@property='og:image']/@content").get()
        ld_img  = schema.get("image") if isinstance(schema.get("image"), str) else None
        item["image_url"]  = preload or og or ld_img
        item["image_urls"] = (
            [schema["image"]]
            if isinstance(schema.get("image"), str)
            else schema.get("image", [])
        )

        def to_int(v):
            try:
                return int(float(v))
            except:
                return None

        item.update({
            "name":               schema.get("name"),
            "sku":                schema.get("sku"),
            "description":        schema.get("description"),
            "price_valid_until":  schema.get("priceValidUntil"),
            "fuel_type":          schema.get("fuelType"),
            "title":              schema.get("name"),
            "brand":              schema.get("brand"),
            "model":              schema.get("model"),
            "year":               to_int(schema.get("modelDate")),
        })

        # — DataLayer overrides —
        dl = {}
        m = re.search(r"window\['dataLayer'\]\.push\((\{[\s\S]*?\})\)", response.text)
        if m:
            blob = re.sub(r',\s*([}\]])', r'\1', m.group(1))
            try:
                dl = json.loads(blob)
            except:
                pass

        def pick(*keys):
            for k in keys:
                v = dl.get(k)
                if v not in (None, "", []):
                    return v

        item.update({
            "price":             pick("price"),
            "currency":          pick("currency_unit"),
            "condition":         pick("ad_condition"),
            "new_used":          pick("new_used"),
            "transmission_type": pick("transmission"),
            "mileage":           pick("mileage"),
            "mileage_unit":      dl.get("area_unit"),
            "body_type":         pick("body_type"),
            "price_type":        pick("price_type"),
            "seats":             pick("seats"),
            "owners":            pick("owners"),
            "interior":          pick("interior"),
            "air_con":           pick("air_con"),
            "deliverable":       pick("deliverable"),
            "has_video":         pick("video"),
            "has_panorama":      pick("panorama"),
            "seller_type":       pick("seller_type"),
            "seller_verified":   pick("seller_verified"),
            "seller_id":         pick("seller_id"),
            "agency_id":         pick("agency_id", "company_ids"),
            "agency_name":       pick("agency_name"),
            "is_agent":          pick("is_agent"),
            "location_city":     pick("loc_name"),
            "location_region":   pick("loc_2_name", "loc_1_name"),
            "loc_id":            pick("loc_id"),
            "loc_breadcrumb":    pick("loc_breadcrumb"),
            "category_1_id":     pick("category_1_id"),
            "category_1_name":   pick("category_1_name"),
            "category_2_id":     pick("category_2_id"),
            "category_2_name":   pick("category_2_name"),
            "number_of_images":  pick("number_of_photos"),
            "ownership_type":    pick("ownership_type"),
            "page_type":         pick("page_type"),
            "color": pick("color"),
            "source":            pick("source")
        })

        # — Timestamp from window.state —
        created_dt = None
        m_s = re.search(r"window\.state\s*=\s*(\{[\s\S]*?\});", response.text)
        if m_s:
            raw = re.sub(r',\s*([}\]])', r'\1', m_s.group(1))
            try:
                state   = json.loads(raw)
                unix_ts = state.get("ad", {}).get("data", {}).get("timestamp")
                if unix_ts is not None:
                    created_dt = datetime.fromtimestamp(unix_ts, tz=timezone.utc)
                    self.logger.info(f"🕒 Found post_date {created_dt.isoformat()}")
            except:
                pass

        item["post_date"] = created_dt
        item["seller"]    = state.get("ad", {}).get("data", {}).get("name")
        trim_obj = state.get("ad", {}).get("data", {}).get("extraFields", {}).get("version", {})

        item["trim"] = None if not trim_obj else trim_obj


        def clean_doors(v):
            if not v:
                return None
            try:
                if "-" in v:
                    nums = [int(x) for x in v.split("-") if x.isdigit()]
                    return max(nums) if nums else None
                return int(v)
            except:
                return None

        item["doors"] = clean_doors(pick("doors"))
        item["date_scraped"] = datetime.now()
        yield item

   def errback_page(self, failure):
        self.logger.error(f"[Error❌] Failed to load page: {failure.request.url}")

   def errback_ad(self, failure):
        self.logger.error(f"[Error❌] Failed to load ad: {failure.request.url}")

   def closed(self, reason):
        self.logger.info(f"🔚 Crawl finished: reason={reason}")
