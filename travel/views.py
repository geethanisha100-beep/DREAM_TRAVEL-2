import hashlib, hmac, io, json
import re 
from urllib.parse import urlencode
from decimal import Decimal
import qrcode
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F, Q
from django.http import FileResponse, Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from .forms import BookingForm
from .models import (Booking, Destination, Hotel, Payment, PackagePhoto, Review, TourPackage, Vehicle, Wishlist)

def home(request):
    return render(request, "travel/home.html", {
        "destinations": Destination.objects.all()[:3],
        "packages": TourPackage.objects.filter(is_available=True)[:3]})

def destinations(request):
    qs = Destination.objects.all()
    q, district, cat = (request.GET.get(k, "").strip() for k in ("q", "district", "category"))
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(city__icontains=q) | Q(district__icontains=q))
    if district: qs = qs.filter(district=district)
    if cat: qs = qs.filter(category=cat)
    return render(request, "travel/destinations.html", {
        "items": qs, "q": q, "district": district, "cat": cat,
        "districts": Destination.objects.values_list("district", flat=True).distinct(),
        "categories": Destination.CATEGORIES})

def destination_detail(request, pk):
    d = get_object_or_404(Destination, pk=pk)
    return render(request, "travel/destination_detail.html", {"d": d})

def packages(request):
    qs = TourPackage.objects.select_related("destination").prefetch_related("photos")
    q,  cat, start = (request.GET.get(k, "").strip() for k in ("q",  "category", "start"))
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(destination__name__icontains=q) | Q(destination__city__icontains=q))
    if cat: qs = qs.filter(destination__category=cat)
    if start: qs = qs.filter(starting_location__icontains=start)
    return render(request, "travel/packages.html", {
        "items": qs, "q": q, "cat": cat, "start": start,
        "categories": Destination.CATEGORIES})

def package_detail(request, pk):
    p = get_object_or_404(TourPackage.objects.select_related("destination"), pk=pk)
    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect(f"/login/?next={request.path}")
        try:
            rating = int(request.POST.get("rating", 0))
        except ValueError:
            rating = 0
        if 1 <= rating <= 5:
            Review.objects.create(package=p, user=request.user, rating=rating, comment=request.POST.get("comment", "")[:1000])
            messages.success(request, "Thanks for your review.")
        return redirect("package_detail", pk=pk)
    in_wishlist = request.user.is_authenticated and Wishlist.objects.filter(user=request.user, package=p).exists()
    return render(request, "travel/package_detail.html", {"p": p, "in_wishlist": in_wishlist})

def vehicles(request):
    return render(request, "travel/vehicles.html", {
        "two": Vehicle.objects.filter(kind="two"), "four": Vehicle.objects.filter(kind="four")})

def hotels(request):
    return render(request, "travel/hotels.html", {"items": Hotel.objects.prefetch_related("rooms")})

@login_required
@require_POST
def wishlist_toggle(request, pk):
    p = get_object_or_404(TourPackage, pk=pk)
    obj, created = Wishlist.objects.get_or_create(user=request.user, package=p)
    if not created:
        obj.delete()
    messages.success(request, "Added to wishlist." if created else "Removed from wishlist.")
    return redirect(request.POST.get("next") or "dashboard")

@login_required
def book(request, kind, pk):
    model = {"package": TourPackage, "vehicle": Vehicle, "hotel": Hotel}.get(kind)
    if not model:
        raise Http404
    obj = get_object_or_404(model, pk=pk)
    form = BookingForm(request.POST or None, kind=kind, obj=obj, initial={
        "traveller_name": request.user.first_name, "contact": request.user.username})
    if form.is_valid():
        b = form.save(commit=False)
        b.user, b.kind = request.user, kind
        if kind == "package":
            b.package, b.start_date, b.end_date = obj, obj.travel_start_date, obj.travel_end_date
        elif kind == "vehicle":
            b.vehicle = obj
        b.total = b.calculate()
        b.save()
        return redirect("payment", ref=b.reference)
    rooms = {r.pk: str(r.charge_per_day) for r in obj.rooms.all()} if kind == "hotel" else {}
    unit = {"package": getattr(obj, "price_per_person", 0), "vehicle": getattr(obj, "rent_per_day", 0)}.get(kind, 0)
    return render(request, "travel/book.html", {"form": form, "obj": obj, "kind": kind, "unit": unit,
                                                "extra": getattr(obj, "additional_charges", 0), "rooms": json.dumps(rooms)})

def upi_uri(b):
    q = urlencode({"pa": settings.UPI_ID, "pn": "Dream Travel", "am": f"{b.total:.2f}", "cu": "INR",
                   "tr": b.reference, "tn": f"Dream Travel {b.reference}"})
    return "upi://pay?" + q

@login_required
def payment(request, ref):
    b = get_object_or_404(Booking, reference=ref, user=request.user)
    pay, _ = Payment.objects.get_or_create(booking=b, defaults={"amount": b.total, "contact": b.contact})
    return render(request, "travel/payment.html", {"b": b, "pay": pay, "upi_ready": bool(settings.UPI_ID),
                                                   "sandbox": settings.DEBUG})

@login_required
def qr_png(request, ref):
    b = get_object_or_404(Booking, reference=ref, user=request.user)
    if not settings.UPI_ID:
        raise Http404("UPI_ID is not configured.")
    buf = io.BytesIO()
    qrcode.make(upi_uri(b)).save(buf, format="PNG")
    return HttpResponse(buf.getvalue(), content_type="image/png")

def mark_paid(payment, txn_id):
    with transaction.atomic():
        pay = Payment.objects.select_for_update().get(pk=payment.pk)
        if pay.status == "success":
            return
        pay.status, pay.transaction_id, pay.paid_at = "success", txn_id, timezone.now()
        pay.save()
        b = pay.booking
        b.status = "confirmed"
        b.save(update_fields=["status"])
        if b.kind == "package":
            TourPackage.objects.filter(pk=b.package_id).update(available_seats=F("available_seats") - b.members)
        elif b.kind == "vehicle":
            Vehicle.objects.filter(pk=b.vehicle_id, quantity__gt=0).update(quantity=F("quantity") - 1)

@csrf_exempt
@require_POST
def payment_webhook(request):
    """Payment provider calls this. The HMAC signature proves the call is genuine.
    A scanned QR alone never marks a booking paid."""
    secret = settings.PAYMENT_WEBHOOK_SECRET.encode()
    if not secret:
        return HttpResponseBadRequest("Webhook secret not configured")
    sig = request.headers.get("X-Signature", "")
    expected = hmac.new(secret, request.body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return HttpResponse(status=403)
    try:
        data = json.loads(request.body)
        pay = Payment.objects.get(booking__reference=data["reference"])
        ok = data["status"] == "success" and Decimal(str(data["amount"])) == pay.amount
    except Exception:
        return HttpResponseBadRequest("Invalid payload")
    if ok:
        mark_paid(pay, str(data.get("transaction_id", "")))
    else:
        Payment.objects.filter(pk=pay.pk).exclude(status="success").update(status="failed")
    return HttpResponse("ok")

@login_required
@require_POST
def sandbox_pay(request, ref):
    """DEBUG only: simulates the provider's verified callback while developing."""
    if not settings.DEBUG:
        raise Http404
    b = get_object_or_404(Booking, reference=ref, user=request.user)
    mark_paid(b.payment, "SANDBOX-" + b.reference)
    messages.success(request, "Sandbox payment verified.")
    return redirect("dashboard")

@login_required
def receipt(request, ref):
    b = get_object_or_404(Booking, reference=ref, user=request.user)
    pay = getattr(b, "payment", None)
    if not pay or pay.status != "success":
        messages.error(request, "A receipt is available after payment is verified.")
        return redirect("dashboard")
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    y = 800
    c.setFont("Helvetica-Bold", 20); c.drawString(50, y, "Dream Travel - Payment Receipt"); y -= 40
    c.setFont("Helvetica", 12)
    rows = [("Booking ID", b.reference), ("Traveller", b.traveller_name), ("Contact", pay.contact),
            ("Booking", f"{b.get_kind_display()}: {b.item}"),
            ("Dates", f"{b.start_date or '-'} to {b.end_date or '-'}"),
            ("Members" if b.kind == "package" else "Days", b.members if b.kind == "package" else b.days),
            ("Amount paid", f"INR {pay.amount}"), ("Transaction ID", pay.transaction_id),
            ("Paid at", pay.paid_at.strftime("%d %b %Y %H:%M")), ("Status", "Paid")]
    for k, v in rows:
        c.drawString(50, y, f"{k}:"); c.drawString(190, y, str(v)); y -= 24
    c.showPage(); c.save(); buf.seek(0)
    return FileResponse(buf, as_attachment=True, filename=f"receipt-{b.reference}.pdf")
