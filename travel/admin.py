from django.contrib import admin
from .models import *

class PhotoInline(admin.TabularInline):
    model = PackagePhoto
    extra = 3
    max_num = 3

class RoomInline(admin.TabularInline):
    model = HotelRoom
    extra = 1

@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "district","category")
    list_filter = ( "city","category")
    search_fields = ("name", "city","district")

@admin.register(TourPackage)
class PackageAdmin(admin.ModelAdmin):
    list_display = ("title", "destination", "starting_location", "price_per_person", "available_seats", "is_available")
    list_filter = ("is_available","destination")
    search_fields = ("title", "starting_location", "destination__name")
    inlines = [PhotoInline]

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("name", "model_name", "kind", "quantity", "is_available", "rent_per_day")
    list_filter = ("kind", "is_available")

@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "rating", "is_available")
    inlines = [RoomInline]

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("reference", "user", "kind", "total", "status", "created")
    list_filter = ("kind", "status")
    search_fields = ("reference", "traveller_name", "contact")
    readonly_fields = ("reference", "total")

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("booking", "amount", "status", "transaction_id", "paid_at")
    list_filter = ("status",)
    readonly_fields = ("booking", "amount", "status", "transaction_id", "paid_at", "contact")

admin.site.register([Review, Wishlist])
