from django.urls import path
from . import views as v

urlpatterns = [
    path("", v.home, name="home"),
    path("destinations/", v.destinations, name="destinations"),
    path("destinations/<int:pk>/", v.destination_detail, name="destination_detail"),
    path("packages/", v.packages, name="packages"),
    path("packages/<int:pk>/", v.package_detail, name="package_detail"),
    path("packages/<int:pk>/wishlist/", v.wishlist_toggle, name="wishlist_toggle"),
    path("vehicles/", v.vehicles, name="vehicles"),
    path("hotels/", v.hotels, name="hotels"),
    path("book/<str:kind>/<int:pk>/", v.book, name="book"),
    path("payment/<str:ref>/", v.payment, name="payment"),
    path("payment/<str:ref>/qr.png", v.qr_png, name="qr_png"),
    path("payment/<str:ref>/sandbox/", v.sandbox_pay, name="sandbox_pay"),
    path("payment/<str:ref>/receipt/", v.receipt, name="receipt"),
    path("payments/webhook/", v.payment_webhook, name="payment_webhook"),
]
