import math
import re
from datetime import date, datetime

# Accept common email addresses with a dotted domain; reject missing @ or domain suffix.
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def validate_patient(data):
    errors = []
    full_name = (data.get("full_name") or "").strip()
    email = (data.get("email") or "").strip()
    dob_text = (data.get("date_of_birth") or "").strip()

    if not full_name:
        errors.append("Full name is required.")
    elif len(full_name) > 100:
        errors.append("Full name must be 100 characters or fewer.")

    if not EMAIL_RE.fullmatch(email):
        errors.append("Invalid email address. Enter a valid address such as name@example.com.")

    parsed_dob = None
    for fmt in ("%d/%m/%Y", "%d.%m.%Y"):
        try:
            parsed_dob = datetime.strptime(dob_text, fmt).date()
            break
        except ValueError:
            continue

    if parsed_dob is None:
        errors.append("Invalid date of birth. Use DD/MM/YYYY (or the supplied DD.MM.YYYY format).")
    elif parsed_dob > date.today():
        errors.append("Date of birth cannot be in the future.")

    values = {}
    for field in ("glucose", "haemoglobin", "cholesterol"):
        raw = data.get(field)
        try:
            value = float(raw)
            if not math.isfinite(value) or value < 0:
                raise ValueError
            values[field] = value
        except (TypeError, ValueError):
            errors.append(f"{field.capitalize()} must be a non-negative numeric value.")

    return errors, parsed_dob, values
