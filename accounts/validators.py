import re
from django.core.exceptions import ValidationError

SPECIAL = "!@#$%&*^()_+-=?.,:;"

class DreamPasswordValidator:
    """8-20 chars, first char A-Z, at least one digit and one special character."""
    def validate(self, password, user=None):
        errors = []
        if not 8 <= len(password) <= 20:
            errors.append("Password must be 8 to 20 characters long.")
        if not re.match(r"^[A-Z]", password):
            errors.append("The first character must be an uppercase letter (A-Z).")
        if not re.search(r"\d", password):
            errors.append("Include at least one number (0-9).")
        if not any(c in SPECIAL for c in password):
            errors.append("Include at least one special character such as ! @ # $ % &.")
        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return "8-20 characters, starts with an uppercase letter, has a number and a special character."
