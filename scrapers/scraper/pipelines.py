# scraper/pipelines.py

import logging
import psycopg2
from scrapy import signals
from scrapy.exceptions import DropItem, NotConfigured, CloseSpider
from itemadapter import ItemAdapter
from datetime import datetime


import psycopg2
from scrapy.exceptions import NotConfigured
from itemadapter import ItemAdapter

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
              post_date         TIMESTAMP
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
            "image_url","number_of_images","post_date"
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
        settings = crawler.settings
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