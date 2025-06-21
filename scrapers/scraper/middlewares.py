# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import requests
import threading
import time
import urllib.parse
from scrapy import signals
from scrapy.exceptions import IgnoreRequest
from random import choice


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


class EmptyPageRetryMiddleware:
    """
    Detect stub ad pages (no <h1> or dataLayer), blacklist that proxy,
    and retry the request on a fresh IP.
    """
    def process_response(self, request, response, spider):
        if "/en/ad/" not in request.url:
            return response

        has_title = bool(response.xpath("//h1/text()").get())
        has_data  = b"dataLayer" in response.body
        if not (has_title and has_data):
            spider.logger.warning(f"Stub ad page: {request.url} → retry")
            # tell FreeProxyMiddleware to drop this IP
            proxy = request.meta.pop('proxy', None)
            if proxy and hasattr(spider, 'free_proxy_middleware'):
                spider.free_proxy_middleware.drop_proxy(proxy, spider)
            raise IgnoreRequest("Stub ad page")
        return response