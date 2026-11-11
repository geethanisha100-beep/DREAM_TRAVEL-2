import uuid
from datetime import date
from decimal import Decimal
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg

RATING = [MinValueValidator(0), MaxValueValidator(5)]

class Destination(models.Model):
    CATEGORIES = [("hills", "Hills"), ("beach", "Beaches"), ("adventure", "Adventure"),
                  ("heritage", "Heritage"), ("honeymoon", "Honeymoon")]
    name = models.CharField(max_length=100)
    city = models.CharField(max_length=80)
    district = models.CharField(max_length=80)
    country = models.CharField(max_length=80, default="India")
    address_or_landmark = models.CharField(max_length=200, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    map_url = models.URLField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORIES)
    description = models.TextField()
    photo = models.ImageField(upload_to="destinations/")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def directions_url(self):
        if self.map_url:
            return self.map_url
        if self.latitude is not None and self.longitude is not None:
            return f"https://www.google.com/maps?q={self.latitude},{self.longitude}"
        return ""

class TourPackage(models.Model):
    title = models.CharField(max_length=150)
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="packages")
    starting_location = models.CharField(max_length=100)
    pickup_point = models.CharField(max_length=150, blank=True)
    pickup_map_url = models.URLField(blank=True)
    route_or_itinerary = models.TextField(help_text="One stop per line, in order.")
    travel_start_date = models.DateField()
    travel_end_date = models.DateField()
    duration = models.CharField(max_length=40, help_text="e.g. 4 days / 3 nights")
    price_per_person = models.DecimalField(max_digits=10, decimal_places=2)
    additional_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                             help_text="Fixed extra charge per booking (taxes, permits).")
    available_seats = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)
    description = models.TextField()

    class Meta:
        ordering = ["travel_start_date"]

    def __str__(self):
        return self.title

    @property
    def stops(self):
        return [s.strip() for s in self.route_or_itinerary.splitlines() if s.strip()]

    @property
    def bookable(self):
        return self.is_available and self.available_seats > 0 and self.travel_start_date >= date.today()

    @property
    def rating(self):
        return round(self.reviews.aggregate(a=Avg("rating"))["a"] or 0, 1)

class PackagePhoto(models.Model):
    package = models.ForeignKey(TourPackage, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="packages/")

class Review(models.Model):
    package = models.ForeignKey(TourPackage, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlist")
    package = models.ForeignKey(TourPackage, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("user", "package")

class Vehicle(models.Model):
    KINDS = [("two", "Two-wheeler"), ("four", "Four-wheeler")]
    name = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100)
    kind = models.CharField(max_length=4, choices=KINDS)
    photo = models.ImageField(upload_to="vehicles/")
    description = models.TextField(blank=True)
    quantity = models.PositiveIntegerField(default=1)
    is_available = models.BooleanField(default=True)
    rent_per_day = models.DecimalField(max_digits=8, decimal_places=2)
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=0, validators=RATING)

    def __str__(self):
        return f"{self.name} {self.model_name}"

    @property
    def bookable(self):
        return self.is_available and self.quantity > 0

class Hotel(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=150)
    photo = models.ImageField(upload_to="hotels/")
    food_details = models.TextField(blank=True)
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=0, validators=RATING)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class HotelRoom(models.Model):
    TYPES = [("single", "Single"), ("double", "Double"), ("family", "Family"), ("suite", "Suite")]
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="rooms")
    room_type = models.CharField(max_length=10, choices=TYPES)
    charge_per_day = models.DecimalField(max_digits=8, decimal_places=2)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.hotel.name} - {self.get_room_type_display()}"

def new_ref():
    return "DT" + uuid.uuid4().hex[:8].upper()

class Booking(models.Model):
    KINDS = [("package", "Package"), ("vehicle", "Vehicle"), ("hotel", "Hotel")]
    STATUS = [("pending", "Pending"), ("confirmed", "Confirmed"), ("cancelled", "Cancelled")]
    reference = models.CharField(max_length=12, unique=True, default=new_ref, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings")
    kind = models.CharField(max_length=10, choices=KINDS)
    package = models.ForeignKey(TourPackage, null=True, blank=True, on_delete=models.PROTECT)
    vehicle = models.ForeignKey(Vehicle, null=True, blank=True, on_delete=models.PROTECT)
    room = models.ForeignKey(HotelRoom, null=True, blank=True, on_delete=models.PROTECT)
    traveller_name = models.CharField(max_length=80)
    contact = models.CharField(max_length=150, verbose_name="Phone or email")
    address = models.TextField()
    message = models.TextField(blank=True)
    members = models.PositiveIntegerField(default=1)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS, default="pending")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.reference

    @property
    def days(self):
        if self.start_date and self.end_date:
            return max((self.end_date - self.start_date).days, 1) if self.kind == "hotel" \
                else (self.end_date - self.start_date).days + 1
        return 1

    def calculate(self):
        """Server-side total. Never trust a total sent by the browser."""
        if self.kind == "package":
            p = self.package
            return p.price_per_person * self.members + p.additional_charges
        if self.kind == "vehicle":
            return self.vehicle.rent_per_day * self.days
        return self.room.charge_per_day * self.days

    @property
    def item(self):
        return self.package or self.vehicle or self.room

class Payment(models.Model):
        METHODS = [("upi", "UPI"), ("card", "Card"), ("cod", "Cash on delivery")]
        method = models.CharField(max_length=10, choices=METHODS, default="upi")
        card_brand = models.CharField(max_length=20, blank=True)
        card_last4 = models.CharField(max_length=4, blank=True)
        STATUS = [("pending", "Pending"), ("success", "Success"), ("failed", "Failed")]
        booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="payment")
        amount = models.DecimalField(max_digits=12, decimal_places=2)
        status = models.CharField(max_length=10, choices=STATUS, default="pending")
        transaction_id = models.CharField(max_length=100, blank=True)
        contact = models.CharField(max_length=150)
        created = models.DateTimeField(auto_now_add=True)
        paid_at = models.DateTimeField(null=True, blank=True)

def __str__(self):
     return f"{self.booking.reference} {self.status}"
