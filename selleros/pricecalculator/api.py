from ninja import Router

from .schemas import PricingInput, PricingOutput

router = Router(tags=["Pricing"])

# Illustrative marketplace commission rates — these vary by category and
# change over time. Verify current rates on each platform's seller policy
# page before relying on this for real pricing decisions.
PLATFORM_COMMISSION_RATES = {
    "meesho": 5.0,
    "amazon": 17.0,
    "flipkart": 14.0,
}


@router.post("/calculate", response=PricingOutput)
def calculate(request, data: PricingInput):
    commission_rate = PLATFORM_COMMISSION_RATES[data.platform] / 100

    return_cost = (data.return_rate / 100) * data.shipping_cost
    damaged_cost = (data.damage_rate / 100) * data.product_cost

    # Costs before commission and before profit
    base_cost = (
        data.product_cost
        + return_cost
        + damaged_cost
        + data.ad_spend
    )

    # Commission is a % of the listing price itself (before GST), so we solve
    # for listing_price algebraically instead of applying it as a flat cost:
    #   listing_price = base_cost + profit + (commission_rate * listing_price)
    #   listing_price * (1 - commission_rate) = base_cost + profit
    pre_gst_price = (base_cost + data.desired_profit) / (1 - commission_rate)
    platform_fee = pre_gst_price - (base_cost + data.desired_profit)

    gst = pre_gst_price * data.gst_rate / 100
    final_price = pre_gst_price + gst

    total_cost = base_cost + platform_fee

    roi = (data.desired_profit / total_cost) * 100 if total_cost else 0
    margin = (data.desired_profit / final_price) * 100 if final_price else 0

    return {
        "listing_price": round(final_price, 2),
        "total_cost": round(total_cost, 2),
        "profit": round(data.desired_profit, 2),
        "margin": round(margin, 2),
        "roi": round(roi, 2),
        "gst": round(gst, 2),
        "product_cost": round(data.product_cost, 2),
        "shipping_cost": round(data.shipping_cost, 2),
        "platform_fee": round(platform_fee, 2),
        "return_cost": round(return_cost, 2),
        "damaged_cost": round(damaged_cost, 2),
        "ad_spend": round(data.ad_spend, 2),
    }