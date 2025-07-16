from scrapy import Spider
import scrapy
from scraper.items import OpenSooqItem
from urllib.parse import urlparse, parse_qs
import re
from scraper.maps import get_body_type_code, get_transmission_code, get_color_code
import json
from datetime import datetime
from scrapy.exceptions import DropItem


class OpenSooqTemplateSpider(Spider):
    allowed_domains = ["opensooq.sa", "sa.opensooq.com"]


    def parse_ad(self, response):

        if response.status != 200:
          self.logger.warning(f"Ad not reachable ({response.status}): {response.url}")
          raise DropItem(f"HTTP {response.status}")

        blob = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        if not blob:
              self.logger.warning(f"No __NEXT_DATA__ on page, skipping: {response.url}")
              raise DropItem("Missing JSON")
        try:
          payload  = json.loads(blob)
          pageProps = payload["props"]["pageProps"]
          postData  = pageProps["postData"]
          listing   = postData["listing"]
        except (ValueError, KeyError, TypeError) as e:
          self.logger.warning(f"Listing missing or removed at {response.url}: {e}")
          raise DropItem("Ad removed")

        item = OpenSooqItem()
        blob = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        raw_data = json.loads(blob)
        data = raw_data["props"]["pageProps"]
        postData = data["postData"]
        listing =   postData['listing']

        item['ad_id'] = listing['listing_id'] # raw_data["props"]["pageProps"]["postData"]['listing']['listing_id']

        # Basic fields
        item['url']     = response.url or listing['post_url']
        item['website'] = "OpenSooq"
        item['name'] = listing['title'] # raw_data["props"]["pageProps"]["postData"]['listing']['title']
        item['title'] = listing['title']


        # Assertion here is that the raw_data basic info fields are always in the same order

        basic_info = listing['basic_info']
        # Raw info box
        raw_info = {}
        for field in basic_info:
            label = field.get('field_label')
            if not label:
                continue

            dtype = field.get('data_type')
            if dtype == 'multi_cps':
                # multi-select: pull every option_label into a Python list
                opts = field.get('options') or []
                raw_info[label] = [opt.get('option_label') for opt in opts]
            else:
                # single-select (cp, post_id, post_date, etc)
                # use option_label if present, otherwise reporting_value_label
                raw_info[label] = (field.get('option_label') or field.get('reporting_value_label') or None)
        # Normalize core fields
        item['condition'] = (raw_info.get('Condition') or '').lower()
        item['brand']     = raw_info.get('Car Make')
        item['model']     = raw_info.get('Model')
        item['trim']      = raw_info.get('Trim')
        year = raw_info.get('Year')
        item['year'] = int(year) if year and year.isdigit() else None

        kms = raw_info.get('Kilometers') or ''
        nums = [int(x.replace(',', '')) for x in re.findall(r'[0-9,]+', kms)]
        item['mileage'] = sum(nums) // len(nums) if nums else None

        raw = (raw_info.get('Body Type') or "").lower()
        item['body_type'] = get_body_type_code(raw)
        raw_seats = raw_info.get('Number of Seats') or ''
        raw_seats = raw_seats.strip()
        match = re.search(r'(\d+)', raw_seats)
        if match:
            n = int(match.group(1))
            # if it literally says “More than 9”, treat it as 10
            if raw_seats.lower().startswith('more than'):
                seats = n + 1
            else:
                seats = n
        else:
            seats = None

        item['seats'] = seats
        item['fuel_type']      = raw_info.get('Fuel')
        trans = (raw_info.get('Transmission') or '').lower()
        item['transmission_type'] = get_transmission_code(trans)
        # normalize the raw label to lowercase (and handle None safely)
        ext_col = (raw_info.get('Exterior Color') or "").lower()
        int_col = (raw_info.get('Interior Color') or "").lower()

        # lookup, with a default of “-1” (or whatever makes sense)
        item['color']          = get_color_code(ext_col)
        item['interior_color'] = get_color_code(int_col)
        item['source']         = raw_info.get('Regional Specs')
        item['body_condition'] = raw_info.get('Body Condition')
        item['paint_quality']  = raw_info.get('Paint')
        item['location_city']  = raw_info.get('City')
        item['location_region'] = raw_info.get('Neighborhood')
        item['category']       = raw_info.get('Category')
        item['subcategory']    = raw_info.get('Subcategory')
        item['engine_size']    = raw_info.get('Engine Size (cc)')
        item['payment_method'] = raw_info.get('Payment Method')
        item['interior_options']   = json.dumps(raw_info.get('Interior Options', []))
        item['exterior_options']   = json.dumps(raw_info.get('Exterior Options', []))
        item['technology_options'] = json.dumps(raw_info.get('Technology Options', []))

        item['description'] = listing['masked_description']
        item['price'] = int(listing['price']['price'].replace(",", ""))
        item['price_valid_until'] = datetime.fromisoformat(listing['price_valid_until'])
        item['currency'] = listing['price']['currencies'][0]['symbol_label']
        item['listing_status']  = listing['listing_status']
        item['has_video'] = listing['has_video']
        item['has_panorama'] = listing['has_360']
        # in your parse_ad, immediately after you set item['image_url']:
        raw_path = listing['first_image_uri']         # e.g. "0c/2b/…4898.jpg"
        base_url = "https://opensooq-images.os-cdn.com/previews/0x720/"

        # strip any leading “/” just in case, then build the full webp URL:
        item['image_url'] = f"{base_url}{raw_path.lstrip('/').removesuffix('.webp').removesuffix('.jpg')}.jpg.webp"
        item['number_of_images'] = len(listing['media'])
        date_str = listing['publish_date']
        date_obj = datetime.strptime(date_str, '%d-%m-%Y')
        item['post_date'] = date_obj
        item['post_map'] = json.dumps(listing['post_map'])

        # listing['post_map']
# {'lat': 24.695161, 'lng': 46.732351}
#  listing['next_prev']
# {'next_url': '/en/search/265828689/تاهو-ليميتد-ادشن-2017', 'prev_url': '/en/search/265928537/قطع-سياره-اكسنت-2019'}



        item['date_scraped'] = datetime.now()
        item['user_target_type'] = listing['user_target_type']
        # Seller info
        seller = postData['seller']
        member_link = seller['member_link']
        item['seller'] = seller['full_name']
        item['seller_url'] = member_link
        item['seller_id'] = seller['id']
        item['is_shop'] = seller.get('is_shop', '')
        item['is_pro_buyer'] = seller.get('is_pro_buyer', '')
        item['seller_verified'] = seller.get('authorised_seller', '')
        item['rating_avg'] = seller['rating_avg']
        item['seller_joined']     = datetime.strptime(seller['member_since'], '%d-%m-%Y')
        item['number_of_ratings'] = seller['number_of_ratings']
        item['response_time'] = seller['response_time']
        item['seller_type'] = 'Business' if seller.get('authorised_seller', '') else 'Private'
        item['mileage_unit'] = 'km'



        # Options & description



        # JSON LD DATA __NEXT DATA USEFUL PATHS:
        # blob = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        # data = json.loads(blob)
        # serp = data["props"]["pageProps"]
#         serp["postData"].keys()
# dict_keys(['listing', 'seller', 'buyer', 'logging_data', 'listings_count', 'isFullLoaded', 'isQuickPost'])
#  serp["postData"]['listing'].keys()
# dict_keys(['listing_id', 'member_id', 'post_type', 'country_id', 'title', 'masked_description', 'has_delivery_service', 'city_neighborhood', 'city', 'neighborhood', 'posted_date', 'post_map', 'lang', 'category', 'sub_category', 'publish_date', 'price_valid_until', 'masked_local_phone', 'listing_reveal_phone_key', 'has_video', 'has_360', 'has_youtube', 'share_deeplink', 'post_url', 'cv_id', 'media', 'first_image_uri', 'basic_info', 'dynamic_sections', 'price', 'price_amount', 'addOn', 'can_export', 'services', 'next_prev', 'loan_type', 'enable_review', 'is_listing_reported', 'hide_contact_info', 'similar_type', 'map_supported', 'listing_status', 'is_active', 'is_shop', 'user_target_type', 'vin_number', 'similar_recommended', 'post_tags'])
#serp["postData"]['seller'].keys()
# dict_keys(['id', 'rating_avg', 'number_of_ratings', 'full_name', 'profile_picture', 'member_since', 'is_shop', 'response_time', 'authorised_seller', 'is_followed', 'member_link', 'is_pro_buyer'])
# serp["postData"]['listings_count']
# 2
# >>> serp["postData"]['isQuickPost']
# >>> serp["postData"]['isFullLoaded'] - CAN USE FOR STUB MIDDLEWARE
# serp["postData"]['listing']['basic_info']
# [{'type': 'full_row', 'data_type': 'cp', 'field_id': 83, 'option_id': 4643, 'field_name': 'ConditionUsed', 'field_label': 'Condition', 'option_label': 'Used', 'reporting_value_label': 'Used', 'is_indexable': False, 'link': 'sa/cpsearch//1729/1731/ConditionUsed:4643////////'}, {'type': 'full_row', 'data_type': 'cp', 'field_id': 875, 'option_id': 24871, 'option_img': 'https://opensooqui2.os-cdn.com/api/apiV/android/xh/cp/field_1450111166.png', 'field_name': 'car_make', 'field_label': 'Car Make', 'option_label': 'Hyundai', 'reporting_value_label': 'Hyundai', 'is_indexable': True, 'link': '/en/cars/cars-for-sale/hyundai'}, {'type': 'full_row', 'data_type': 'cp', 'field_id': 877, 'option_id': 26223, 'field_name': 'car_model', 'field_label': 'Model', 'option_label': 'H1', 'reporting_value_label': 'H1', 'is_indexable': True, 'link': '/en/cars/cars-for-sale/hyundai/o26223-h1'}, {'type': 'full_row', 'data_type': 'cp', 'field_id': 879, 'option_id': 31237, 'field_name': 'car_trim', 'field_label': 'Trim', 'option_label': 'Standard', 'reporting_value_label': 'Standard', 'is_indexable': True, 'link': '/en/cars/cars-for-sale/hyundai/o26223-h1/o31237-standard'}, {'type': 'full_row', 'data_type': 'cp', 'field_id': 9, 'option_id': 13637, 'field_name': 'Car_Year', 'field_label': 'Year', 'option_label': '2021', 'reporting_value_label': '2021', 'is_indexable': True, 'link': '/en/cars/cars-for-sale/hyundai/o26223-h1/o31237-standard/2021'}, {'type': 'full_row', 'data_type': 'cp', 'field_id': 81, 'option_id': 4633, 'field_name': 'Kilometers_Cars', 'field_label': 'Kilometers', 'option_label': '170,000 - 179,999', 'reporting_value_label': '170,000 - 179,999', 'is_indexable': False, 'link': 'sa/cpsearch//1729/1731/ConditionUsed:4643;Kilometers_Cars:4633////////'}, {'type': 'full_row', 'data_type': 'cp', 'field_id': 346, 'option_id': 7702, 'option_img': 'https://opensooqui2.os-cdn.com/api/apiV/android/xh/cp/BusMiniVan_7702.png', 'field_name': 'Cars_body_types', 'field_label': 'Body Type', 'option_label': 'Bus - Van', 'reporting_value_label': 'Bus - Van', 'is_indexable': False, 'link': 'sa/cpsearch//1729/1731/Cars_body_types:7702////////'}, {'type': 'full_row', 'data_type': 'cp', 'field_id': 838, 'option_id': 23142, 'field_name': 'Seats_Number', 'field_label': 'Number of Seats', 'option_label': '9', 'reporting_value_label': '9', 'is_indexable': False, 'link': 'sa/cpsearch//1729/1731/Seats_Number:23142////////'}, {'type': 'full_row', 'data_type': 'cp', 'field_id': 95, 'option_id': 4697, 'field_name': 'Fuel_Cars', 'field_label': 'Fuel', 'option_label': 'Gasoline', 'reporting_value_label': 'Gasoline', 'is_indexable': False, 'link': 'sa/cpsearch//1729/1731/Fuel_Cars:4697////////'}, {'type': 'full_row', 'data_type': 'cp', 'field_id': 119, 'option_id': 4795, 'field_name': 'Tramsmission_Cars', 'field_label': 'Transmission', 'option_label': 'Automatic', 'reporting_value_label': 'Automatic', 'is_indexable': False, 'link': 'sa/cpsearch//1729/1731/Tramsmission_Cars:4795////////'}, {'type': 'full_row', 'data_type': 'cp', 'field_id': 854, 'option_id': 24650, 'field_name': 'Car_Engine_Size', 'field_label': 'Engine Size (cc)', 'option_label': '1,000 - 1,999 cc', 'reporting_value_label': '1,000 - 1,999 cc', 'is_indexable': False, 'link': 'sa/cpsearch//1729/1731/Car_Engine_Size:24650////////'}, {'type': 'full_row', 'data_type': 'cp', 'field_id': 275, 'option_id': 7321, 'option_img': 'https://opensooqui2.os-cdn.com/api/apiV/android/xh/cp/field_1489327497.png', 'field_name': 'Car_Color', 'field_label': 'Exterior Color', 'option_label': 'Brown', 'reporting_value_label': 'Brown', 'is_indexable': False, 'link': 'sa/cpsearch//1729/1731/Car_Color:7321////////'}, {'type': 'full_row', 'data_type': 'cp', 'field_id': 881, 'option_id': 37313, 'option_img': 'https://opensooqui2.os-cdn.com/api/apiV/android/xh/cp/field_1489327515.png', 'field_name': 'Interior_Color', 'field_label': 'Interior Color', 'option_label': 'Grey', 'reporting_value_label': 'Grey', 'is_indexable': False, 'link': 'sa/cpsearch//1729/1731/Interior_Color:37313////////'}, {'type': 'full_row', 'data_type': 'cp', 'field_id': 825, 'option_id': 12541, 'field_name': 'Interior_Options', 'field_label': 'Interior Options', 'option_label': 'Air Condition', 'reporting_value_label': 'Air Condition', 'is_indexable': False, 'link': 'sa/cpsearch//1729/1731/Interior_Options:12541////////'}, {'type': 'full_row', 'data_type': 'cp', 'field_id': 827, 'option_id': 21581, 'field_name': 'Exterior_Options', 'field_label': 'Exterior Options', 'option_label': 'Spare Tyre', 'reporting_value_label': 'Spare Tyre', 'is_indexable': False, 'link': 'sa/cpsearch//1729/1731/Exterior_Options:21581////////'}, {'type': 'full_row', 'data_type': 'cp', 'field_id': 897, 'option_id': 21555, 'field_name': 'Technology_Options', 'field_label': 'Technology Options', 'option_label': 'Android Auto', 'reporting_value_label': 'Android Auto', 'is_indexable': False, 'link': 'sa/cpsearch//1729/1731/Technology_Options:21555////////'}, {'type': 'full_row', 'data_type': 'cp', 'field_id': 669, 'option_id': 18371, 'field_name': 'regional_specs', 'field_label': 'Regional Specs', 'option_label': 'GCC Specs', 'reporting_value_label': 'GCC Specs', 'is_indexable': False, 'link': 'sa/cpsearch//1729/1731/regional_specs:18371////////'}, {'type': 'full_row', 'data_type': 'cp', 'field_id': 671, 'option_id': 18387, 'field_name': 'body_condition', 'field_label': 'Body Condition', 'option_label': 'Excellent with no defects', 'reporting_value_label': 'Excellent with no defects', 'is_indexable': False, 'link': 'sa/cpsearch//1729/1731/body_condition:18387////////'}, {'type': 'full_row', 'data_type': 'cp', 'field_id': 673, 'option_id': 18393, 'field_name': 'paint', 'field_label': 'Paint', 'option_label': 'Original Paint', 'reporting_value_label': 'Original Paint', 'is_indexable': False, 'link': 'sa/cpsearch//1729/1731/paint:18393////////'}, {'type': 'full_row', 'data_type': 'cp', 'field_id': 323, 'option_id': 7513, 'field_name': 'Payment_Method', 'field_label': 'Payment Method', 'option_label': 'Cash', 'reporting_value_label': 'Cash', 'is_indexable': False, 'link': 'sa/cpsearch//1729/1731/Payment_Method:7513////////'}, {'type': 'full_row', 'data_type': 'post_id', 'field_label': 'Listing Id', 'option_label': '265930847'}, {'type': 'full_row', 'data_type': 'post_date', 'field_label': 'Published Date', 'option_label': '03-07-2025'}, {'type': 'full_row', 'data_type': 'category', 'field_label': 'Category', 'option_label': 'Car and Bikes', 'reporting_value_label': 'Autos', 'link': 'cars'}, {'type': 'full_row', 'data_type': 'sub_category', 'field_label': 'Sub Category', 'option_label': 'Cars For Sale', 'reporting_value_label': 'CarsForSale', 'link': 'cars-for-sale'}, {'type': 'full_row', 'data_type': 'price'}, {'typ
#{'type': 'full_row', 'data_type': 'vin', 'cps': 'Hyundai . H1 . 2021'}]
#
#
        yield item

    def errback_page(self, failure):
        self.logger.error(f"[Error❌] Failed to load page: {failure.request.url}")

    def errback_ad(self, failure):
        self.logger.error(f"[Error❌] Failed to load ad: {failure.request.url}")

