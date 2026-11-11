from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from .forms import ProfileForm, RegisterForm
from travel.models import Payment
from .models import Profile

def register(request):
    form = RegisterForm(request.POST or None)
    if form.is_valid():
        login(request, form.save())
        messages.success(request, "Welcome to Dream Travel!")
        return redirect("home")
    return render(request, "accounts/register.html", {"form": form})

@login_required
def dashboard(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    form = ProfileForm(request.POST or None, request.FILES or None, instance=profile)
    if form.is_valid():
        form.save()
        messages.success(request, "Profile updated.")
        return redirect("dashboard")
    u = request.user
    return render(request, "accounts/dashboard.html", {
        "form": form,
        "wishlist": u.wishlist.select_related("package__destination"),
        "bookings": u.bookings.select_related("package", "vehicle", "room__hotel"),
        "payments": Payment.objects.filter(booking__user=u).select_related("booking"),
    })
