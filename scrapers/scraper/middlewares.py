# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import requests
import threading
import random

from scrapy import signals
from scrapy.exceptions import IgnoreRequest
from random import choice
from fake_useragent import UserAgent
from swiftshadow.classes import ProxyInterface
from typing import List
from requests.exceptions import RequestException
import logging
from twisted.internet.task import deferLater


import re
from twisted.internet import reactor, task



class ScraperSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class ScraperDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


# class ScrapeOpsHeaderMiddleware:
#     def __init__(self):
        
        
#         load_dotenv() 
#         self.api_key = os.getenv("SCRAPEOPS_API_KEY")
#         if not self.api_key:
#             raise NotConfigured("Missing SCRAPEOPS_API_KEY in environment")
#         self.endpoint = (
#             f"http://headers.scrapeops.io/v1/browser-headers"
#             f"?api_key={self.api_key}"
#         )
#         self.headers_list = []

#     def _fetch_headers(self):
#         resp = requests.get(self.endpoint)
#         resp.raise_for_status()
#         data = resp.json()
#         self.headers_list = data.get("result", [])

#     def process_request(self, request, spider):
        
#         if not self.headers_list:
#             self._fetch_headers()
       
#         hdrs = random.choice(self.headers_list)
#         for name, val in hdrs.items():
#             request.headers[name] = val
       
#         return None

#     def spider_opened(self, spider):
#         spider.logger.info("ScrapeOpsHeaderMiddleware enabled")


# class FreeProxyMiddleware:
#     def __init__(self):
#         self.proxies = []
#         self.idx     = 0
#         self.lock    = threading.Lock()
#         self.enabled = True

#     @classmethod
#     def from_crawler(cls, crawler):
#         mw = cls()
#         crawler.signals.connect(mw.spider_opened, signal=signals.spider_opened)
#         crawler.signals.connect(mw.spider_idle,  signal=signals.spider_idle)
#         return mw

#     def spider_opened(self, spider):
#         # initial load
#         self._refresh(spider)

#     def spider_idle(self, spider):
#         # every time the spider goes idle, kick off a 30m refresh if not already running
#         # (this ensures a fresh list periodically)
#         spider.logger.info("[FreeProxy] Spider idle—refreshing proxy list")
#         self._refresh(spider)

# def _refresh(self, spider, max_rows=1000):
#     new_list = []
#     sources = [
#       "https://proxylist.geonode.com/api/proxy-list?limit=1000&page=1&sort_by=lastChecked&sort_type=desc",
#       "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all",
#       "https://www.proxy-list.download/api/v1/get?type=https"
#     ]
#     for url in sources:
#         try:
#             resp = requests.get(url, timeout=10)
#             resp.raise_for_status()
#             # JSON source
#             if "json" in resp.headers.get("Content-Type", ""):
#                 data = resp.json().get("data", [])
#                 for e in data[:max_rows]:
#                     ip, port = e["ip"], e["port"]
#                     proto = "https" if "https" in e.get("protocols",[]) else "http"
#                     new_list.append(f"{proto}://{ip}:{port}")
#             else:
#                 # plain-text list
#                 for line in resp.text.splitlines()[:max_rows]:
#                     line=line.strip()
#                     if line:
#                         if ":" in line:
#                             proto="https" if url.endswith("type=https") else "http"
#                             new_list.append(f"{proto}://{line}")
#         except Exception as e:
#             spider.logger.warning(f"[FreeProxy] source failed {url}: {e}")

#     # dedupe
#     with self.lock:
#         self.proxies = list(dict.fromkeys(new_list))
#         self.idx     = 0
#     spider.logger.info(f"[FreeProxy] Total unique IPs: {len(self.proxies)}")


#     def process_request(self, request, spider):
#         with self.lock:
#             if not self.proxies:
#                 return
#             proxy = self.proxies[self.idx]
#             # round-robin index
#             self.idx = (self.idx + 1) % len(self.proxies)

#         spider.logger.debug(f"[FreeProxy] Using proxy #{self.idx}: {proxy}")
#         request.meta["proxy"] = proxy

#     def process_exception(self, request, exception, spider):
#         # on any download exception, drop this proxy and retry
#         if "proxy" in request.meta:
#             bad = request.meta.pop("proxy")
#             spider.logger.debug(f"[FreeProxy] Dropping bad proxy {bad}: {exception}")
#         raise IgnoreRequest("Proxy failed, retrying")

# class EmptyPageRetryMiddleware:
#     def process_response(self, request, response, spider):
#         if "/en/ad/" not in request.url:
#             return response
#         has_title = bool(response.xpath("//h1/text()").get())
#         has_data  = b"dataLayer" in response.body
#         if not (has_title and has_data):
#             spider.logger.warning("Empty ad page—retrying: %s", request.url)
#             raise IgnoreRequest("Stub page")
#         return response
# # class CloudflareProxyMiddleware:
#     """
#     Only rewrite individual ad URLs via Workers. Leave listing pages alone
#     so pagination and offsite filtering still work normally.
#     """
#     def __init__(self, worker_urls):
#         self.workers = worker_urls or []
#         self.idx = 0

#     @classmethod
#     def from_crawler(cls, crawler):
#         return cls(crawler.settings.getlist("CLOUDFLARE_WORKER_URLS"))

#     def process_request(self, request, spider):
#         # Only proxy ad details pages, not listing or pagination pages
#         if "/en/ad/" not in request.url or not self.workers:
#             return

#         # pick next worker
#         worker = self.workers[self.idx]
#         self.idx = (self.idx + 1) % len(self.workers)

#         # rebuild path+query
#         parts = urllib.parse.urlsplit(request.url)
#         path_qs = parts.path + (f"?{parts.query}" if parts.query else "")
#         new_url = worker.rstrip("/") + path_qs

#         spider.logger.debug(f"[CFProxy] {request.url} → {new_url}")
#         return request.replace(url=new_url)

# class EmptyPageRetryMiddleware:

    # """
    # Only retry “empty” stub pages on *ad* URLs.  Category pages will pass through.
    # """
    # def process_response(self, request, response, spider):
    #     # only apply to individual ad URLs
    #     if "/en/ad/" not in request.url:
    #         return response

    #     # now check for the two key markers of a valid *ad* page
    #     has_title = bool(response.xpath("//h1/text()").get())
    #     has_data  = b"dataLayer" in response.body
    #     if not (has_title and has_data):
    #         spider.logger.warning(
    #             "Empty/stub ad page detected, dropping proxy & retrying: %s",
    #             request.url
    #         )
    #         request.meta.pop("proxy", None)   # rotate free proxy next time
    #         raise IgnoreRequest("Stub ad page")
    #     return response


# class SingleCookieMiddleware:
#     """
#     Force every request to share the same cookiejar ID (1),
#     so cookies persist across retries & proxy switches.
#     """
#     def process_request(self, request, spider):
#         request.meta['cookiejar'] = 1
#         return None
    

# class BrowserHeaderMiddleware:
#     def process_request(self, request, spider):
#         # only apply to dubizzle requests
#         if 'dubizzle.sa' in request.url:
#             hdrs = {
#                 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#                 'Accept-Language': 'en-US,en;q=0.5',
#                 'Referer': 'https://www.dubizzle.sa/en/vehicles/cars-for-sale/',
#             }
#             for k, v in hdrs.items():
#                 request.headers.setdefault(k, v)
#         return None
    




class SingleCookieMiddleware:
    """Force every request to share the same cookiejar ID."""
    def process_request(self, request, spider):
        request.meta['cookiejar'] = 1
        return None


HEADER_POOLS = {
    'Accept': [
      'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
      'text/html,application/xml;q=0.9,*/*;q=0.8',
    ],
    'Accept-Language': [
      'en-US,en;q=0.5',
      'ar-SA,ar;q=0.5,en-US;q=0.3',
    ],
    # we’ll dynamically fill Referer from listing pages in your spider if you like,
    # here’s a basic pool to start with:
    'Referer': [
      'https://www.dubizzle.sa/en/vehicles/cars-for-sale/',
      'https://www.dubizzle.sa/en/vehicles/cars-for-sale/?page=2',
      'https://www.dubizzle.sa/en/vehicles/cars-for-sale/?page=3',
    ],
}

class BrowserHeaderMiddleware:
    """Inject a random, realistic browser header set on each ad request."""
    def process_request(self, request, spider):
        if "/en/ad/" not in request.url:
            return None
        for hdr, opts in HEADER_POOLS.items():
            request.headers[hdr] = choice(opts)
        return None


class FreeProxyMiddleware:
    """
    • Fetches up to 1 000 free proxies (Geonode) + any from PAID_PROXIES.
    • Round-robins through them.
    • On any network error or stub page, blacklists that proxy.
    • Refreshes the pool on spider_opened and spider_idle.
    """
    def __init__(self):
        self.proxies   = []
        self.paid      = []
        self.blacklist = set()
        self.idx       = 0
        self.lock      = threading.Lock()

    @classmethod
    def from_crawler(cls, crawler):
        mw = cls()
        # load any paid proxies from settings
        mw.paid = crawler.settings.getlist('PAID_PROXIES', [])
        # hook signals
        crawler.signals.connect(mw.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(mw.spider_idle,   signal=signals.spider_idle)
        return mw

    def spider_opened(self, spider):
        # allow EmptyPageRetryMiddleware to find us
        spider.free_proxy_middleware = self
        self._refresh(spider)

    def spider_idle(self, spider):
        # refresh on idle so you never run dry
        spider.logger.info("[FreeProxy] spider_idle: refreshing proxy list")
        self._refresh(spider)

    def _refresh(self, spider, max_rows=1000):
        """Re-fetch free proxies & combine with paid ones."""
        try:
            URL = (
              "https://proxylist.geonode.com/api/proxy-list"
              "?limit=1000&page=1&sort_by=lastChecked&sort_type=desc"
            )
            resp = requests.get(URL, timeout=10)
            resp.raise_for_status()
            data = resp.json().get("data", [])
            free = []
            for entry in data[:max_rows]:
                ip = entry.get("ip"); port = entry.get("port")
                prots = entry.get("protocols", [])
                scheme = "https" if "https" in prots else "http"
                if ip and port:
                    free.append(f"{scheme}://{ip}:{port}")
            with self.lock:
                self.proxies = free + list(self.paid)
                self.blacklist.clear()
                self.idx = 0
            spider.logger.info(f"[FreeProxy] Loaded {len(self.proxies)} proxies (free+paid)")
        except Exception as e:
            spider.logger.warning(f"[FreeProxy] refresh failed: {e}")

    def process_request(self, request, spider):
        with self.lock:
            # skip blacklisted
            n = len(self.proxies)
            if n == 0:
                return
            # find next non-blacklisted
            for _ in range(n):
                p = self.proxies[self.idx]
                self.idx = (self.idx + 1) % n
                if p not in self.blacklist:
                    request.meta['proxy'] = p
                    spider.logger.debug(f"[FreeProxy] → {p}")
                    return
        # no good proxies, just fall through

    def process_exception(self, request, exception, spider):
        # any network/TLS/etc error, blacklist and retry
        proxy = request.meta.pop('proxy', None)
        if proxy:
            self.blacklist.add(proxy)
            spider.logger.info(f"[FreeProxy] blacklisting failed proxy {proxy}")
        raise IgnoreRequest("Proxy failed, retrying")


    def drop_proxy(self, proxy, spider):
        """Manual drop for stub pages."""
        with self.lock:
            self.blacklist.add(proxy)
        spider.logger.info(f"[FreeProxy] blacklisting stub proxy {proxy}")






# load_dotenv()
logger = logging.getLogger(__name__)


class EmptyPageRetryMiddleware:
    """
    Retry on stub pages *and* on HTTP 401/500+ errors.
    On 401, also rotate Scrapy-Impersonate browsers via request.meta["impersonate"].
    """

    # list of browser codes supported by scrapy-impersonate
    BROWSERS = [
        "chrome110", "chrome119", "edge99", "firefox133",
        "safari15_5", "safari17_0"
    ]

    def __init__(
        self,
        base_delay=1.0,
        max_delay=60.0,
        jitter_factor=0.5,
        think_chance=0.05,
        think_min=0.1,
        think_max=0.5
    ):
        self.base_delay    = base_delay
        self.max_delay     = max_delay
        self.jitter_factor = jitter_factor
        self.think_chance  = think_chance
        self.think_min     = think_min
        self.think_max     = think_max

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            base_delay    = crawler.settings.getfloat("BACKOFF_BASE_DELAY",   1.0),
            max_delay     = crawler.settings.getfloat("BACKOFF_MAX_DELAY",   60.0),
            jitter_factor = crawler.settings.getfloat("BACKOFF_JITTER",      0.5),
            think_chance  = crawler.settings.getfloat("HUMAN_THINK_CHANCE",  0.05),
            think_min     = crawler.settings.getfloat("HUMAN_THINK_MIN",     0.1),
            think_max     = crawler.settings.getfloat("HUMAN_THINK_MAX",     0.5),
        )

    def _compute_delay(self, retry_count):
        delay = min(self.max_delay, self.base_delay * (2 ** (retry_count - 1)))
        jitter = random.uniform(-self.jitter_factor * delay, self.jitter_factor * delay)
        return max(0, delay + jitter)

    def _should_retry(self, request, response):
        # only for detail pages
        if "/en/ad/" not in request.url:
            return False

        # stub detection
        has_title = bool(response.xpath("//h1/text()").get())
        has_data  = b"dataLayer" in response.body
        if not (has_title and has_data):
            return True

        # HTTP errors to retry
        if response.status == 401 or 500 <= response.status < 600:
            return True

        return False

    def process_response(self, request, response, spider):
        if self._should_retry(request, response):
            retry = request.meta.get("stub_retry", 0) + 1
            delay = self._compute_delay(retry)

            spider.logger.warning(
                f"[Retry] status={response.status}, stub={bool(response.xpath('//h1/text()').get())}, "
                f"retry #{retry} in {delay:.1f}s: {request.url}")

            # drop bad proxy if using one
            proxy = request.meta.pop("proxy", None)
            if proxy and hasattr(spider, "free_proxy_middleware"):
                spider.free_proxy_middleware.drop_proxy(proxy, spider)

            # build the retry request
            new_meta = {**request.meta, "stub_retry": retry}

            # on 401, add a random impersonation fingerprint
            if response.status == 401:
                browser = random.choice(self.BROWSERS)
                new_meta["impersonate"] = browser
                spider.logger.debug(f"[Retry] Using impersonation '{browser}' for next attempt")

            new_req = request.replace(dont_filter=True, meta=new_meta)
            return deferLater(reactor, delay, lambda: new_req)

        # on success: optional human “think” delay
        if "stub_retry" in request.meta:
            spider.logger.debug(
                f"[Retry] Succeeded after {request.meta['stub_retry']} retries: {request.url}"
            )
        if random.random() < self.think_chance:
            think = random.uniform(self.think_min, self.think_max)
            spider.logger.debug(f"[Human] thinking for {think:.2f}s before parsing {request.url}")
            return deferLater(reactor, think, lambda: response)

        return response

    def process_exception(self, request, exception, spider):
        # treat network errors the same as stubs
        retry = request.meta.get("stub_retry", 0) + 1
        delay = self._compute_delay(retry)

        spider.logger.error(f"[Retry] Exception {exception} on {request.url}; retry #{retry} in {delay:.1f}s")

        new_meta = {**request.meta, "stub_retry": retry}
        # optionally rotate impersonation on network errors too:
        browser = random.choice(self.BROWSERS)
        new_meta["impersonate"] = browser
        spider.logger.debug(f"[Retry] Using impersonation '{browser}' after exception")

        new_req = request.replace(dont_filter=True, meta=new_meta)
        return deferLater(reactor, delay, lambda: new_req)
    """
    Retry on stub pages *and* on HTTP 401/500+ errors.
    On 401, also rotate headers (UA, Accept-Language, Referer) before retrying.
    """

    # some sample Accept-Language strings to rotate
    LANGUAGES = [
        "en-US,en;q=0.9",
        "en-GB,en;q=0.8",
        "ar-SA,ar;q=0.9,en;q=0.8",
        "fr-FR,fr;q=0.9,en;q=0.8",
    ]

    def __init__(
        self,
        base_delay=1.0,
        max_delay=60.0,
        jitter_factor=0.5,
        think_chance=0.05,
        think_min=0.1,
        think_max=0.5
    ):
        self.base_delay    = base_delay
        self.max_delay     = max_delay
        self.jitter_factor = jitter_factor
        self.think_chance  = think_chance
        self.think_min     = think_min
        self.think_max     = think_max

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            base_delay    = crawler.settings.getfloat("BACKOFF_BASE_DELAY",   1.0),
            max_delay     = crawler.settings.getfloat("BACKOFF_MAX_DELAY",   60.0),
            jitter_factor = crawler.settings.getfloat("BACKOFF_JITTER",      0.5),
            think_chance  = crawler.settings.getfloat("HUMAN_THINK_CHANCE",  0.05),
            think_min     = crawler.settings.getfloat("HUMAN_THINK_MIN",     0.1),
            think_max     = crawler.settings.getfloat("HUMAN_THINK_MAX",     0.5),
        )

    def _compute_delay(self, retry_count):
        # exponential back-off + jitter
        delay = min(self.max_delay, self.base_delay * (2 ** (retry_count - 1)))
        jitter = random.uniform(-self.jitter_factor * delay, self.jitter_factor * delay)
        return max(0, delay + jitter)

    def _should_retry(self, request, response):
        # only for ad detail pages
        if "/en/ad/" not in request.url:
            return False

        # stub detection
        has_title = bool(response.xpath("//h1/text()").get())
        has_data  = b"dataLayer" in response.body
        if not (has_title and has_data):
            return True

        # retry on 401 or 5xx
        if response.status == 401 or 500 <= response.status < 600:
            return True

        return False

    def process_response(self, request, response, spider):
        if self._should_retry(request, response):
            retry = request.meta.get("stub_retry", 0) + 1
            delay = self._compute_delay(retry)
            spider.logger.warning(
                f"[Retry] status={response.status}, stub={not bool(response.xpath('//h1/text()').get())}, "
                f"retry #{retry} in {delay:.1f}s → {request.url}"
            )

            # drop bad proxy if you have one
            proxy = request.meta.pop("proxy", None)
            if proxy and hasattr(spider, "free_proxy_middleware"):
                spider.free_proxy_middleware.drop_proxy(proxy, spider)

            # prepare the new request
            new_req = request.replace(
                dont_filter=True,
                meta={**request.meta, "stub_retry": retry}
            )

            # On 401, rotate headers
            if response.status == 401:
                # re-randomize User-Agent
                new_ua = spider.settings.get("USER_AGENT") or request.headers.get("User-Agent")
                # if you use fake_useragent, do something like:
                # from fake_useragent import UserAgent
                # new_ua = UserAgent().random
                new_req.headers["User-Agent"] = new_ua
                # random Accept-Language
                new_req.headers["Accept-Language"] = random.choice(self.LANGUAGES)
                # random Referer: use the base listing page or a random page
                base = "https://www.dubizzle.sa/en/vehicles/cars-for-sale/"
                page = random.randint(1, 10)
                new_req.headers["Referer"] = f"{base}?page={page}"
                spider.logger.debug(
                    f"[Retry] Rotated headers for 401 retry #{retry}: UA={new_ua}, "
                    f"Accept-Language={new_req.headers['Accept-Language']}, Referer={new_req.headers['Referer']}"
                )

            return deferLater(reactor, delay, lambda: new_req)

        # on success: optional human “think” delay
        if "stub_retry" in request.meta:
            spider.logger.debug(
                f"[Retry] Succeeded after {request.meta['stub_retry']} retries: {request.url}"
            )
        if random.random() < self.think_chance:
            think = random.uniform(self.think_min, self.think_max)
            spider.logger.debug(f"[Human] thinking for {think:.2f}s")
            return deferLater(reactor, think, lambda: response)

        return response

    def process_exception(self, request, exception, spider):
        # network errors are treated like retryable errors
        retry = request.meta.get("stub_retry", 0) + 1
        delay = self._compute_delay(retry)
        spider.logger.error(
            f"[Retry] Exception {exception} on {request.url}; retry #{retry} in {delay:.1f}s"
        )
        new_req = request.replace(
            dont_filter=True,
            meta={**request.meta, "stub_retry": retry}
        )
        return deferLater(reactor, delay, lambda: new_req)
    """
    Retry on stub pages (no <h1> or dataLayer) *and* on HTTP 401/500+ errors.
    Drops the proxy, backs off with jitter, and retries until success.
    """

    def __init__(
        self,
        base_delay=1.0,
        max_delay=60.0,
        jitter_factor=0.5,
        think_chance=0.05,
        think_min=0.1,
        think_max=0.5
    ):
        self.base_delay    = base_delay
        self.max_delay     = max_delay
        self.jitter_factor = jitter_factor
        self.think_chance  = think_chance
        self.think_min     = think_min
        self.think_max     = think_max

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            base_delay    = crawler.settings.getfloat("BACKOFF_BASE_DELAY",   1.0),
            max_delay     = crawler.settings.getfloat("BACKOFF_MAX_DELAY",   60.0),
            jitter_factor = crawler.settings.getfloat("BACKOFF_JITTER",      0.5),
            think_chance  = crawler.settings.getfloat("HUMAN_THINK_CHANCE",  0.05),
            think_min     = crawler.settings.getfloat("HUMAN_THINK_MIN",     0.1),
            think_max     = crawler.settings.getfloat("HUMAN_THINK_MAX",     0.5),
        )

    def _compute_delay(self, retry_count):
        # exponential back-off
        delay = min(self.max_delay, self.base_delay * (2 ** (retry_count - 1)))
        # apply jitter ± jitter_factor * delay
        jitter = random.uniform(-self.jitter_factor * delay, self.jitter_factor * delay)
        return max(0, delay + jitter)

    def _should_retry(self, request, response):
        # only retry ad detail pages
        if "/en/ad/" not in request.url:
            return False

        # retry on stub detection
        has_title = bool(response.xpath("//h1/text()").get())
        has_data  = b"dataLayer" in response.body
        if not (has_title and has_data):
            return True

        # retry on 401 or any 5xx server error
        if response.status == 401 or 500 <= response.status < 600:
            return True

        return False

    def process_response(self, request, response, spider):
        if self._should_retry(request, response):
            retry = request.meta.get("stub_retry", 0) + 1
            delay = self._compute_delay(retry)
            spider.logger.warning(
                f"[RetryMiddleware] Status={response.status}, stub={not bool(response.xpath('//h1/text()').get())}, "
                f"retry #{retry} in {delay:.1f}s: {request.url}"
            )

            # drop the bad proxy
            proxy = request.meta.pop("proxy", None)
            if proxy and hasattr(spider, "free_proxy_middleware"):
                spider.free_proxy_middleware.drop_proxy(proxy, spider)

            # schedule a retry
            new_req = request.replace(
                dont_filter=True,
                meta={**request.meta, "stub_retry": retry}
            )
            return deferLater(reactor, delay, lambda: new_req)

        # on success, optionally inject a “think” delay
        if "stub_retry" in request.meta:
            spider.logger.debug(
                f"[RetryMiddleware] Succeeded after {request.meta['stub_retry']} retries: {request.url}"
            )
        if random.random() < self.think_chance:
            think = random.uniform(self.think_min, self.think_max)
            spider.logger.debug(f"[Humanize] Thinking for {think:.2f}s before parsing {request.url}")
            return deferLater(reactor, think, lambda: response)

        return response

    def process_exception(self, request, exception, spider):
        # treat network exceptions exactly like stub/server errors
        retry = request.meta.get("stub_retry", 0) + 1
        delay = self._compute_delay(retry)
        spider.logger.error(
            f"[RetryMiddleware] Exception {exception} on {request.url}; retry #{retry} in {delay:.1f}s"
        )
        new_req = request.replace(
            dont_filter=True,
            meta={**request.meta, "stub_retry": retry}
        )
        return deferLater(reactor, delay, lambda: new_req)
    """
    Detect stub ad pages (no <h1> or dataLayer), blacklist that proxy,
    and retry the request with exponential back-off + jitter until the real
    page loads, then add small random “think” delays to mimic a human user.
    """

    def __init__(self, base_delay=1.0, max_delay=60.0, jitter_factor=0.5, think_chance=0.05, think_min=0.1, think_max=0.5):
        self.base_delay    = base_delay     # first retry delay
        self.max_delay     = max_delay      # cap for back-off
        self.jitter_factor = jitter_factor  # fraction of delay to jitter
        self.think_chance  = think_chance   # chance to “think” on success
        self.think_min     = think_min      # min think delay (s)
        self.think_max     = think_max      # max think delay (s)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            base_delay   = crawler.settings.getfloat("BACKOFF_BASE_DELAY", 1.0),
            max_delay    = crawler.settings.getfloat("BACKOFF_MAX_DELAY", 60.0),
            jitter_factor= crawler.settings.getfloat("BACKOFF_JITTER", 0.5),
            think_chance = crawler.settings.getfloat("HUMAN_THINK_CHANCE", 0.05),
            think_min    = crawler.settings.getfloat("HUMAN_THINK_MIN", 0.1),
            think_max    = crawler.settings.getfloat("HUMAN_THINK_MAX", 0.5),
        )

    def process_response(self, request, response, spider):
        # Only retry detail ad pages
        if "/en/ad/" not in request.url:
            return response

        has_title = bool(response.xpath("//h1/text()").get())
        has_data  = b"dataLayer" in response.body

        if not (has_title and has_data):
            # exponential back-off counter
            retry = request.meta.get("stub_retry", 0) + 1
            delay = min(self.max_delay, self.base_delay * (2 ** (retry - 1)))

            spider.logger.warning(
                f"[EmptyPageRetry] Stub detected: {request.url} "
                f"(retry #{retry} in {delay:.1f}s), dropping proxy."
            )

            # drop the bad proxy from your free_proxy middleware
            proxy = request.meta.pop("proxy", None)
            if proxy and hasattr(spider, "free_proxy_middleware"):
                spider.free_proxy_middleware.drop_proxy(proxy, spider)

            # schedule the retry after the delay
            new_req = request.replace(
                dont_filter=True,
                meta={**request.meta, "stub_retry": retry}
            )
            return deferLater(reactor, delay, lambda: new_req)

        # on success, clear the retry counter
        if "stub_retry" in request.meta:
            spider.logger.debug(
                f"[EmptyPageRetry] Success after {request.meta['stub_retry']} retries on {request.url}"
            )

        return response

    def process_exception(self, request, exception, spider):
        # treat network errors the same way
        retry = request.meta.get("stub_retry", 0) + 1
        delay = min(self.max_delay, self.base_delay * (2 ** (retry - 1)))

        spider.logger.error(
            f"[EmptyPageRetry] Exception {exception} on {request.url}; "
            f"retry #{retry} in {delay:.1f}s"
        )

        new_req = request.replace(
            dont_filter=True,
            meta={**request.meta, "stub_retry": retry}
        )
        return deferLater(reactor, delay, lambda: new_req)
    



class MixedHeadersRetryMiddleware:
    """
    1) On every request: rotate UA, Accept-Language, Referer.
    2) On 401 or stub/5xx responses: backoff, drop proxy, set impersonate.
    3) Retry indefinitely with jitter + human think delays.
    """

    # Browsers for scrapy-impersonate
    BROWSERS = ["chrome110", "chrome119", "edge99", "firefox133", "safari15_5"]
    # Accept-Language pool
    LANGUAGES = ["en-US,en;q=0.9", "en-GB,en;q=0.8", "ar-SA,ar;q=0.9,en;q=0.8"]
    # Base listing URL for fake Referer
    BASE_LISTING = "https://www.dubizzle.sa/en/vehicles/cars-for-sale/"

    def __init__(
        self,
        base_delay=1.0,
        max_delay=60.0,
        jitter_factor=0.5,
        think_chance=0.05,
        think_min=0.1,
        think_max=0.5
    ):
        self.ua = UserAgent()
        self.base_delay    = base_delay
        self.max_delay     = max_delay
        self.jitter_factor = jitter_factor
        self.think_chance  = think_chance
        self.think_min     = think_min
        self.think_max     = think_max

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            base_delay    = crawler.settings.getfloat("BACKOFF_BASE_DELAY",   1.0),
            max_delay     = crawler.settings.getfloat("BACKOFF_MAX_DELAY",   60.0),
            jitter_factor = crawler.settings.getfloat("BACKOFF_JITTER",      0.5),
            think_chance  = crawler.settings.getfloat("HUMAN_THINK_CHANCE",  0.05),
            think_min     = crawler.settings.getfloat("HUMAN_THINK_MIN",     0.1),
            think_max     = crawler.settings.getfloat("HUMAN_THINK_MAX",     0.5),
        )

    def _compute_delay(self, retry):
        d = min(self.max_delay, self.base_delay * (2 ** (retry - 1)))
        jitter = random.uniform(-self.jitter_factor * d, self.jitter_factor * d)
        return max(0, d + jitter)

    def process_request(self, request, spider):
        """
        Always rotate these on every request before download:
        - User-Agent via fake_useragent
        - Accept-Language
        - Referer to a random page of the listing search
        """
        # 1) UA
        ua = self.ua.random
        request.headers["User-Agent"] = ua

        # 2) Accept-Language
        request.headers["Accept-Language"] = random.choice(self.LANGUAGES)

        # 3) Referer
        page = random.randint(1, 10)
        request.headers["Referer"] = f"{self.BASE_LISTING}?page={page}"

        spider.logger.debug(f"[Headers] UA={ua}, Lang={request.headers['Accept-Language']}, Ref={request.headers['Referer']}")

        return None

    def _should_retry(self, request, response):
        # detail pages only
        if "/en/ad/" not in request.url:
            return False
        # stub detection
        has_title = bool(response.xpath("//h1/text()").get())
        has_data  = b"dataLayer" in response.body

        if not (has_title and has_data):
            # exponential back-off counter
            retry = request.meta.get("stub_retry", 0) + 1
            # base delay * 2^(retry-1)
            delay = min(self.max_delay, self.base_delay * (2 ** (retry - 1)))
            # add random jitter up to ± jitter_factor * delay
            jitter = random.uniform(-self.jitter_factor * delay, self.jitter_factor * delay)
            delay = max(0, delay + jitter)

            spider.logger.warning(
                f"[EmptyPageRetry] Stub detected on {request.url} "
                f"(retry #{retry}, delaying {delay:.1f}s)…"
            )

            # drop proxy if present
            proxy = request.meta.pop("proxy", None)
            if proxy and hasattr(spider, "free_proxy_middleware"):
                spider.free_proxy_middleware.drop_proxy(proxy, spider)

            # schedule retry
            new_req = request.replace(
                dont_filter=True,
                meta={**request.meta, "stub_retry": retry}
            )
            return deferLater(reactor, delay, lambda: new_req)

        # on success: optional human “think” delay
        if "stub_retry" in request.meta:
            spider.logger.debug(
                f"[EmptyPageRetry] Success after {request.meta['stub_retry']} retries on {request.url}"
            )
        if random.random() < self.think_chance:
            think = random.uniform(self.think_min, self.think_max)
            spider.logger.debug(f"[Humanize] Thinking for {think:.2f}s before proceeding")
            return deferLater(reactor, think, lambda: response)

        return response

    def process_exception(self, request, exception, spider):
        # treat exceptions like stubs
        retry = request.meta.get("stub_retry", 0) + 1
        delay = min(self.max_delay, self.base_delay * (2 ** (retry - 1)))
        jitter = random.uniform(-self.jitter_factor * delay, self.jitter_factor * delay)
        delay = max(0, delay + jitter)

        spider.logger.error(
            f"[EmptyPageRetry] Exception {exception} on {request.url}; "
            f"retry #{retry} in {delay:.1f}s"
        )
        new_req = request.replace(
            dont_filter=True,
            meta={**request.meta, "stub_retry": retry}
        )
        return deferLater(reactor, delay, lambda: new_req)
    """
    Detect stub ad pages (no <h1> or dataLayer), blacklist that proxy,
    and retry the request with exponential back-off until the real page loads.
    """

    def __init__(self, base_delay=1.0, max_delay=60.0):
        self.base_delay = base_delay
        self.max_delay = max_delay

    @classmethod
    def from_crawler(cls, crawler):
        mw = cls(
            base_delay=crawler.settings.getfloat("BACKOFF_BASE_DELAY", 1.0),
            max_delay=crawler.settings.getfloat("BACKOFF_MAX_DELAY", 60.0),
        )
        return mw

    def process_response(self, request, response, spider):
        # only re-try detail ad pages
        if "/en/ad/" not in request.url:
            return response

        has_title = bool(response.xpath("//h1/text()").get())
        has_data  = b"dataLayer" in response.body

        if not (has_title and has_data):
            # exponential back-off counter
            retry = request.meta.get("stub_retry", 0) + 1
            delay = min(self.max_delay, self.base_delay * (2 ** (retry - 1)))

            spider.logger.warning(
                f"[EmptyPageRetry] Stub detected: {request.url} "
                f"(retry #{retry} in {delay:.1f}s), dropping proxy."
            )

            # drop the bad proxy from your free_proxy middleware
            proxy = request.meta.pop("proxy", None)
            if proxy and hasattr(spider, "free_proxy_middleware"):
                spider.free_proxy_middleware.drop_proxy(proxy, spider)

            # schedule the retry after the delay
            new_req = request.replace(
                dont_filter=True,
                meta={**request.meta, "stub_retry": retry}
            )
            return deferLater(reactor, delay, lambda: new_req)

        # on success, clear the retry counter
        if "stub_retry" in request.meta:
            spider.logger.debug(
                f"[EmptyPageRetry] Success after {request.meta['stub_retry']} retries on {request.url}"
            )

        return response

    def process_exception(self, request, exception, spider):
        # treat network errors the same way
        retry = request.meta.get("stub_retry", 0) + 1
        delay = min(self.max_delay, self.base_delay * (2 ** (retry - 1)))

        spider.logger.error(
            f"[EmptyPageRetry] Exception {exception} on {request.url}; "
            f"retry #{retry} in {delay:.1f}s"
        )

        new_req = request.replace(
            dont_filter=True,
            meta={**request.meta, "stub_retry": retry}
        )
        return deferLater(reactor, delay, lambda: new_req)
    


class MixedHeadersRetryMiddleware:
    """
    1) On every request: rotate UA, Accept-Language, Referer.
    2) On 401 or stub/5xx: back-off with jitter, drop proxy,
       set meta['impersonate'], and retry indefinitely.
    """

    BROWSERS = ["chrome110","chrome119","edge99","firefox133","safari15_5"]
    LANGUAGES = ["en-US,en;q=0.9","en-GB,en;q=0.8","ar-SA,ar;q=0.9,en;q=0.8"]
    BASE_LISTING = "https://www.dubizzle.sa/en/vehicles/cars-for-sale/"

    def __init__(self, base_delay=1.0, max_delay=60.0,
                 jitter_factor=0.5, think_chance=0.05,
                 think_min=0.1, think_max=0.5):
        self.ua = UserAgent()
        self.base_delay    = base_delay
        self.max_delay     = max_delay
        self.jitter_factor = jitter_factor
        self.think_chance  = think_chance
        self.think_min     = think_min
        self.think_max     = think_max

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            base_delay    = crawler.settings.getfloat("BACKOFF_BASE_DELAY",  1.0),
            max_delay     = crawler.settings.getfloat("BACKOFF_MAX_DELAY",  60.0),
            jitter_factor = crawler.settings.getfloat("BACKOFF_JITTER",     0.5),
            think_chance  = crawler.settings.getfloat("HUMAN_THINK_CHANCE", 0.05),
            think_min     = crawler.settings.getfloat("HUMAN_THINK_MIN",    0.1),
            think_max     = crawler.settings.getfloat("HUMAN_THINK_MAX",    0.5),
        )

    def _compute_delay(self, retry):
        d = min(self.max_delay, self.base_delay * (2 ** (retry-1)))
        j = random.uniform(-self.jitter_factor*d, self.jitter_factor*d)
        return max(0, d+j)

    def process_request(self, request, spider):
        # rotate UA
        ua = self.ua.random
        request.headers["User-Agent"] = ua
        # rotate Accept-Language
        request.headers["Accept-Language"] = random.choice(self.LANGUAGES)
        # rotate Referer
        page = random.randint(1,10)
        request.headers["Referer"] = f"{self.BASE_LISTING}?page={page}"
        spider.logger.debug(f"[Headers] UA={ua}, AL={request.headers['Accept-Language']}, Ref={request.headers['Referer']}")
        return None

    def _should_retry(self, request, response):
        if "/en/ad/" not in request.url:
            return False
        # stub detection
        has_title = bool(response.xpath("//h1/text()").get())
        has_data  = b"dataLayer" in response.body
        if not (has_title and has_data):
            return True
        # HTTP errors
        if response.status==401 or 500<=response.status<600:
            return True
        return False

    def process_response(self, request, response, spider):
        if self._should_retry(request, response):
            retry = request.meta.get("stub_retry",0)+1
            delay = self._compute_delay(retry)
            spider.logger.warning(f"[Retry] status={response.status}, stub={bool(response.xpath('//h1/text()').get())}, retry#{retry} in {delay:.1f}s: {request.url}")
            # drop bad proxy
            proxy = request.meta.pop("proxy", None)
            if proxy and hasattr(spider, "free_proxy_middleware"):
                spider.free_proxy_middleware.drop_proxy(proxy, spider)
            # build new meta
            new_meta = {**request.meta, "stub_retry": retry}
            # on 401, impersonate
            if response.status==401:
                b = random.choice(self.BROWSERS)
                new_meta["impersonate"] = b
                spider.logger.debug(f"[Retry] Impersonating {b}")
            new_req = request.replace(dont_filter=True, meta=new_meta)
            return deferLater(reactor, delay, lambda: new_req)

        # on success: clear counter, maybe “think”
        if "stub_retry" in request.meta:
            spider.logger.debug(f"[Retry] Succeeded after {request.meta['stub_retry']} retries")
        if random.random()<self.think_chance:
            t = random.uniform(self.think_min, self.think_max)
            spider.logger.debug(f"[Human] think for {t:.2f}s")
            return deferLater(reactor, t, lambda: response)
        return response

    def process_exception(self, request, exception, spider):
        retry = request.meta.get("stub_retry",0)+1
        delay = self._compute_delay(retry)
        spider.logger.error(f"[Retry] Exception {exception} on {request.url}; retry#{retry} in {delay:.1f}s")
        new_meta = {**request.meta, "stub_retry": retry}
        # impersonate on exception too
        b = random.choice(self.BROWSERS)
        new_meta["impersonate"] = b
        spider.logger.debug(f"[Retry] Impersonating {b} after exception")
        new_req = request.replace(dont_filter=True, meta=new_meta)
        return deferLater(reactor, delay, lambda: new_req)


class PageChangeLoggingMiddleware:
    """Log every time we land on a new listing page (?page=N)."""
    def process_response(self, request, response, spider):
        if "?page=" in response.url:
            try:
                p = int(response.url.split("page=")[-1])
            except ValueError:
                p = response.url
            spider.logger.info(f"[Page] Now scraping listing page {p}")
        return response
    """
    1) On every request: rotate UA, Accept-Language, Referer.
    2) On 401 or stub/5xx responses: backoff, drop proxy, set impersonate.
    3) Retry indefinitely with jitter + human think delays.
    """

    # Browsers for scrapy-impersonate
    BROWSERS = ["chrome110", "chrome119", "edge99", "firefox133", "safari15_5"]
    # Accept-Language pool
    LANGUAGES = ["en-US,en;q=0.9", "en-GB,en;q=0.8", "ar-SA,ar;q=0.9,en;q=0.8"]
    # Base listing URL for fake Referer
    BASE_LISTING = "https://www.dubizzle.sa/en/vehicles/cars-for-sale/"

    def __init__(
        self,
        base_delay=1.0,
        max_delay=60.0,
        jitter_factor=0.5,
        think_chance=0.05,
        think_min=0.1,
        think_max=0.5
    ):
        self.ua = UserAgent()
        self.base_delay    = base_delay
        self.max_delay     = max_delay
        self.jitter_factor = jitter_factor
        self.think_chance  = think_chance
        self.think_min     = think_min
        self.think_max     = think_max

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            base_delay    = crawler.settings.getfloat("BACKOFF_BASE_DELAY",   1.0),
            max_delay     = crawler.settings.getfloat("BACKOFF_MAX_DELAY",   60.0),
            jitter_factor = crawler.settings.getfloat("BACKOFF_JITTER",      0.5),
            think_chance  = crawler.settings.getfloat("HUMAN_THINK_CHANCE",  0.05),
            think_min     = crawler.settings.getfloat("HUMAN_THINK_MIN",     0.1),
            think_max     = crawler.settings.getfloat("HUMAN_THINK_MAX",     0.5),
        )

    def _compute_delay(self, retry):
        d = min(self.max_delay, self.base_delay * (2 ** (retry - 1)))
        jitter = random.uniform(-self.jitter_factor * d, self.jitter_factor * d)
        return max(0, d + jitter)

    def process_request(self, request, spider):
        """
        Always rotate these on every request before download:
        - User-Agent via fake_useragent
        - Accept-Language
        - Referer to a random page of the listing search
        """
        # 1) UA
        ua = self.ua.random
        request.headers["User-Agent"] = ua

        # 2) Accept-Language
        request.headers["Accept-Language"] = random.choice(self.LANGUAGES)

        # 3) Referer
        page = random.randint(1, 10)
        request.headers["Referer"] = f"{self.BASE_LISTING}?page={page}"

        spider.logger.debug(f"[Headers] UA={ua}, Lang={request.headers['Accept-Language']}, Ref={request.headers['Referer']}")

        return None

    def _should_retry(self, request, response):
        # detail pages only
        if "/en/ad/" not in request.url:
            return False
        # stub detection
        has_title = bool(response.xpath("//h1/text()").get())
        has_data  = b"dataLayer" in response.body
        if not (has_title and has_data):
            return True
        # HTTP errors
        if response.status == 401 or 500 <= response.status < 600:
            return True
        return False

    def process_response(self, request, response, spider):
        if self._should_retry(request, response):
            retry = request.meta.get("stub_retry", 0) + 1
            delay = self._compute_delay(retry)

            spider.logger.warning(
                f"[Retry] status={response.status}, stub={bool(response.xpath('//h1/text()').get())}, "
                f"retry #{retry} in {delay:.1f}s: {request.url}"
            )

            # drop proxy if you have one
            proxy = request.meta.pop("proxy", None)
            if proxy and hasattr(spider, "free_proxy_middleware"):
                spider.free_proxy_middleware.drop_proxy(proxy, spider)

            # prepare new request meta
            new_meta = {**request.meta, "stub_retry": retry}

            # on 401, also set impersonation
            if response.status == 401:
                browser = random.choice(self.BROWSERS)
                new_meta["impersonate"] = browser
                spider.logger.debug(f"[Retry] Impersonate={browser}")

            new_req = request.replace(dont_filter=True, meta=new_meta)
            return deferLater(reactor, delay, lambda: new_req)

        # success: maybe “think”
        if "stub_retry" in request.meta:
            spider.logger.debug(f"[Retry] Succeeded after {request.meta['stub_retry']} retries")
        if random.random() < self.think_chance:
            think = random.uniform(self.think_min, self.think_max)
            spider.logger.debug(f"[Human] think={think:.2f}s")
            return deferLater(reactor, think, lambda: response)

        return response

    def process_exception(self, request, exception, spider):
        retry = request.meta.get("stub_retry", 0) + 1
        delay = self._compute_delay(retry)
        spider.logger.error(f"[Retry] Exception {exception} on {request.url}; retry #{retry} in {delay:.1f}s")

        new_meta = {**request.meta, "stub_retry": retry}
        # also rotate impersonation on exception
        browser = random.choice(self.BROWSERS)
        new_meta["impersonate"] = browser
        spider.logger.debug(f"[Retry] Impersonate={browser} after exception")

        new_req = request.replace(dont_filter=True, meta=new_meta)
        return deferLater(reactor, delay, lambda: new_req)