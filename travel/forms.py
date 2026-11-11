from datetime import date
from django import forms
from .models import Booking, HotelRoom

class DateInput(forms.DateInput):
    input_type = "date"

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["traveller_name", "contact", "address", "message", "members", "start_date", "end_date", "room"]
        widgets = {"start_date": DateInput, "end_date": DateInput, "address": forms.Textarea(attrs={"rows": 2}),
                   "message": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *a, kind, obj, **kw):
        super().__init__(*a, **kw)
        self.kind, self.obj = kind, obj
        if kind == "package":
            for f in ("start_date", "end_date", "room"):
                del self.fields[f]
        elif kind == "vehicle":
            del self.fields["members"]; del self.fields["room"]
            self.fields["start_date"].required = self.fields["end_date"].required = True
        else:
            del self.fields["members"]
            self.fields["room"].queryset = obj.rooms.filter(is_available=True)
            self.fields["room"].required = True
            self.fields["start_date"].required = self.fields["end_date"].required = True

    def clean(self):
        d = super().clean()
        if self.kind == "package":
            if not self.obj.bookable:
                raise forms.ValidationError("This package is not available for booking.")
            if d.get("members") and d["members"] > self.obj.available_seats:
                self.add_error("members", f"Only {self.obj.available_seats} seats are left.")
        else:
            if self.kind == "vehicle" and not self.obj.bookable:
                raise forms.ValidationError("This vehicle is currently unavailable.")
            if self.kind == "hotel" and not self.obj.is_available:
                raise forms.ValidationError("This hotel is currently unavailable.")
            s, e = d.get("start_date"), d.get("end_date")
            if s and s < date.today():
                self.add_error("start_date", "Start date cannot be in the past.")
            if s and e and e < s:
                self.add_error("end_date", "End date must be on or after the start date.")
            if self.kind == "hotel" and s and e and e == s:
                self.add_error("end_date", "Choose at least one night.")
        return d
