from django.contrib.auth import views as v
from django.urls import path
from . import views
from .forms import LoginForm

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", v.LoginView.as_view(template_name="accounts/login.html", authentication_form=LoginForm,
                                       redirect_authenticated_user=True), name="login"),
    path("logout/", v.LogoutView.as_view(), name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("password-reset/", v.PasswordResetView.as_view(), name="password_reset"),
    path("password-reset/done/", v.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", v.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/done/", v.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
]
