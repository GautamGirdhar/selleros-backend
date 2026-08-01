from ninja import Schema
from typing import Literal


class PricingInput(Schema):
    platform: Literal["meesho", "amazon", "flipkart"]
    product_cost: float
    gst_rate: float
    desired_profit: float
    return_rate: float          # % of orders returned
    damage_rate: float          # % of product cost lost to damage
    shipping_cost: float
    ad_spend: float


class PricingOutput(Schema):
    listing_price: float
    total_cost: float
    profit: float
    margin: float
    roi: float
    gst: float
    product_cost: float
    shipping_cost: float
    platform_fee: float
    return_cost: float
    damaged_cost: float
    ad_spend: float