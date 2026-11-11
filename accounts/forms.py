import re
from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from .models import Profile

class RegisterForm(forms.Form):
    name = forms.CharField(max_length=60)
    identifier = forms.CharField(label="Phone number or email", max_length=150)
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput, max_length=20)
    password2 = forms.CharField(label="Confirm password", widget=forms.PasswordInput, max_length=20)

    def clean_identifier(self):
        v = self.cleaned_data["identifier"].strip().lower()
        if "@" in v:
            if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
                raise forms.ValidationError("Enter a valid email address.")
        elif not re.match(r"^\+?\d{10,13}$", v):
            raise forms.ValidationError("Enter a valid phone number (10-13 digits) or an email.")
        if User.objects.filter(username=v).exists():
            raise forms.ValidationError("An account with this phone/email already exists.")
        return v

    def clean(self):
        data = super().clean()
        p1, p2 = data.get("password1"), data.get("password2")
        if p1:
            password_validation.validate_password(p1)  # backend enforcement of Section 4 rules
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Passwords do not match.")
        return data

    def save(self):
        d = self.cleaned_data
        ident = d["identifier"]
        user = User.objects.create_user(
            username=ident, email=ident if "@" in ident else "",
            password=d["password1"], first_name=d["name"])
        Profile.objects.create(user=user, phone="" if "@" in ident else ident)
        return user

class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Phone number or email")

    def clean_username(self):
        return self.cleaned_data["username"].strip().lower()

class ProfileForm(forms.ModelForm):
    name = forms.CharField(max_length=60)
    email = forms.EmailField(required=False)

    class Meta:
        model = Profile
        fields = ["photo", "phone", "address"]

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.fields["name"].initial = self.instance.user.first_name
        self.fields["email"].initial = self.instance.user.email

    def save(self, commit=True):
        p = super().save(commit)
        u = p.user
        u.first_name, u.email = self.cleaned_data["name"], self.cleaned_data["email"]
        u.save()
        return p
