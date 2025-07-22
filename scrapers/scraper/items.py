import scrapy
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any


class CoreItem(scrapy.Item):
    # ——— Core identifiers ———
    ad_id: str = scrapy.Field()
    url: str = scrapy.Field()
    website: str = scrapy.Field()

    # ——— Listing basics ———
    title: str = scrapy.Field()
    price: Decimal = scrapy.Field()
    currency: str = scrapy.Field()

    # ——— Vehicle specs ———
    brand: str = scrapy.Field()
    model: str = scrapy.Field()
    year: int = scrapy.Field()
    trim: str = scrapy.Field()
    mileage: int = scrapy.Field()
    mileage_unit: str = scrapy.Field()
    fuel_type: str = scrapy.Field()
    transmission_type: str = scrapy.Field()
    body_type: str = scrapy.Field()
    condition: str = scrapy.Field()
    color: str = scrapy.Field()

    # ——— Seller info ———
    seller: str = scrapy.Field()
    seller_type: str = scrapy.Field()

    # ——— Location ———
    location_city: str = scrapy.Field()
    location_region: str = scrapy.Field()

    # ——— Media & timing ———
    image_url: str = scrapy.Field()
    number_of_images: int = scrapy.Field()
    post_date: datetime = scrapy.Field()
    date_scraped: datetime = scrapy.Field()


class DubizzleItem(CoreItem):
    # ——— JSON-LD fields ———
    name: Optional[str] = scrapy.Field()
    sku: Optional[str] = scrapy.Field()
    description: Optional[str] = scrapy.Field()
    image_urls: Optional[List[str]] = scrapy.Field()
    price_valid_until: Optional[datetime] = scrapy.Field()

    # ——— Basic info & specs ———
    new_used: Optional[str] = scrapy.Field()
    source: Optional[str] = scrapy.Field()

    # ——— Usage & ownership ———
    kilometers: Optional[int] = scrapy.Field()
    doors: Optional[int] = scrapy.Field()
    seats: Optional[int] = scrapy.Field()
    owners: Optional[int] = scrapy.Field()
    interior: Optional[str] = scrapy.Field()
    air_con: Optional[str] = scrapy.Field()
    ownership_type: Optional[str] = scrapy.Field()

    # ——— Price breakdown ———
    price_type: Optional[str] = scrapy.Field()

    # ——— Seller & agency ———
    seller_verified: Optional[bool] = scrapy.Field()
    seller_id: Optional[str] = scrapy.Field()
    agency_id: Optional[str] = scrapy.Field()
    agency_name: Optional[str] = scrapy.Field()
    is_agent: Optional[bool] = scrapy.Field()

    # ——— Location details ———
    loc_id: Optional[str] = scrapy.Field()
    loc_name: Optional[str] = scrapy.Field()
    loc_breadcrumb: Optional[str] = scrapy.Field()
    loc_1_id: Optional[str] = scrapy.Field()
    loc_1_name: Optional[str] = scrapy.Field()
    loc_2_id: Optional[str] = scrapy.Field()
    loc_2_name: Optional[str] = scrapy.Field()

    # ——— Category & page meta ———
    category_1_id: Optional[int] = scrapy.Field()
    category_1_name: Optional[str] = scrapy.Field()
    category_2_id: Optional[int] = scrapy.Field()
    category_2_name: Optional[str] = scrapy.Field()
    page_type: Optional[str] = scrapy.Field()
    website_section: Optional[str] = scrapy.Field()

    # ——— Media & extras ———
    has_video: Optional[bool] = scrapy.Field()
    has_panorama: Optional[bool] = scrapy.Field()
    deliverable: Optional[bool] = scrapy.Field()
    delivery_option: Optional[str] = scrapy.Field()


class OpenSooqItem(CoreItem):
    engine_size: Optional[str] = scrapy.Field()
    payment_method: Optional[str] = scrapy.Field()
    seats: Optional[int] = scrapy.Field()
    interior_color: Optional[str] = scrapy.Field()
    name: Optional[str] = scrapy.Field()
    source: Optional[str] = scrapy.Field()
    paint_quality: Optional[str] = scrapy.Field()
    body_condition: Optional[str] = scrapy.Field()
    category: Optional[str] = scrapy.Field()
    subcategory: Optional[str] = scrapy.Field()
    interior_options: Optional[List[str]] = scrapy.Field()
    exterior_options: Optional[List[str]] = scrapy.Field()
    technology_options: Optional[List[str]] = scrapy.Field()
    description: Optional[str] = scrapy.Field()

    seller_url: Optional[str] = scrapy.Field()
    seller_id: Optional[str] = scrapy.Field()
    is_shop: Optional[bool] = scrapy.Field()
    is_pro_buyer: Optional[bool] = scrapy.Field()
    seller_verified: Optional[bool] = scrapy.Field()
    rating_avg: Optional[Decimal] = scrapy.Field()
    number_of_ratings: Optional[int] = scrapy.Field()
    seller_joined: Optional[datetime] = scrapy.Field()
    response_time: Optional[str] = scrapy.Field()

    price_valid_until: Optional[datetime] = scrapy.Field()
    listing_status: Optional[str] = scrapy.Field()
    user_target_type: Optional[str] = scrapy.Field()
    post_map: Optional[Dict[str, Any]] = scrapy.Field()


class CarSwitchItem(CoreItem):
    secondary_id: Optional[str] = scrapy.Field()
    regional_specs: Optional[Dict[str, Any]] = scrapy.Field()
    uuid: Optional[str] = scrapy.Field()
    cylinders: Optional[int] = scrapy.Field()
    engine_size: Optional[str] = scrapy.Field()
    asking_price: Optional[Decimal] = scrapy.Field()
    is_paid: Optional[bool] = scrapy.Field()
    is_featured: Optional[bool] = scrapy.Field()
    drive_type: Optional[str] = scrapy.Field()
    variant: Optional[str] = scrapy.Field()
    listing_rank: Optional[int] = scrapy.Field()
    status: Optional[str] = scrapy.Field()
    zoho_car_id: Optional[str] = scrapy.Field()
    overall_condition: Optional[str] = scrapy.Field()
    is_accidented: Optional[bool] = scrapy.Field()
    accident_detail: Optional[str] = scrapy.Field()
    air_bags_condition: Optional[str] = scrapy.Field()
    chassis_condition: Optional[str] = scrapy.Field()
    engine_condition: Optional[str] = scrapy.Field()
    gear_box_condition: Optional[str] = scrapy.Field()
    service_history: Optional[str] = scrapy.Field()
    service_history_verified: Optional[bool] = scrapy.Field()
    crossed_price: Optional[Decimal] = scrapy.Field()
    last_price: Optional[Decimal] = scrapy.Field()
    original_success_fee: Optional[Decimal] = scrapy.Field()
    final_success_fee: Optional[Decimal] = scrapy.Field()
    success_fee_type: Optional[str] = scrapy.Field()
    success_fee_promo_code: Optional[str] = scrapy.Field()
    price_dropped_badge: Optional[bool] = scrapy.Field()
    price_dropped_badge_expiration: Optional[datetime] = scrapy.Field()
    alloy_rims: Optional[bool] = scrapy.Field()
    rim_size: Optional[str] = scrapy.Field()
    roof_type: Optional[str] = scrapy.Field()
    no_of_keys: Optional[int] = scrapy.Field()
    currently_financed: Optional[bool] = scrapy.Field()
    bank_name: Optional[str] = scrapy.Field()
    cash_buyer_only: Optional[bool] = scrapy.Field()
    warranty: Optional[str] = scrapy.Field()
    warranty_expiration_date: Optional[datetime] = scrapy.Field()
    warranty_mileage_limit: Optional[int] = scrapy.Field()
    service_contract: Optional[str] = scrapy.Field()
    service_contract_verified: Optional[bool] = scrapy.Field()
    classified_web_link: Optional[str] = scrapy.Field()
    special_about_car: Optional[str] = scrapy.Field()
    registration_city_name: Optional[str] = scrapy.Field()
    cappasity_link: Optional[str] = scrapy.Field()
    first_owner: Optional[str] = scrapy.Field()
    fair_value_override: Optional[Decimal] = scrapy.Field()
    inspection_started_by: Optional[str] = scrapy.Field()
    seller_nationality: Optional[str] = scrapy.Field()
    created_at: Optional[datetime] = scrapy.Field()
    updated_at: Optional[datetime] = scrapy.Field()
    buyer_services: Optional[List[str]] = scrapy.Field()
    show_all_details: Optional[bool] = scrapy.Field()
    fair_value_computation_id: Optional[str] = scrapy.Field()
    fair_value: Optional[Decimal] = scrapy.Field()
    confidence: Optional[Decimal] = scrapy.Field()
    explanation_en: Optional[str] = scrapy.Field()
    explanation_ar: Optional[str] = scrapy.Field()
    min_fair_value: Optional[Decimal] = scrapy.Field()
    max_fair_value: Optional[Decimal] = scrapy.Field()


class SyarahItem(CoreItem):
    is_sold: Optional[bool] = scrapy.Field()
    is_deleted: Optional[bool] = scrapy.Field()
    is_preowned: Optional[bool] = scrapy.Field()
    interior_color: Optional[str] = scrapy.Field()
    source: Optional[str] = scrapy.Field()
    cylinders: Optional[int] = scrapy.Field()
    engine_size: Optional[str] = scrapy.Field()
    drive_type: Optional[str] = scrapy.Field()
    number_of_keys: Optional[int] = scrapy.Field()
    seats: Optional[int] = scrapy.Field()
    engine_type: Optional[str] = scrapy.Field()
