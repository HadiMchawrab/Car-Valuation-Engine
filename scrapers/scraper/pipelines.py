# scraper/pipelines.py


import psycopg2

from scrapy.exceptions import NotConfigured
from itemadapter import ItemAdapter
from datetime import datetime


class PostgresPipeline:
    """Reliable single-insert pipeline: listings (core) + dubizzle_details (site-specific)."""

    def __init__(self, conn_params):
        self.conn_params = conn_params
        self.conn = None

    @classmethod
    def from_crawler(cls, crawler):
        params = dict(
            host         = crawler.settings.get("POSTGRES_HOST"),
            port         = crawler.settings.get("POSTGRES_PORT"),
            dbname       = crawler.settings.get("POSTGRES_DB"),
            user         = crawler.settings.get("POSTGRES_USER"),
            password     = crawler.settings.get("POSTGRES_PASSWORD"),
            sslmode      = crawler.settings.get("POSTGRES_SSLMODE"),
            sslrootcert  = crawler.settings.get("POSTGRES_SSLROOTCERT"),
        )
        if not all(params.values()):
            raise NotConfigured("Postgres settings incomplete")
        return cls(params)

    def open_spider(self, spider):
        """Establish a single autocommit connection and ensure tables exist."""
        try:
            self.conn = psycopg2.connect(
                host         = self.conn_params['host'],
                port         = self.conn_params['port'],
                dbname       = self.conn_params['dbname'],
                user         = self.conn_params['user'],
                password     = self.conn_params['password'],
                sslmode      = self.conn_params['sslmode'],
                sslrootcert  = self.conn_params['sslrootcert'],
            )
            self.conn.autocommit = True
        except psycopg2.OperationalError as e:
            spider.logger.error("Postgres connect error: %s", e)
            raise

        with self.conn.cursor() as cur:
            # 1) Core listings table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS listings (
              ad_id               TEXT     PRIMARY KEY,
              url                 TEXT     UNIQUE NOT NULL,
              website             TEXT     NOT NULL,
              title               TEXT,
              price               NUMERIC,
              currency            TEXT,
              brand               TEXT,
              model               TEXT,
              year                INT,
              mileage             INT,
              mileage_unit        TEXT,
              fuel_type           TEXT,
              transmission_type   TEXT,
              body_type           TEXT,
              condition           TEXT,
              color               TEXT,
              seller              TEXT,
              seller_type         TEXT,
              location_city       TEXT,
              location_region     TEXT,
              image_url           TEXT,
              number_of_images    INT,
              post_date           TIMESTAMP
            );
            """)

            # 2) Dubizzle-specific details
            cur.execute("""
            CREATE TABLE IF NOT EXISTS dubizzle_details (
              ad_id               TEXT    PRIMARY KEY
                REFERENCES listings(ad_id) ON DELETE CASCADE,
              name                TEXT,
              sku                 TEXT,
              description         TEXT,
              image_urls          TEXT,
              price_valid_until   TIMESTAMP,
              business_function   TEXT,
              new_used            TEXT,
              kilometers          INT,
              doors               INT,
              seats               INT,
              owners              INT,
              interior            TEXT,
              air_con             TEXT,
              ownership_type      TEXT,
              cost                NUMERIC,
              vat_amount          NUMERIC,
              price_type          TEXT,
              seller_verified     BOOLEAN,
              seller_id           TEXT,
              agency_id           TEXT,
              agency_name         TEXT,
              is_agent            BOOLEAN,
              loc_id              TEXT,
              loc_name            TEXT,
              loc_breadcrumb      TEXT,
              loc_1_id            TEXT,
              loc_1_name          TEXT,
              loc_2_id            TEXT,
              loc_2_name          TEXT,
              category_1_id       INT,
              category_1_name     TEXT,
              category_2_id       INT,
              category_2_name     TEXT,
              page_type           TEXT,
              website_section     TEXT,
              has_video           BOOLEAN,
              has_panorama        BOOLEAN,
              deliverable         BOOLEAN,
              delivery_option     TEXT
            );
            """)
        spider.logger.info("PostgresPipeline opened and tables ensured.")

    def close_spider(self, spider):
        """Close the DB connection."""
        if self.conn:
            self.conn.cursor().close()
            self.conn.close()
            spider.logger.info("Postgres connection closed.")

    def process_item(self, item, spider):
        """Insert each item immediately for maximum reliability."""
        adapter = ItemAdapter(item)

        # Build core and details dicts
        core = { field: adapter.get(field) for field in [
            "ad_id", "url", "website",
            "title", "price", "currency", "brand", "model", "year",
            "mileage", "mileage_unit", "fuel_type", "transmission_type",
            "body_type", "condition", "color", "seller", "seller_type",
            "location_city", "location_region", "image_url",
            "number_of_images", "post_date"
        ] }

        # Ensure non-nullable fields
        if not core.get("website"):
            core["website"] = spider.name
        
        details = { field: adapter.get(field) for field in [
            "ad_id", "name", "sku", "description", "image_urls",
            "price_valid_until", "business_function", "new_used", "kilometers", "doors", "seats",
            "owners", "interior", "air_con", "ownership_type",
             "price_type", "seller_verified",
            "seller_id", "agency_id", "agency_name", "is_agent",
            "loc_id", "loc_name", "loc_breadcrumb", "loc_1_id",
            "loc_1_name", "loc_2_id", "loc_2_name",
            "category_1_id", "category_1_name",
            "category_2_id", "category_2_name",
            "page_type", "website_section", "has_video",
            "has_panorama", "deliverable", "delivery_option",
            
        ] }

        try:
            with self.conn.cursor() as cur:
                # Upsert into listings
                cur.execute(
                    f"""
                    INSERT INTO listings ({', '.join(core.keys())})
                    VALUES ({', '.join(f'%({k})s' for k in core)})
                    ON CONFLICT (ad_id) DO UPDATE SET
                      {', '.join(f"{k}=EXCLUDED.{k}" for k in core if k != 'ad_id')};
                    """,
                    core
                )
                spider.logger.info(f"[DB] Saved ad_id={core['ad_id']}")

                # Upsert into dubizzle_details
                self.conn.commit()
                cur.execute(
                    f"""
                    INSERT INTO dubizzle_details ({', '.join(details.keys())})
                    VALUES ({', '.join(f'%({k})s' for k in details)})
                    ON CONFLICT (ad_id) DO UPDATE SET
                      {', '.join(f"{k}=EXCLUDED.{k}" for k in details if k != 'ad_id')};
                    """,
                    details
                )
                self.conn.commit()
        except Exception as e:
            spider.logger.error(f"Failed to insert item {core.get('ad_id')}: {e}")
        return item
