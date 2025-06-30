# scraper/pipelines.py

import logging
import psycopg2
from scrapy import signals, Item, Spider
from scrapy.exceptions import DropItem, NotConfigured, CloseSpider
from itemadapter import ItemAdapter
from collections import deque

from scripts.utils import normalize_ar, normalize_en
import os

import json
from flashtext import KeywordProcessor
from rapidfuzz import process

import psycopg2
from scrapy.exceptions import NotConfigured
from itemadapter import ItemAdapter

# ——— Load master_map.json ———
HERE = os.path.dirname(__file__)  # .../Markaba_Trial-1/scrapers/scraper
MASTER_MAP_PATH = os.path.abspath(
    os.path.join(HERE, os.pardir, 'scripts', 'master_map.json')
)

with open(MASTER_MAP_PATH, encoding='utf-8') as f:
    raw = json.load(f)

# rebuild with proper tuple keys
master_map = {
    (make, model, int(year)): variants
    for key, variants in raw.items()
    for make, model, year in [key.split('|')]
}

# ——— Build fast lookups ———
flashtext_procs = {}
trim_codes      = {}

for key, var2code in master_map.items():
    kp = KeywordProcessor(case_sensitive=False)
    for variant_norm, code in var2code.items():
        kp.add_keyword(variant_norm, code)
    flashtext_procs[key] = kp
    trim_codes[key]      = list(set(var2code.values()))

class DubizzlePostgresPipeline:
    """Reliable upsert pipeline: listings + dubizzle_details."""

    def __init__(self, conn_params):
        self.conn_params = conn_params
        self.conn = None

    @classmethod
    def from_crawler(cls, crawler):
        params = dict(
            host        = crawler.settings.get("POSTGRES_HOST"),
            port        = crawler.settings.get("POSTGRES_PORT"),
            dbname      = crawler.settings.get("POSTGRES_DB"),
            user        = crawler.settings.get("POSTGRES_USER"),
            password    = crawler.settings.get("POSTGRES_PASSWORD"),
            sslmode     = crawler.settings.get("POSTGRES_SSLMODE"),
            sslrootcert = crawler.settings.get("POSTGRES_SSLROOTCERT"),
        )
        if not all(params.values()):
            raise NotConfigured("Postgres settings incomplete")
        return cls(params)

    def open_spider(self, spider):
        try:
            self.conn = psycopg2.connect(**self.conn_params)
            self.conn.autocommit = True
        except psycopg2.OperationalError as e:
            spider.logger.error("Postgres connect error: %s", e)
            raise

        with self.conn.cursor() as cur:
            # Core listings table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS listings (
              ad_id             TEXT PRIMARY KEY,
              url               TEXT UNIQUE NOT NULL,
              website           TEXT NOT NULL,
              title             TEXT,
              price             NUMERIC,
              currency          TEXT,
              brand             TEXT,
              model             TEXT,
              year              INT,
              mileage           INT,
              mileage_unit      TEXT,
              fuel_type         TEXT,
              transmission_type TEXT,
              body_type         TEXT,
              condition         TEXT,
              color             TEXT,
              seller            TEXT,
              seller_type       TEXT,
              location_city     TEXT,
              location_region   TEXT,
              image_url         TEXT,
              number_of_images  INT,
              post_date         TIMESTAMP,
              date_scraped      TIMESTAMP,
              trim              TEXT
            );
            """)
            # Dubizzle‐specific details
            cur.execute("""
            CREATE TABLE IF NOT EXISTS dubizzle_details (
              ad_id             TEXT PRIMARY KEY REFERENCES listings(ad_id) ON DELETE CASCADE,
              name              TEXT,
              sku               TEXT,
              description       TEXT,
              image_urls        TEXT,
              price_valid_until TIMESTAMP,
              business_function TEXT,
              new_used          TEXT,
              kilometers        INT,
              doors             INT,
              seats             INT,
              owners            INT,
              interior          TEXT,
              air_con           TEXT,
              ownership_type    TEXT,
              cost              NUMERIC,
              vat_amount        NUMERIC,
              price_type        TEXT,
              seller_verified   BOOLEAN,
              seller_id         TEXT,
              agency_id         TEXT,
              agency_name       TEXT,
              is_agent          BOOLEAN,
              loc_id            TEXT,
              loc_name          TEXT,
              loc_breadcrumb    TEXT,
              loc_1_id          TEXT,
              loc_1_name        TEXT,
              loc_2_id          TEXT,
              loc_2_name        TEXT,
              category_1_id     INT,
              category_1_name   TEXT,
              category_2_id     INT,
              category_2_name   TEXT,
              page_type         TEXT,
              website_section   TEXT,
              has_video         BOOLEAN,
              has_panorama      BOOLEAN,
              deliverable       BOOLEAN,
              delivery_option   TEXT
            );
            """)
        spider.logger.info("DubizzlePostgresPipeline opened and tables ensured.")

    def close_spider(self, spider):
        if self.conn:
            self.conn.close()
            spider.logger.info("Postgres connection closed.")

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        # 1) Build core dict
        core_fields = [
            "ad_id","url","website","title","price","currency","brand","model","year",
            "mileage","mileage_unit","fuel_type","transmission_type","body_type",
            "condition","color","seller","seller_type","location_city","location_region",
            "image_url","number_of_images","post_date", "date_scraped", "trim"
        ]
        core = { f: adapter.get(f) or (spider.name if f=="website" else None) for f in core_fields }

        # 2) Build details dict
        detail_fields = [
            "ad_id","name","sku","description","image_urls","price_valid_until",
            "business_function","new_used","kilometers","doors","seats","owners",
            "interior","air_con","ownership_type","cost","vat_amount","price_type",
            "seller_verified","seller_id","agency_id","agency_name","is_agent",
            "loc_id","loc_name","loc_breadcrumb","loc_1_id","loc_1_name",
            "loc_2_id","loc_2_name","category_1_id","category_1_name",
            "category_2_id","category_2_name","page_type","website_section",
            "has_video","has_panorama","deliverable","delivery_option"
        ]
        details = { f: adapter.get(f) for f in detail_fields }

        placeholders_core   = ", ".join(f"%({f})s" for f in core_fields)
        columns_core        = ", ".join(core_fields)
        update_core_clause  = ", ".join(f"{f}=EXCLUDED.{f}" for f in core_fields if f!="ad_id")

        placeholders_det    = ", ".join(f"%({f})s" for f in detail_fields)
        columns_det         = ", ".join(detail_fields)
        update_det_clause   = ", ".join(f"{f}=EXCLUDED.{f}" for f in detail_fields if f!="ad_id")

        upsert_core_sql = f"""
            INSERT INTO listings ({columns_core})
            VALUES ({placeholders_core})
            ON CONFLICT (ad_id) DO UPDATE
              SET {update_core_clause};
        """

        upsert_det_sql = f"""
            INSERT INTO dubizzle_details ({columns_det})
            VALUES ({placeholders_det})
            ON CONFLICT (ad_id) DO UPDATE
              SET {update_det_clause};
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(upsert_core_sql, core)
                spider.logger.debug(f"[DB] Upserted listings.ad_id={core['ad_id']}")
                cur.execute(upsert_det_sql, details)
                spider.logger.debug(f"[DB] Upserted dubizzle_details.ad_id={core['ad_id']}")
        except Exception as e:
            spider.logger.error(f"Failed to upsert item {core.get('ad_id')}: {e}")

        return item


logger = logging.getLogger(__name__)

class LoadSeenIDsPipeline:
    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls(
            host        = crawler.settings.get("POSTGRES_HOST"),
            port        = crawler.settings.get("POSTGRES_PORT"),
            dbname      = crawler.settings.get("POSTGRES_DB"),
            user        = crawler.settings.get("POSTGRES_USER"),
            password    = crawler.settings.get("POSTGRES_PASSWORD"),
            sslmode     = crawler.settings.get("POSTGRES_SSLMODE"),
            sslrootcert = crawler.settings.get("POSTGRES_SSLROOTCERT")
        )
        # connect the spider_opened/closed signals
        crawler.signals.connect(pipeline.open_spider, signal=signals.spider_opened)
        crawler.signals.connect(pipeline.close_spider, signal=signals.spider_closed)
        logger.info("🔧 LoadSeenIDsPipeline initialized")
        return pipeline

    def __init__(self, host, port, dbname, user, password, sslmode, sslrootcert):
        self.db_args = dict(
            host     = host,
            port     = port,
            dbname   = dbname,
            user     = user,
            password = password,
            sslmode  = sslmode,
            sslrootcert = sslrootcert
        )

    def open_spider(self, spider):
        spider.logger.info("🔄 Loading seen IDs from Postgres…")
        conn = psycopg2.connect(**self.db_args)
        cur  = conn.cursor()
        cur.execute("SELECT ad_id FROM listings;")
        rows = cur.fetchall()
        spider.seen_ids = set(str(r[0]) for r in rows)
        spider.logger.info(f"✅ Loaded {len(spider.seen_ids)} seen IDs")
        cur.close()
        conn.close()

    def close_spider(self, spider):
        spider.logger.info("🔒 LoadSeenIDsPipeline closed")
        
        
class LoadAllURLsPipeline:
    
    
    def __init__(self, host, port, dbname, user, password, sslmode, sslrootcert):
        self.db_args = dict(
            host     = host,
            port     = port,
            dbname   = dbname,
            user     = user,
            password = password,
            sslmode  = sslmode,
            sslrootcert = sslrootcert
        )

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls(
            host        = crawler.settings.get("POSTGRES_HOST"),
            port        = crawler.settings.get("POSTGRES_PORT"),
            dbname      = crawler.settings.get("POSTGRES_DB"),
            user        = crawler.settings.get("POSTGRES_USER"),
            password    = crawler.settings.get("POSTGRES_PASSWORD"),
            sslmode     = crawler.settings.get("POSTGRES_SSLMODE"),
            sslrootcert = crawler.settings.get("POSTGRES_SSLROOTCERT")
        )
        # connect the spider_opened/closed signals
        crawler.signals.connect(pipeline.open_spider, signal=signals.spider_opened)
        #crawler.signals.connect(pipeline.close_spider, signal=signals.spider_closed)
        logger.info("🔧 LoadSeenURLsPipeline initialized")
        return pipeline
    

    def open_spider(self, spider):
        spider.logger.info("🔄 Loading seen URLs from Postgres…")
        conn = psycopg2.connect(**self.db_args)
        cur  = conn.cursor()
        cur.execute("SELECT url FROM listings;")
        rows = cur.fetchall()
        spider.urls = deque(str(r[0]) for r in rows)
        spider.logger.info(f"✅ Loaded {len(spider.urls)} seen IDs")
        cur.close()
        conn.close()





class TrimInferencePipeline:

    def open_spider(self, spider: Spider):
        logger.info("TrimInferencePipeline opened for spider %s", spider.name)

    def process_item(self, item: Item, spider: Spider):
        ad_id = item.get('ad_id', '<no-id>')
        make = item.get('brand') or item.get('make')
        key  = (make, item.get('model'), item.get('year'))
        logger.debug("Processing %s with key %s", ad_id, key)

        # Only infer if trim is missing or blank
        raw_trim = item.get('trim')
        if raw_trim and raw_trim.strip():
            logger.debug("Item %s already has trim '%s', skipping inference", ad_id, raw_trim)
            return item

        text = f"{item.get('title','')} {item.get('description','')}"
        en = normalize_en(text)
        ar = normalize_ar(text)
        logger.debug("Normalized EN: '%s'… AR: '%s'…", en[:50], ar[:50])

        # 1) Exact match
        proc = flashtext_procs.get(key)
        if proc:
            hits = proc.extract_keywords(en) + proc.extract_keywords(ar)
            if hits:
                best = max(hits, key=len)
                logger.info("Exact trim match '%s' for item %s", best, ad_id)
                item['trim'] = best
                return item
            else:
                logger.debug("No exact trim hit for item %s", ad_id)
        else:
            logger.warning("No flashtext processor for key %s", key)

        # 2) Fuzzy fallback
        codes = trim_codes.get(key, [])
        best = None
        if codes:
            best = process.extractOne(en, codes, score_cutoff=80) \
                   or process.extractOne(ar, codes, score_cutoff=80)
        if best:
            logger.info("Fuzzy trim match '%s' (score=%s) for item %s", best[0], best[1], ad_id)
            item['trim'] = best[0]
            return item
        else:
            logger.debug("No fuzzy trim hit for item %s", ad_id)

        # 3) Give up
        logger.info("Could not infer trim for item %s; leaving null", ad_id)
        item['trim'] = None
        return item

    def close_spider(self, spider: Spider):
        logger.info("TrimInferencePipeline closed for spider %s", spider.name)