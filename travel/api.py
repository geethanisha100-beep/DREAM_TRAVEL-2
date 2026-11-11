from django.urls import include, path
from rest_framework.permissions import IsAuthenticated
from rest_framework import filters, routers, serializers, viewsets
from .models import Booking, Destination, Hotel, TourPackage, Vehicle

def make(model, extra=()):
    class S(serializers.ModelSerializer):
        class Meta:
            fields = "__all__"
    S.Meta.model = model
    return S

class PackageSerializer(serializers.ModelSerializer):
    rating = serializers.FloatField(read_only=True)
    stops = serializers.ListField(read_only=True)
    class Meta:
        model = TourPackage
        fields = "__all__"

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ["reference", "kind", "total", "status", "start_date", "end_date", "created"]

def viewset(model, serializer, search):
    class VS(viewsets.ReadOnlyModelViewSet):
        queryset = model.objects.all()
        serializer_class = serializer
        filter_backends = [filters.SearchFilter]
        search_fields = search
    return VS

class MyBookings(viewsets.ReadOnlyModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)

router = routers.DefaultRouter()
router.register("destinations", viewset(Destination, make(Destination), ["name", "city", "district"]))
router.register("packages", viewset(TourPackage, PackageSerializer, ["title", "destination__name", "starting_location"]))
router.register("vehicles", viewset(Vehicle, make(Vehicle), ["name", "model_name"]))
router.register("hotels", viewset(Hotel, make(Hotel), ["name", "location"]))
router.register("my-bookings", MyBookings, basename="my-bookings")
urlpatterns = [path("", include(router.urls))]
