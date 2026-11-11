from django.conf import settings
from django.db import models

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    photo = models.ImageField(upload_to="profiles/", blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    # admin-only profile fields
    experience = models.CharField(max_length=100, blank=True)
    about = models.TextField(blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username
