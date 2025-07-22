import json
import re
from datetime import datetime
from urllib.parse import urlencode, urlparse, parse_qs
from scrapy import Request, Spider
from scraper.items import CarSwitchItem
from scraper.maps import get_body_type_code, get_transmission_code, get_color_code


class CarSwitchTemplateSpider(Spider):
    # NO `name` here; subclasses must provide it

    # Typesense API configuration; Hardcoded for now
    base_api = "https://hd7x32pwz5l1k9frp-1.a1.typesense.net/collections/cars_prod/documents/search"
    api_key  = "Tv1qKAFwcLU5hFb3W2Y2u4Xirp3IG6Ld"

    # Default search parameters; override as needed
    per_page: int = 250
    sort_by: str = "rank:asc,updatedAt:desc"
    filter_by: str = 'countryName:="ksa"'
    query_by: str = "makeName,modelName"
    include_fields: str = "id,uuid,cityName,makeName,modelName,year"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.page = 1

    def start_requests(self):
        # Kick off at the first page
        yield Request(
            url=self._api_url(self.page),
            callback=self.parse_page,
            meta={"page": self.page},
            dont_filter=True,
        )

    def _api_url(self, page: int) -> str:
        qs = {
            "q": "*",
            "query_by": self.query_by,
            "filter_by": self.filter_by,
            "per_page": str(self.per_page),
            "page": str(page),
            "sort_by": self.sort_by,
            "include_fields": self.include_fields,
            "x-typesense-api-key": self.api_key,
        }
        return f"{self.base_api}?{urlencode(qs)}"

    def parse_page(self, response):
        page = response.meta["page"]
        data = json.loads(response.text)
        hits = data.get("hits", [])

        if not hits:
            self.logger.info(f"[Done] No more results at page {page}")
            return

        self.logger.info(f"[Page {page}] Retrieved {len(hits)} listings")

        for hit in hits:
            doc = hit.get("document", {})
            url = self.build_listing_url(doc)
            yield Request(url, callback=self.parse_ad, errback=self.errback_ad)

        # Schedule next page
        next_page = page + 1
        yield Request(
            url=self._api_url(next_page),
            callback=self.parse_page,
            meta={"page": next_page},
            dont_filter=True,
        )

    @staticmethod
    def build_listing_url( doc: dict) -> str:
        return (
            f"https://ksa.carswitch.com/"
            f"{doc['cityName']}/used-car/"
            f"{doc['makeName']}/{doc['modelName']}/{doc['year']}/{doc['id']}"
        )

    def parse_ad(self, response):

        qs = parse_qs(urlparse(response.url).query)
        current_page = int(qs.get("page", ["1"])[0])
        self.logger.info(f"[Loaded📄] Page #{current_page} → {response.url}")

        ad_id = response.url.split('/')[-1].split('-')[0]


        item = CarSwitchItem()
        try:
            data = self._extract_car_data(response)
        except ValueError as e:
            self.logger.error(e)
            return

#

        item['ad_id'] = ad_id
        item['url'] = response.url
        item['website'] = "CarSwitch"


        # ——— Listing basics ———

        car_details = data['serverData']['car']['car']

        item['price'] = car_details['listingPrice']
        item['currency'] = "SAR"

        # ——— Vehicle specs ———
        item['brand'] = car_details['makeName'][0].upper() +  car_details['makeName'][1:]
        item['model'] = car_details['modelName'][0].upper() +  car_details['modelName'][1:]
        item['year'] = car_details['year']
        item['trim'] = car_details['optionLevel'].upper()

        item['title'] = item['brand'] + " " +item['model'] + " " + item['trim']

        item['mileage'] = car_details['mileage']
        item['mileage_unit'] = 'kmt'
        item['fuel_type'] = car_details['fuelType']
        raw_trans = car_details['transmission']
        item['transmission_type'] = get_transmission_code(raw_trans)
        raw_body = car_details['bodyType']
        item['body_type'] = get_body_type_code(raw_body)
        item['condition'] = 'Used'
        raw_color =  car_details['color']
        item['color'] = get_color_code(raw_color)

        # ——— Seller info ———
        listingType = car_details['listingType']
        if listingType == 'safe_switch':
          item['seller'] = car_details['zohoSellerId']
          item['seller_type'] = 'Private'
        elif listingType == 'self_switch':
          item['seller'] = car_details['zohoSellerId']
          item['seller_type'] = 'Private'
        else:
            item['seller'] = car_details['zohoSellerId']
            item['seller_type'] = 'Dealership'



        # ——— Location ———
        item['location_city'] = car_details['cityName'][0].upper() + car_details['cityName'][1:]
        item['location_region'] = car_details['areaName'][0].upper() + car_details['areaName'][1:]
        cover_photo = data['serverData']['car']['carAttachments'][0]['url']

        # ——— Media & timing ———
        image_url = self.build_image_url(cover_photo)

        item['image_url'] = image_url
        item['number_of_images'] = len(data['serverData']['car']['carAttachments'])
        dt_str =  car_details['firstPublishedOn']

        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        item['post_date'] = dt
        item['date_scraped'] = datetime.now()


        #--- EXTRA FEATURES:
        item['secondary_id'] = self.safe_get(data, 'carIds', 'secondaryId')
        item['uuid'] = self.safe_get(data, 'serverData', 'car', 'car', 'uuid')
        item['regional_specs'] = self.safe_get(data, 'serverData', 'car', 'car', 'regionalSpecs')
        item['cylinders'] = self.safe_get(data, 'serverData', 'car', 'car', 'cylinders')
        item['engine_size'] = self.safe_get(data, 'serverData', 'car', 'car', 'engineSize')
        item['asking_price'] = self.safe_get(data, 'serverData', 'car', 'car', 'askingPrice')
        item['is_paid'] = self.safe_get(data, 'serverData', 'car', 'car', 'isPaid', default=False)
        item['is_featured'] = self.safe_get(data, 'serverData', 'car', 'car', 'isFeatured', default=False)
        item['drive_type'] = self.safe_get(data, 'serverData', 'car', 'car', 'driveType')
        item['variant'] = self.safe_get(data, 'serverData', 'car', 'car', 'variant')
        item['seats'] = self.safe_get(data, 'serverData', 'car', 'car', 'noOfSeats')
        item['listing_rank'] = self.safe_get(data, 'serverData', 'car', 'car', 'listingRank')
        item['status'] = self.safe_get(data, 'serverData', 'car', 'car', 'status')
        item['zoho_car_id'] = self.safe_get(data, 'serverData', 'car', 'car', 'zohoCarId')

        car_details = self.safe_get(data, 'serverData', 'car', 'carDetails', default={})
        item['overall_condition'] = car_details.get('overallCondition')
        item['is_accidented'] = car_details.get('isAccidented', False)
        item['accident_detail'] = car_details.get('accidentDetail')
        item['air_bags_condition'] = car_details.get('airBagsCondition')
        item['chassis_condition'] = car_details.get('chassisCondition')
        item['engine_condition'] = car_details.get('engineCondition')
        item['gear_box_condition'] = car_details.get('gearBoxCondition')
        item['service_history'] = car_details.get('serviceHistory')
        item['service_history_verified'] = car_details.get('serviceHistoryVerified', False)
        item['crossed_price'] = car_details.get('crossedPrice')
        item['last_price'] = car_details.get('lastPrice')
        item['fair_value_computation_id'] = car_details.get('fairValueComputationId')
        item['original_success_fee'] = car_details.get('originalSuccessFee')
        item['final_success_fee'] = car_details.get('finalSuccessFee')
        item['success_fee_type'] = car_details.get('successFeeType')
        item['success_fee_promo_code'] = car_details.get('successFeePromoCode')
        item['price_dropped_badge'] = car_details.get('priceDroppedBadge')
        item['price_dropped_badge_expiration'] = car_details.get('priceDroppedBadgeExpiration')
        item['alloy_rims'] = car_details.get('alloyRims', False)
        item['rim_size'] = car_details.get('rimSize')
        item['roof_type'] = car_details.get('roofType')
        item['no_of_keys'] = car_details.get('noOfKeys')
        item['currently_financed'] = car_details.get('currentlyFinanced', False)
        item['bank_name'] = car_details.get('bankName')
        item['cash_buyer_only'] = car_details.get('cashBuyerOnly', False)
        item['warranty'] = car_details.get('warranty')
        item['warranty_expiration_date'] = car_details.get('warrantyExpirationDate')
        item['warranty_mileage_limit'] = car_details.get('warrantyMileageLimit')
        item['service_contract'] = car_details.get('serviceContract')
        item['service_contract_verified'] = car_details.get('serviceContractVerified', False)
        item['classified_web_link'] = car_details.get('classifiedWebLink')
        item['special_about_car'] = car_details.get('specialAboutCar')
        item['registration_city_name'] = car_details.get('registrationCityName')

        item['cappasity_link'] = car_details.get('cappasityLink')
        item['first_owner'] = car_details.get('firstOwner')
        item['fair_value_override'] = car_details.get('fairValueOverride')
        item['inspection_started_by'] = car_details.get('inspectionStartedBy')
        item['seller_nationality'] = car_details.get('sellerNationality')
        item['created_at'] = car_details.get('createdAt')
        item['updated_at'] = car_details.get('updatedAt')

        item['buyer_services'] = car_details.get('buyerServices')
        item['show_all_details'] = car_details.get('showAllDetails', False)

        fair_obj = car_details.get('fairValueObject', {})
        item['fair_value'] = fair_obj.get('fairValue')
        item['confidence'] = fair_obj.get('confidence')
        item['explanation_en'] = fair_obj.get('explanationEn')
        item['explanation_ar'] = fair_obj.get('explanationAr')
        item['min_fair_value'] = fair_obj.get('minFairValue')
        item['max_fair_value'] = fair_obj.get('maxFairValue')


        yield item



    def errback_ad(self, failure):
        self.logger.error("[Error] Failed to load ad: %s", failure.request.url)

    @staticmethod
    def safe_get(dct, *keys, default=None):
        for key in keys:
            if not isinstance(dct, dict) or key not in dct:
                return default
            dct = dct[key]
        return dct


    def _extract_car_data(self, response ) -> dict:
           # Returns the entire self.data push list
        all_chunks = response.xpath(    '//script[contains(text(),"self.__next_f.push")]/text()').getall()
        ad_id = response.url.split('/')[-1].split('-')[0]
        target = f'\\"id\\":\\"{ad_id}\\"'
        matches = [s for s in all_chunks if target in s]
        script_text = matches[0] if matches else None

        if not script_text:
            self.logger.error("Could not find JSON blob for ad %s", ad_id)
            return
        raw = re.search(    r'self\.__next_f\.push\(\[\d+,(.*)\]\)',    script_text,    re.S).group(1)
        literal = json.loads(raw)
        _, payload_str = literal.split(":", 1)
        arr = json.loads(payload_str)
        children = arr[1]
        data = children[3]['children'][1][3] # hardcoded path
        return data


    def build_image_url(cover_photo:str) -> str:
        original_base = 'https://images.carswitch.com/'
        new_base = 'https://d1esl34bhh6pms.cloudfront.net/cars/used/images/611x456/'


        # Build the full image URL first
        image_url = original_base + cover_photo + '?.webp'

        # Check if:
        # - coverPhoto is a UUID
        # - and does NOT contain .jpg, .jpeg, or .png
        # - and does NOT contain slashes (no subfolders like 682652/...)
        if (re.fullmatch(r'[0-9a-fA-F\-]{36}', cover_photo) and not any(ext in cover_photo.lower() for ext in ['.jpg', '.jpeg', '.png'])):
            # Replace domain
            image_url = new_base + cover_photo + '?.webp'
        return image_url



