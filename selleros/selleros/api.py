from ninja import NinjaAPI

from accounts.api import router as auth_router
from pricecalculator.api import router as pricing_router

api = NinjaAPI(
    title="SellerOS API",
    version="1.0.0",
)

api.add_router(
    "/auth/",
    auth_router,
)
api.add_router("/pricing", pricing_router)