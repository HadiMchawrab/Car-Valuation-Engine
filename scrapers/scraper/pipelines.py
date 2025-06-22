# scraper/pipelines.py

import re
from psycopg2 import pool, extras, OperationalError
from scrapy import signals
from scrapy.exceptions import NotConfigured
from itemadapter import ItemAdapter

class PostgresPipeline:
    """Two-table pipeline: listings + dubizzle_details with FK."""

    BATCH_SIZE = 100  # flush every 100 items

    def __init__(self, conn_params):
        self.conn_params = conn_params
        self.pool        = None
        self.buffer      = []

    @classmethod
    def from_crawler(cls, crawler):
        params = dict(
            host     = crawler.settings.get("POSTGRES_HOST"),
            port     = crawler.settings.get("POSTGRES_PORT"),
            dbname   = crawler.settings.get("POSTGRES_DB"),
            user     = crawler.settings.get("POSTGRES_USER"),
            password = crawler.settings.get("POSTGRES_PASSWORD"),
            sslmode  = crawler.settings.get("POSTGRES_SSLMODE"),
            sslrootcert = crawler.settings.get("POSTGRES_SSLROOTCERT"), 
        )
        if not all(params.values()):
            raise NotConfigured("Postgres settings incomplete")
        pipe = cls(params)
        # connect spider_idle for final flush
        crawler.signals.connect(pipe.spider_idle,   signal=signals.spider_idle)
        crawler.signals.connect(pipe.close_spider,  signal=signals.spider_closed)
        return pipe

    def open_spider(self, spider):
        """Called by Scrapy when the spider opens: create pool & ensure tables."""
        try:
            self.pool = pool.ThreadedConnectionPool(1, 5, **self.conn_params)
        except OperationalError as e:
            spider.logger.error("Postgres connect error: %s", e)
            raise

        conn = self.pool.getconn()
        conn.autocommit = True
        with conn.cursor() as cur:
            # 1) listings table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS listings (
              id         SERIAL   PRIMARY KEY,
              site       TEXT     NOT NULL,
              url        TEXT     NOT NULL UNIQUE,
              title      TEXT     NOT NULL,
              price      NUMERIC  NOT NULL,
              currency   TEXT     NOT NULL,
              kilometers INT,
              year       INT      NOT NULL,
              make       TEXT     NOT NULL,
              model      TEXT     NOT NULL,
              location   TEXT,
              scraped_at TIMESTAMP NOT NULL DEFAULT NOW(),
              image_urls JSONB
            );
            """)
            # 2) dubizzle_details table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS dubizzle_details (
              listing_id        INT  NOT NULL
                REFERENCES listings(id) ON DELETE CASCADE,
              ad_id             TEXT NOT NULL UNIQUE,
              description       TEXT,
              cost              NUMERIC,
              seller_type       TEXT,
              time_created      TEXT,
              condition         TEXT,
              new_used          TEXT,
              body_type         TEXT,
              fuel_type         TEXT,
              transmission_type TEXT,
              doors             INT,
              seats             INT,
              owners            INT,
              color             TEXT,
              interior          TEXT,
              air_con           TEXT,
              source            TEXT,
              PRIMARY KEY(ad_id)
            );
            """)
        self.pool.putconn(conn)
        spider.logger.info("PostgresPipeline opened and tables ensured.")

    def process_item(self, item, spider):
        """Buffer the item and flush in batches."""
        adapter = ItemAdapter(item)
        # build record tuple for both tables in one go
        record = {
            # listings fields
            "site":       adapter.get("website"),
            "url":        adapter.get("url"),
            "title":      adapter.get("title"),
            "price":      adapter.get("price"),
            "currency":   adapter.get("currency"),
            "kilometers": adapter.get("kilometers"),
            "year":       adapter.get("year"),
            "make":       adapter.get("brand"),
            "model":      adapter.get("model"),
            "location":   adapter.get("location"),
            "image_urls": extras.Json(adapter.get("images") or []),

            # dubizzle_details fields
            "ad_id":             adapter.get("ad_id"),
            "description":       adapter.get("description"),
            "cost":              adapter.get("cost"),
            "seller_type":       adapter.get("seller_type"),
            "time_created":      adapter.get("time_created"),
            "condition":         adapter.get("condition"),
            "new_used":          adapter.get("new_used"),
            "body_type":         adapter.get("body_type"),
            "fuel_type":         adapter.get("fuel_type"),
            "transmission_type": adapter.get("transmission_type"),
            "doors":             adapter.get("doors"),
            "seats":             adapter.get("seats"),
            "owners":            adapter.get("owners"),
            "color":             adapter.get("color"),
            "interior":          adapter.get("interior"),
            "air_con":           adapter.get("air_con"),
            "source":            adapter.get("source"),
        }
        self.buffer.append(record)

        if len(self.buffer) >= self.BATCH_SIZE:
            spider.logger.info(f"Batch size reached ({len(self.buffer)}), flushing")
            self._flush(spider)

        return item

    def spider_idle(self, spider):
        """Flush any remaining items when the spider is idle."""
        if self.buffer:
            spider.logger.info(f"Spider idle: flushing {len(self.buffer)} remaining items")
            self._flush(spider)

    def close_spider(self, spider):
        """Ensure final flush & close pool."""
        if self.buffer:
            spider.logger.info(f"Closing spider: final flush of {len(self.buffer)} items")
            self._flush(spider)
        if self.pool:
            self.pool.closeall()
            spider.logger.info("Postgres connection pool closed.")

    def _flush(self, spider):
        """Insert all buffered records into both tables, within one transaction."""
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                for rec in self.buffer:
                    # 1) upsert into listings, returning id
                    cur.execute("""
                    INSERT INTO listings (
                      site, url, title, price, currency,
                      kilometers, year, make, model,
                      location, image_urls
                    ) VALUES (
                      %(site)s, %(url)s, %(title)s, %(price)s, %(currency)s,
                      %(kilometers)s, %(year)s, %(make)s, %(model)s,
                      %(location)s, %(image_urls)s
                    )
                    ON CONFLICT (url) DO UPDATE
                      SET title=EXCLUDED.title,
                          price=EXCLUDED.price,
                          currency=EXCLUDED.currency,
                          kilometers=EXCLUDED.kilometers,
                          year=EXCLUDED.year,
                          make=EXCLUDED.make,
                          model=EXCLUDED.model,
                          location=EXCLUDED.location,
                          image_urls=EXCLUDED.image_urls
                    RETURNING id;
                    """, rec)
                    listing_id = cur.fetchone()[0]

                    # 2) upsert into dubizzle_details using that listing_id
                    rec["listing_id"] = listing_id
                    cur.execute("""
                    INSERT INTO dubizzle_details (
                      listing_id, ad_id, description, cost, seller_type,
                      time_created, condition, new_used, body_type,
                      fuel_type, transmission_type, doors, seats,
                      owners, color, interior, air_con, source
                    ) VALUES (
                      %(listing_id)s, %(ad_id)s, %(description)s, %(cost)s, %(seller_type)s,
                      %(time_created)s, %(condition)s, %(new_used)s, %(body_type)s,
                      %(fuel_type)s, %(transmission_type)s, %(doors)s, %(seats)s,
                      %(owners)s, %(color)s, %(interior)s, %(air_con)s, %(source)s
                    )
                    ON CONFLICT (ad_id) DO UPDATE
                      SET description = EXCLUDED.description,
                          cost        = EXCLUDED.cost,
                          seller_type = EXCLUDED.seller_type,
                          time_created= EXCLUDED.time_created,
                          condition   = EXCLUDED.condition,
                          new_used    = EXCLUDED.new_used,
                          body_type   = EXCLUDED.body_type,
                          fuel_type   = EXCLUDED.fuel_type,
                          transmission_type = EXCLUDED.transmission_type,
                          doors       = EXCLUDED.doors,
                          seats       = EXCLUDED.seats,
                          owners      = EXCLUDED.owners,
                          color       = EXCLUDED.color,
                          interior    = EXCLUDED.interior,
                          air_con     = EXCLUDED.air_con,
                          source      = EXCLUDED.source;
                    """, rec)
                conn.commit()
            spider.logger.info(f"Flushed {len(self.buffer)} items to Postgres.")
        except Exception as e:
            spider.logger.error(f"Error during flush: {e}")
            conn.rollback()
        finally:
            self.pool.putconn(conn)
            self.buffer.clear()
