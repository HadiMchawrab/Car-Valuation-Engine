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


class BasePostgresPipeline:
    """Generic Postgres pipeline for upserting into a shared `listings` table and an optional detail table."""
    table = 'listings'
    key_column = 'ad_id'

    # Core listings schema: column name -> SQL type
    core_schema = {
        'ad_id':            'TEXT PRIMARY KEY',
        'url':              'TEXT UNIQUE NOT NULL',
        'website':          'TEXT NOT NULL',
        'title':            'TEXT',
        'price':            'NUMERIC',
        'currency':         'TEXT',
        'brand':            'TEXT',
        'model':            'TEXT',
        'year':             'INT',
        'mileage':          'INT',
        'mileage_unit':     'TEXT',
        'fuel_type':        'TEXT',
        'transmission_type':'TEXT',
        'body_type':        'TEXT',
        'condition':        'TEXT',
        'color':            'TEXT',
        'seller':           'TEXT',
        'seller_type':      'TEXT',
        'location_city':    'TEXT',
        'location_region':  'TEXT',
        'image_url':        'TEXT',
        'number_of_images':'INT',
        'post_date':        'TIMESTAMP',
        'date_scraped':     'TIMESTAMP',
        'trim':             'TEXT',
    }

    # Subclasses configure these
    detail_table = None          # e.g. 'dubizzle_details'
    detail_schema = None         # dict of detail columns -> SQL types

    def __init__(self, conn_params):
        self.conn_params = conn_params
        self.conn = None

    @classmethod
    def from_crawler(cls, crawler):
        params = dict(
            host        = crawler.settings.get('POSTGRES_HOST'),
            port        = crawler.settings.get('POSTGRES_PORT'),
            dbname      = crawler.settings.get('POSTGRES_DB'),
            user        = crawler.settings.get('POSTGRES_USER'),
            password    = crawler.settings.get('POSTGRES_PASSWORD'),
            sslmode     = crawler.settings.get('POSTGRES_SSLMODE'),
            sslrootcert = crawler.settings.get('POSTGRES_SSLROOTCERT'),
        )
        if not all(params.values()):
            raise NotConfigured(f"{cls.__name__}: incomplete Postgres settings")
        return cls(params)

    def open_spider(self, spider):
        # Establish connection
        self.conn = psycopg2.connect(**self.conn_params)
        self.conn.autocommit = True

        # Ensure tables exist with correct types
        with self.conn.cursor() as cur:
            # Create shared listings table
            core_cols = ",\n  ".join(f"{col} {typ}" for col, typ in self.core_schema.items())
            cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table} (
              {core_cols}
            );
            """)

            # Create detail table if provided
            if self.detail_table and self.detail_schema:
                detail_cols = ",\n  ".join(f"{col} {typ}" for col, typ in self.detail_schema.items())
                cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.detail_table} (
                  {detail_cols}
                );
                """)

        spider.logger.info(f"{self.__class__.__name__}: ready (tables ensured).")

    def close_spider(self, spider):
        if self.conn:
            self.conn.close()
            spider.logger.info(f"{self.__class__.__name__}: connection closed.")

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        # Build main data dict
        main_cols = list(self.core_schema.keys())
        main_data = {col: adapter.get(col) for col in main_cols}

        # Build detail data dict (if any)
        if self.detail_table and self.detail_schema:
            detail_cols = list(self.detail_schema.keys())
            detail_data = {col: adapter.get(col) for col in detail_cols}
        else:
            detail_cols = detail_data = None

        # Helper to create upsert SQL
        def build_upsert(table, cols):
            cols_list  = ", ".join(cols)
            vals_list  = ", ".join(f"%({c})s" for c in cols)
            upd_clause = ", ".join(f"{c}=EXCLUDED.{c}" for c in cols if c != self.key_column)
            return f"""
            INSERT INTO {table} ({cols_list})
            VALUES ({vals_list})
            ON CONFLICT ({self.key_column}) DO UPDATE
              SET {upd_clause};
            """

        sql_main = build_upsert(self.table, main_cols)
        sql_det  = build_upsert(self.detail_table, detail_cols) if detail_cols else None

        # Execute upserts
        with self.conn.cursor() as cur:
            cur.execute(sql_main, main_data)
            spider.logger.debug(f"[DB] upsert {self.table}.{main_data[self.key_column]}")
            if sql_det:
                cur.execute(sql_det, detail_data)
                spider.logger.debug(f"[DB] upsert {self.detail_table}.{detail_data[self.key_column]}")

        return item


class DubizzlePostgresPipeline(BasePostgresPipeline):
    detail_table = 'dubizzle_details'
    detail_schema = {
        'ad_id':            'TEXT PRIMARY KEY REFERENCES listings(ad_id) ON DELETE CASCADE',
        'name':             'TEXT',
        'sku':              'TEXT',
        'description':      'TEXT',
        'image_urls':       'TEXT',
        'price_valid_until':'TIMESTAMP',
        'business_function':'TEXT',
        'new_used':         'TEXT',
        'kilometers':       'INT',
        'doors':            'INT',
        'seats':            'INT',
        'owners':           'INT',
        'interior':         'TEXT',
        'air_con':          'TEXT',
        'ownership_type':   'TEXT',
        'cost':             'NUMERIC',
        'vat_amount':       'NUMERIC',
        'price_type':       'TEXT',
        'seller_verified':  'BOOLEAN',
        'seller_id':        'TEXT',
        'agency_id':        'TEXT',
        'agency_name':      'TEXT',
        'is_agent':         'BOOLEAN',
        'loc_id':           'TEXT',
        'loc_name':         'TEXT',
        'loc_breadcrumb':   'TEXT',
        'loc_1_id':         'TEXT',
        'loc_1_name':       'TEXT',
        'loc_2_id':         'TEXT',
        'loc_2_name':       'TEXT',
        'category_1_id':    'INT',
        'category_1_name':  'TEXT',
        'category_2_id':    'INT',
        'category_2_name':  'TEXT',
        'page_type':        'TEXT',
        'website_section':  'TEXT',
        'has_video':        'BOOLEAN',
        'has_panorama':     'BOOLEAN',
        'deliverable':      'BOOLEAN',
        'delivery_option':  'TEXT',
    }


class OpenSooqPostgresPipeline(BasePostgresPipeline):
    detail_table = 'opensooq_details'
    detail_schema = {
        'ad_id':             'TEXT PRIMARY KEY REFERENCES listings(ad_id) ON DELETE CASCADE',
        'name':              'TEXT',
        'description':       'TEXT',
        'engine_size':       'TEXT',
        'body_type':         'TEXT',
        'payment_method':    'TEXT',
        'seats':             'INT',
        'interior_color':    'TEXT',
        'source':            'TEXT',
        'paint_quality':     'TEXT',
        'body_condition':    'TEXT',
        'category':          'TEXT',
        'subcategory':       'TEXT',
        'interior_options':  'TEXT',
        'exterior_options':  'TEXT',
        'technology_options':'TEXT',
        'seller_url':        'TEXT',
        'seller_id':         'TEXT',
        'is_shop':           'BOOLEAN',
        'is_pro_buyer':      'BOOLEAN',
        'seller_verified':   'BOOLEAN',
        'rating_avg':        'NUMERIC',
        'number_of_ratings': 'INT',
        'seller_joined':     'TIMESTAMP',
        'response_time':     'TEXT',
        'has_video':         'BOOLEAN',
        'has_panorama':      'BOOLEAN',
        'price_valid_until': 'TIMESTAMP',
        'listing_status':    'TEXT',
        'user_target_type':  'TEXT',
        'post_map': 'JSONB'
    }


class CarSwitchPostgresPipeline(BasePostgresPipeline):
    detail_table = 'carswitch_details'
    detail_schema = {
        # link back to listings
        'ad_id':                         'TEXT PRIMARY KEY REFERENCES listings(ad_id) ON DELETE CASCADE',

        # extra CarSwitchItem fields
        'secondary_id':                  'TEXT',
        'regional_specs':                'TEXT',
        'uuid':                          'TEXT',
        'cylinders':                     'TEXT',
        'engine_size':                   'TEXT',
        'asking_price':                  'NUMERIC',
        'is_paid':                       'BOOLEAN',
        'is_featured':                   'BOOLEAN',
        'drive_type':                    'TEXT',
        'variant':                       'TEXT',
        'seats':                         'INT',
        'listing_rank':                  'INT',
        'status':                        'TEXT',
        'zoho_car_id':                   'TEXT',
        'overall_condition':             'TEXT',
        'is_accidented':                 'TEXT',
        'accident_detail':               'TEXT',
        'air_bags_condition':            'TEXT',
        'chassis_condition':             'TEXT',
        'engine_condition':              'TEXT',
        'gear_box_condition':            'TEXT',
        'service_history':               'TEXT',
        'service_history_verified':      'BOOLEAN',
        'crossed_price':                 'NUMERIC',
        'last_price':                    'NUMERIC',

        'original_success_fee':          'NUMERIC',
        'final_success_fee':             'NUMERIC',
        'success_fee_type':              'TEXT',
        'success_fee_promo_code':        'TEXT',
        'price_dropped_badge':           'BOOLEAN',
        'price_dropped_badge_expiration':'TIMESTAMP',
        'alloy_rims':                    'BOOLEAN',
        'rim_size':                      'TEXT',
        'roof_type':                     'TEXT',
        'no_of_keys':                    'INT',
        'currently_financed':            'BOOLEAN',
        'bank_name':                     'TEXT',
        'cash_buyer_only':               'BOOLEAN',
        'warranty':                      'TEXT',
        'warranty_expiration_date':      'TIMESTAMP',
        'warranty_mileage_limit':        'INT',
        'service_contract':              'TEXT',
        'service_contract_verified':     'BOOLEAN',
        'classified_web_link':           'TEXT',
        'special_about_car':             'TEXT',
        'registration_city_name':        'TEXT',
        'cappasity_link':                'TEXT',
        'first_owner':                   'TEXT',
        'fair_value_override':           'NUMERIC',
        'inspection_started_by':         'TEXT',
        'seller_nationality':            'TEXT',
        'created_at':                    'TIMESTAMP',
        'updated_at':                    'TIMESTAMP',



        # additional simple flags & metrics
        'show_all_details':              'BOOLEAN',
        'fair_value':                    'NUMERIC',
        'confidence':                    'NUMERIC',
        'explanation_en':                'TEXT',
        'explanation_ar':                'TEXT',
        'min_fair_value':                'NUMERIC',
        'max_fair_value':                'NUMERIC',
    }



class SyarahPostgresPipeline(BasePostgresPipeline):
    detail_table = 'syarah_details'
    detail_schema = {
        # link back to listings
        'ad_id':           'TEXT PRIMARY KEY REFERENCES listings(ad_id) ON DELETE CASCADE',

        # Syarah‐specific detail fields
        'is_sold':         'BOOLEAN',
        'is_deleted':      'BOOLEAN',
        'is_preowned':     'BOOLEAN',

        'interior_color':  'TEXT',
        'source':          'TEXT',
        'cylinders':       'INT',
        'engine_size':     'TEXT',
        'drive_type':      'TEXT',
        'number_of_keys':  'INT',
        'seats':           'INT',
        'engine_type':     'TEXT',
    }
# class DubizzlePostgresPipeline:
#     """Reliable upsert pipeline: listings + dubizzle_details."""

#     def __init__(self, conn_params):
#         self.conn_params = conn_params
#         self.conn = None

#     @classmethod
#     def from_crawler(cls, crawler):
#         params = dict(
#             host        = crawler.settings.get("POSTGRES_HOST"),
#             port        = crawler.settings.get("POSTGRES_PORT"),
#             dbname      = crawler.settings.get("POSTGRES_DB"),
#             user        = crawler.settings.get("POSTGRES_USER"),
#             password    = crawler.settings.get("POSTGRES_PASSWORD"),
#             sslmode     = crawler.settings.get("POSTGRES_SSLMODE"),
#             sslrootcert = crawler.settings.get("POSTGRES_SSLROOTCERT"),
#         )
#         if not all(params.values()):
#             raise NotConfigured("Postgres settings incomplete")
#         return cls(params)

#     def open_spider(self, spider):
#         try:
#             self.conn = psycopg2.connect(**self.conn_params)
#             self.conn.autocommit = True
#         except psycopg2.OperationalError as e:
#             spider.logger.error("Postgres connect error: %s", e)
#             raise

#         with self.conn.cursor() as cur:
#             # Core listings table
#             cur.execute("""
#             CREATE TABLE IF NOT EXISTS listings (
#               ad_id             TEXT PRIMARY KEY,
#               url               TEXT UNIQUE NOT NULL,
#               website           TEXT NOT NULL,
#               title             TEXT,
#               price             NUMERIC,
#               currency          TEXT,
#               brand             TEXT,
#               model             TEXT,
#               year              INT,
#               mileage           INT,
#               mileage_unit      TEXT,
#               fuel_type         TEXT,
#               transmission_type TEXT,
#               body_type         TEXT,
#               condition         TEXT,
#               color             TEXT,
#               seller            TEXT,
#               seller_type       TEXT,
#               location_city     TEXT,
#               location_region   TEXT,
#               image_url         TEXT,
#               number_of_images  INT,
#               post_date         TIMESTAMP,
#               date_scraped      TIMESTAMP,
#               trim              TEXT
#             );
#             """)
#             # Dubizzle‐specific details
#             cur.execute("""
#             CREATE TABLE IF NOT EXISTS dubizzle_details (
#               ad_id             TEXT PRIMARY KEY REFERENCES listings(ad_id) ON DELETE CASCADE,
#               name              TEXT,
#               sku               TEXT,
#               description       TEXT,
#               image_urls        TEXT,
#               price_valid_until TIMESTAMP,
#               business_function TEXT,
#               new_used          TEXT,
#               kilometers        INT,
#               doors             INT,
#               seats             INT,
#               owners            INT,
#               interior          TEXT,
#               air_con           TEXT,
#               ownership_type    TEXT,
#               cost              NUMERIC,
#               vat_amount        NUMERIC,
#               price_type        TEXT,
#               seller_verified   BOOLEAN,
#               seller_id         TEXT,
#               agency_id         TEXT,
#               agency_name       TEXT,
#               is_agent          BOOLEAN,
#               loc_id            TEXT,
#               loc_name          TEXT,
#               loc_breadcrumb    TEXT,
#               loc_1_id          TEXT,
#               loc_1_name        TEXT,
#               loc_2_id          TEXT,
#               loc_2_name        TEXT,
#               category_1_id     INT,
#               category_1_name   TEXT,
#               category_2_id     INT,
#               category_2_name   TEXT,
#               page_type         TEXT,
#               website_section   TEXT,
#               has_video         BOOLEAN,
#               has_panorama      BOOLEAN,
#               deliverable       BOOLEAN,
#               delivery_option   TEXT
#             );
#             """)
#         spider.logger.info("DubizzlePostgresPipeline opened and tables ensured.")

#     def close_spider(self, spider):
#         if self.conn:
#             self.conn.close()
#             spider.logger.info("Postgres connection closed.")

#     def process_item(self, item, spider):
#         adapter = ItemAdapter(item)

#         # 1) Build core dict
#         core_fields = [
#             "ad_id","url","website","title","price","currency","brand","model","year",
#             "mileage","mileage_unit","fuel_type","transmission_type","body_type",
#             "condition","color","seller","seller_type","location_city","location_region",
#             "image_url","number_of_images","post_date", "date_scraped", "trim"
#         ]
#         core = { f: adapter.get(f) or (spider.name if f=="website" else None) for f in core_fields }

#         # 2) Build details dict
#         detail_fields = [
#             "ad_id","name","sku","description","image_urls","price_valid_until",
#             "business_function","new_used","kilometers","doors","seats","owners",
#             "interior","air_con","ownership_type","cost","vat_amount","price_type",
#             "seller_verified","seller_id","agency_id","agency_name","is_agent",
#             "loc_id","loc_name","loc_breadcrumb","loc_1_id","loc_1_name",
#             "loc_2_id","loc_2_name","category_1_id","category_1_name",
#             "category_2_id","category_2_name","page_type","website_section",
#             "has_video","has_panorama","deliverable","delivery_option"
#         ]
#         details = { f: adapter.get(f) for f in detail_fields }

#         placeholders_core   = ", ".join(f"%({f})s" for f in core_fields)
#         columns_core        = ", ".join(core_fields)
#         update_core_clause  = ", ".join(f"{f}=EXCLUDED.{f}" for f in core_fields if f!="ad_id")

#         placeholders_det    = ", ".join(f"%({f})s" for f in detail_fields)
#         columns_det         = ", ".join(detail_fields)
#         update_det_clause   = ", ".join(f"{f}=EXCLUDED.{f}" for f in detail_fields if f!="ad_id")

#         upsert_core_sql = f"""
#             INSERT INTO listings ({columns_core})
#             VALUES ({placeholders_core})
#             ON CONFLICT (ad_id) DO UPDATE
#               SET {update_core_clause};
#         """

#         upsert_det_sql = f"""
#             INSERT INTO dubizzle_details ({columns_det})
#             VALUES ({placeholders_det})
#             ON CONFLICT (ad_id) DO UPDATE
#               SET {update_det_clause};
#         """

#         try:
#             with self.conn.cursor() as cur:
#                 cur.execute(upsert_core_sql, core)
#                 spider.logger.debug(f"[DB] Upserted listings.ad_id={core['ad_id']}")
#                 cur.execute(upsert_det_sql, details)
#                 spider.logger.debug(f"[DB] Upserted dubizzle_details.ad_id={core['ad_id']}")
#         except Exception as e:
#             spider.logger.error(f"Failed to upsert item {core.get('ad_id')}: {e}")

#         return item


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
