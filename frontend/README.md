# AI Diagnostic System — Frontend

React (Vite, JS) frontend for the [ai-diagnostic-system](../ai-diagnostic-system) backend.
Two user flows: patients book tests and read results, diagnostic centers manage
packages, bookings, and report uploads.

## Stack

- React 18 + Vite + React Router
- Tailwind CSS (design tokens in `tailwind.config.js` — pine/teal for brand,
  a status palette for booking/payment/anomaly states)
- Axios with an interceptor that transparently refreshes the JWT access token
  on a 401 and replays the original request (queues concurrent refreshes into
  one call instead of firing N)
- Razorpay Checkout, loaded via script tag, wired to the backend's
  create-order → verify-payment flow

## Running it

```bash
cp .env.example .env
# point VITE_API_URL at your running backend if it's not on localhost:8000

npm install
npm run dev
```

Requires the backend running (`docker compose up` in `../ai-diagnostic-system`).

## Pages

| Route | Who | What |
|---|---|---|
| `/` | anyone | Landing |
| `/register`, `/login` | anyone | Auth (role picker: patient / center) |
| `/symptom-check` | patient | AI symptom → test recommendation |
| `/centers`, `/centers/:id` | anyone / patient books | Browse centers, book + pay for a package |
| `/bookings` | patient | Booking list + status |
| `/bookings/:id/report` | patient/center/admin | Report detail with the anomaly range-bar visualization |
| `/center/dashboard` | center | Create center profile, add packages |
| `/center/bookings` | center | Upload reports, trigger anomaly analysis |

## Two backend endpoints added while building this

The original backend had no way for the frontend to (a) look up a report by
`booking_id` or (b) let a center list its own bookings — both are needed for
the flows above and have been added to `reports.py` / `bookings.py`:

- `GET /api/v1/reports/by-booking/{booking_id}`
- `GET /api/v1/bookings/center`

Both enforce the same ownership checks as the rest of their routers.

## Signature piece

`src/components/RangeBar.jsx` — instead of a flat "HIGH/LOW" badge for a lab
value, it draws the actual normal-range zone and marks where the patient's
value sits relative to it, colored by severity. Ties directly to the
backend's rule-based anomaly detection rather than being decorative.

## Known gaps

- No auto-refresh polling on `/bookings` or `/center/bookings` — reload to see status changes
- No client-side form validation library; relying on native `required`/`minLength`/`type` constraints
- Auth role is read from decoding the JWT payload client-side (no `/users/me` endpoint exists yet on the backend to fetch a verified profile)
- No test suite (matches the backend's current state)
- Brand name ("Sequel Diagnostics") and logo mark are placeholders — swap `Navbar.jsx` and `index.html`'s `<title>` for your own
