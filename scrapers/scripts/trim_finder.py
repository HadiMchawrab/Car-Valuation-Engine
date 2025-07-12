#!/usr/bin/env python3
# File: trim_finder.py

import os
import logging
import psycopg2
import csv
from collections import defaultdict, Counter
from dotenv import load_dotenv

from utils import (
    normalize_text,
    extract_candidates,
    extract_pre_edition,
    extract_three_letter,
    load_master_trims,
    extract_master_trims,
    fuzzy_cluster, 
    strip_make_model
)

# ──────────────────────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Load env & master‐list
# ──────────────────────────────────────────────────────────────────────────────
load_dotenv()
MASTER_FILE = "scripts/trim_ref.csv"
logger.info("Loading master trims from %s", MASTER_FILE)
master_trims = load_master_trims(MASTER_FILE, column="trim")
logger.info("→ %d master trims loaded", len(master_trims))

POSTGRES_HOST       = "db-car-sales-car-listings.b.aivencloud.com"   
POSTGRES_PORT       = 16838
POSTGRES_DB         = "defaultdb"
POSTGRES_USER       = "avnadmin"
POSTGRES_PASSWORD   = os.getenv('AIVEN_PG_PASSWORD') # put password
POSTGRES_SSLMODE    = 'verify-full'
POSTGRES_SSLROOTCERT= os.getenv('AIVEN_PG_SSLROOTCERT') # put the full path of ca.pem 


# ──────────────────────────────────────────────────────────────────────────────
# Connect & stream
# ──────────────────────────────────────────────────────────────────────────────
logger.info("Connecting to Postgres...")
conn = psycopg2.connect(
    host=POSTGRES_HOST,
    port=POSTGRES_PORT,
    dbname=POSTGRES_DB,
    user=POSTGRES_USER,
    password=POSTGRES_PASSWORD,
    sslmode=POSTGRES_SSLMODE,
    sslrootcert=POSTGRES_SSLROOTCERT
)

cur = conn.cursor(name="listing_cursor")

cur.execute("""
    SELECT
      l.brand,
      l.model,
      l.year,
      l.title,
      d.description,
      l.trim
    FROM listings AS l
    LEFT JOIN dubizzle_details AS d
      ON l.ad_id = d.ad_id
""")

# ──────────────────────────────────────────────────────────────────────────────
# Build raw counts
# ──────────────────────────────────────────────────────────────────────────────
phrase_counts = defaultdict(Counter)
BATCH_SIZE = 1000
total = 0

logger.info("Streaming rows...")
while True:
    rows = cur.fetchmany(BATCH_SIZE)
    if not rows:
        break
    total += len(rows)
    for make, model, year, title, desc, db_trim in rows:
        key  = (make, model, year)
        text = f"{title or ''} {desc or ''}"

        # 1) master‐list hits
        for m in extract_master_trims(text, master_trims):
            phrase_counts[key][m] += 1

        # 2) seed from DB trim
        if db_trim:
            # remove brand/model from the stored trim, then normalize
            raw_trim = db_trim.strip()
            cleaned_trim = strip_make_model(raw_trim, make, model)
            norm = normalize_text(cleaned_trim)
            if norm:
                phrase_counts[key][norm] += 1

        # 3) make/model candidates
        for cand in extract_candidates(text, make, model):
            norm = normalize_text(cand)
            if norm:
                phrase_counts[key][norm] += 1

        # 4) pre-edition candidates
        for cand in extract_pre_edition(text):
            cleaned = strip_make_model(cand, make, model)
            norm    = normalize_text(cleaned)
            if norm:
                phrase_counts[key][norm] += 1

        # 5) three-letter candidates
        for cand in extract_three_letter(text):
            cleaned = strip_make_model(cand, make, model)
            norm    = normalize_text(cleaned)
            if norm:
                phrase_counts[key][norm] += 1

logger.info("Processed %d rows → %d keys", total, len(phrase_counts))

# ──────────────────────────────────────────────────────────────────────────────
# Dump raw CSV
# ──────────────────────────────────────────────────────────────────────────────
raw_csv = "raw_trim_variants.csv"
logger.info("Writing raw counts to %s", raw_csv)
with open(raw_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["make","model","year","variant","count"])
    for (make, model, year), cnt in phrase_counts.items():
        for variant, count in cnt.items():
            writer.writerow([make, model, year, variant, count])

# ──────────────────────────────────────────────────────────────────────────────
# Fuzzy‐cluster & aggregate
# ──────────────────────────────────────────────────────────────────────────────
clustered_counts = {}
logger.info("Clustering variants (threshold=70)...")
for key, cnt in phrase_counts.items():
    variants = list(cnt.keys())
    clusters = fuzzy_cluster(variants, threshold=70)
    agg = Counter()
    for seed, members in clusters.items():
        agg[seed] = sum(cnt[m] for m in members)
    clustered_counts[key] = agg
    logger.info("  %s: %d → %d clusters", key, len(variants), len(agg))

# ──────────────────────────────────────────────────────────────────────────────
# Dump clustered CSV
# ──────────────────────────────────────────────────────────────────────────────
clustered_csv = "clustered_trim_variants.csv"
logger.info("Writing clustered counts to %s", clustered_csv)
with open(clustered_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["make","model","year","cluster_seed","count"])
    for (make, model, year), cnt in clustered_counts.items():
        for variant, count in cnt.items():
            writer.writerow([make, model, year, variant, count])

# ──────────────────────────────────────────────────────────────────────────────
cur.close()
conn.close()
logger.info("Done — generated %s and %s", raw_csv, clustered_csv)
