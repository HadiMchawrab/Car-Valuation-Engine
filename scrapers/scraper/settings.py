# Scrapy settings for scraper project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import os
from dotenv import load_dotenv
load_dotenv()




# from twisted.internet import kqreactor
# kqreactor.install()
# from twisted.internet import reactor
# if not hasattr(reactor, "_handleSignals"):
#     reactor._handleSignals = lambda *args, **kwargs: None

BOT_NAME = "scraper"

SPIDER_MODULES = ["scraper.spiders"]
NEWSPIDER_MODULE = "scraper.spiders"


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "scraper (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "scraper.middlewares.ScraperSpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    "scraper.middlewares.ScraperDownloaderMiddleware": 543,
#}

# CLOUDFLARE_WORKER_URLS = [
#     "https://dubizzle-proxy-1.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-2.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-3.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-4.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-5.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-6.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-7.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-8.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-9.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-10.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-11.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-12.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-13.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-14.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-15.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-16.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-17.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-18.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-19.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-20.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-21.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-22.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-23.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-24.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-25.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-26.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-27.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-28.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-29.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-30.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-31.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-32.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-33.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-34.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-35.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-36.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-37.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-38.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-39.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-40.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-41.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-42.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-43.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-44.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-45.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-46.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-47.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-48.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-49.welcometouseef.workers.dev",
#     "https://dubizzle-proxy-50.welcometouseef.workers.dev"
# ]


# DOWNLOADER_MIDDLEWARES = {
#     # 1) your Cloudflare or FreeProxy middleware
#     #'scraper.middlewares.HybridProxyMiddleware':           90,
#    # 'scraper.middlewares.CloudflareProxyMiddleware':    100,
#       'scraper.middlewares.FreeProxyMiddleware':               100,
#             'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 110,
#             'scraper.middlewares.EmptyPageRetryMiddleware':          150,
#             'scrapy.downloadermiddlewares.retry.RetryMiddleware':    200,
#             'scrapy_user_agents.middlewares.RandomUserAgentMiddleware': 300,
#             'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
# }

RETRY_ENABLED     = True
RETRY_TIMES       = 5
RETRY_HTTP_CODES  = [429, 500, 502, 503, 504, 408]


DOWNLOAD_DELAY = 1.0
RANDOMIZE_DOWNLOAD_DELAY = True


# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

POSTGRES_HOST       = "db-car-sales-car-listings.b.aivencloud.com"   
POSTGRES_PORT       = 16838
POSTGRES_DB         = "defaultdb"
POSTGRES_USER       = "avnadmin"
POSTGRES_PASSWORD   = os.getenv('AIVEN_PG_PASSWORD') # put password
POSTGRES_SSLMODE    = 'verify-full'
POSTGRES_SSLROOTCERT= os.getenv('AIVEN_PG_SSLROOTCERT') # put the full path of ca.pem 

TRIM_CLUSTERED_CSV = 'scripts/clustered_trim_variants.csv'
# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
# ITEM_PIPELINES = {
#    #"scraper.pipelines.ScraperPipeline": 300,
#     'scraper.pipelines.DubizzlePostgresPipeline': 300,
# }

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
