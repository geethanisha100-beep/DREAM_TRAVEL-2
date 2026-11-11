# Dream Travel

Tour and travel agency system. Django, Django REST Framework, SQLite, HTML/CSS/JS.

## Setup
```bash
python -m venv venv && source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env     # then export these values (see below)
python manage.py makemigrations accounts travel
python manage.py migrate
python manage.py createsuperuser      # this is the admin account
python manage.py runserver
```
Set environment variables before running (never commit them):
```bash
export DJANGO_SECRET_KEY="long-random-string"
export UPI_ID="9964911496-2@ybl"
export PAYMENT_WEBHOOK_SECRET="long-random-string"
```
Windows PowerShell: `$env:UPI_ID="9964911496-2@ybl"`.

## Use
- Site: http://127.0.0.1:8000/  Admin (TTAM Administration): http://127.0.0.1:8000/admin/
- In the admin add Destinations, Tour packages (up to 3 photos), Vehicles, Hotels (with rooms). Admins also track Bookings and Payments there.
- REST API: `/api/destinations/`, `/api/packages/`, `/api/vehicles/`, `/api/hotels/` (add `?search=`), `/api/my-bookings/` (login required).
- Admin profile fields (photo, phone, address, experience, about): Admin > Profiles.

## Payments (test mode)
1. A booking creates a pending Payment; the page shows a UPI QR built from `UPI_ID`, the exact amount and the booking reference.
2. A scan alone changes nothing. A booking becomes paid only when your payment provider calls `POST /payments/webhook/` with header `X-Signature` = HMAC-SHA256 of the raw body using `PAYMENT_WEBHOOK_SECRET`. Body: `{"reference":"DT1234ABCD","amount":"8500.00","status":"success","transaction_id":"TXN1"}`. The amount must match.
3. For development (DEBUG=1) use the "Simulate verified payment" button on the payment page.
4. For production wire your provider's real verification (for example a Razorpay/PayU webhook) into `payment_webhook` in `travel/views.py`.
5. After success, the PDF receipt downloads from the payment page or dashboard.

## Password rules
8-20 characters, first character A-Z, one number, one special character. Enforced in `accounts/validators.py` (backend) and `static/js/main.js` (live hints).

## Notes
- Forgot password sends an email (printed in the terminal in development), so it works for accounts registered with an email.
- Push to GitHub: `.gitignore` already excludes `db.sqlite3`, `media/` and `.env`.
