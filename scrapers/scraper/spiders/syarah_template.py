import json
import scrapy
from urllib.parse import urlencode, urlparse, parse_qs
from datetime import datetime
from scraper.maps import get_color_code, get_body_type_code, get_transmission_code

class SyarahTemplateSpider(scrapy.Spider):
    allowed_domains = ['newapi.syarah.com', 'syarah.com']


    # hardcoded credentials from my test
    token   = 'JR4iENSB52eTFYnRgmNgtpZXVBf3wHue'
    user_id = 'uid-1750311664584-82221'
    page_size = 12

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.page_count = 0
        self.total_ads  = 0

    def default_headers(self):
        return {
            'Accept':                     'application/json',
            'Sec-Fetch-Site':             'same-site',
            'Accept-Language':            'en-US,en;q=0.9',
            'Sec-Fetch-Mode':             'cors',
            'Origin':                     'https://syarah.com',
            'User-Agent':                 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                                          'AppleWebKit/605.1.15 (KHTML, like Gecko) '
                                          'Version/18.5 Safari/605.1.15',
            'Sec-Fetch-Dest':             'empty',
            'Priority':                   'u=3, i',
            'user-id':                    self.user_id,
            'token':                      self.token,
            'device':                     'web',
            'Accept-EnhancedStatusCodes': '1',
        }

    def start_requests(self):
        yield from self.request_search_page(1)

    def request_search_page(self, page):
        payload = {
            'filters':  {'text': ''},
            'link':     '',
            'page':     page,
            'sort':     '',
            'size':     self.page_size,
            'new_path': False,
        }
        qs = {
            'ps':          '1-12',
            'includes':    'usps,meta_tags,meta',  # include 'meta' so we get pagination info
            'search_data': json.dumps(payload),
        }
        url = 'https://newapi.syarah.com/syarah_v1/en/search/index?' + urlencode(qs)
        yield scrapy.Request(
            url,
            headers=self.default_headers(),
            callback=self.parse_search,
            errback=self.errback_page,
            cb_kwargs={'page': page},
            dont_filter=True
        )

    def parse_search(self, response, page: int):
        # ——— Core pagination + detail scheduling ———
        self.page_count += 1
        data     = response.json().get('data', {}) or {}
        products = data.get('products', []) or []
        self.total_ads += len(products)

        # enqueue detail page requests
        for prod in products:
            yield from self.schedule_detail(prod)

        # determine if there’s another page
        meta      = data.get('meta', {}) or {}
        last_page = meta.get('last_page')
        if last_page and page < last_page:
            yield from self.request_search_page(page + 1)
        elif len(products) == self.page_size:
            yield from self.request_search_page(page + 1)
        else:
            self.logger.info(f'Completed {self.page_count} pages and {self.total_ads} ads')

    def schedule_detail(self, prod: dict):
        # build and yield the detail URL
        car_id = prod.get('id')
        if not car_id:
            self.logger.error("Found product without ID: %r", prod)
            return
        url = self.build_listing_url(car_id)
        yield scrapy.Request(
            url,
            headers=self.default_headers(),
            callback=self.parse_main,
            errback=self.errback_ad,
            cb_kwargs={'car_id': car_id}
        )


    @staticmethod
    def build_listing_url(car_id: int) -> str:
      main_qs = {
                'id':              car_id,
                'thumb_size':      300,
                'device_type':     'web',
                'should_redirect': 1,
                'include':         ','.join([
                    'details','price','story','quality','meta',
                    'analytics','campaign','g4Data','options',
                    'featuredImage','gallery_section','gallery',
                    'fuel','faqs','footerdetails','footer'
                ]),
            }
      return 'https://newapi.syarah.com/syarah_v1/en/post/view-online?' + urlencode(main_qs)



    @staticmethod
    def extract_car_id(url:str)-> str:
        parsed = urlparse(url)
        qs     = parse_qs(parsed.query)
        return qs.get('id', [None])[0]


    def safe_get(self, obj, *keys, default=None):
        """
        Safely navigate through nested dicts.
        Returns default if any key is missing or obj becomes None.
        """
        for key in keys:
            if not isinstance(obj, dict):
                return default
            obj = obj.get(key, default)
            if obj is None:
                return default
        return obj

    def parse_main(self, response, car_id):
        data      = response.json().get('data', {}) or {}
        details   = data.get('details', {}) or {}
        analytics = data.get('analytics', {}) or {}
        g4        = data.get('g4Data', {}) or {}
        gallery   = data.get('gallery', {}) or {}
        card      = details.get('details_card', {}) or {}
        warranty = details.get('warranty_card', {})

        # Safely grab images list
        images = self.safe_get(gallery, 'images', default=[]) or []
        # Select featured image if available, otherwise first, otherwise empty string
        featured_url = next((img.get('img_url') for img in images if img.get('is_featured') == 1), None)
        image_url = featured_url or (images[0].get('img_url') if images else "")

        post_date_str = g4.get('list_date')
        try:
            post_date = datetime.fromisoformat(post_date_str) if post_date_str else None
        except ValueError:
            post_date = None

        item = {
            'ad_id':            car_id,
            'title':            details.get('title') or analytics.get('name'),
            'url':              details.get('share_link'),
            'brand':            analytics.get('brand'),
            'model':            analytics.get('model'),
            'website':          'Syarah',
            'year':             analytics.get('year'),
            'price':            analytics.get('price'),
            'currency':         self.safe_get(data, 'price', 'currency'),
            'trim':             analytics.get('options'),
            'mileage':          analytics.get('mileage'),
            'mileage_unit':     'km',
            'fuel_type':        analytics.get('fuel'),
            'transmission_type':get_transmission_code(analytics.get('transmission')),
            'body_type':        get_body_type_code(analytics.get('shape')),
            'condition':        analytics.get('condition'),
            'color':            get_color_code(analytics.get('color')),
            'seller':           self.safe_get(warranty, 'wakeel', 'name'),
            'seller_type':      'Private',
            'location_city':    g4.get('post_city'),
            'location_region':  g4.get('post_city'),
            'image_url':        image_url,
            'number_of_images': len(images),
            'post_date':        post_date,
            'date_scraped':     datetime.utcnow().isoformat(),

            # ----- EXTRA FEATURES --------
            'is_sold':          details.get('is_sold') == 1,
            'is_deleted':       details.get('is_deleted') == 1,
            'is_preowned':      bool(details.get('is_preowned')),
            'interior_color':   get_color_code(self.safe_get(card, 'interior_color', 'name')),
            'source':           self.safe_get(card, 'car_origin', 'name'),
            'cylinders':        analytics.get('cylinders')
                                   or self.safe_get(card, 'cylinders', 'id'),
            'engine_size':      analytics.get('engine_size'),
            'drive_type':       analytics.get('drivetrain'),
            'number_of_keys':   self.safe_get(card, 'number_of_keys', 'name'),
            'seats':            self.safe_get(card, 'seats', 'name'),
            'engine_type':      self.safe_get(card, 'engine_type', 'name'),
        }

        yield item




    def errback_page(self, failure):
        self.logger.error(f"[Error❌] Failed to load page: {failure.request.url}")

    def errback_ad(self, failure):
        self.logger.error(f"[Error❌] Failed to load ad: {failure.request.url}")
