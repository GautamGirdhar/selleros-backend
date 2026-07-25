from ninja import NinjaAPI

from accounts.api import router as auth_router

api = NinjaAPI(
    title="SellerOS API",
    version="1.0.0",
)

api.add_router(
    "/auth/",
    auth_router,
)