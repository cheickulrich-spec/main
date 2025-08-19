# Pharmacy Seller App

A simple Flask + SQLite web application to manage and sell pharmacy products. Includes:

- Product catalog with search and category filter
- Shopping cart and checkout flow
- Order creation with stock decrement
- Minimal password-protected admin for inventory CRUD

## Quickstart

1. Create and activate a virtual environment

```bash
python3 -m venv .venv && source .venv/bin/activate
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Initialize the database and seed sample products

```bash
python seed.py
```

4. Run the app

```bash
python app.py
```

Visit `http://127.0.0.1:5000` in your browser.

## Admin Access

- Set an admin password via environment variable `PHARMACY_ADMIN_PASSWORD`, or the default is `admin123` (development only).
- Go to `/admin/login` to sign in.

## Project Structure

```
app.py
models.py
database.py
seed.py
requirements.txt
templates/
  base.html
  index.html
  product_detail.html
  cart.html
  checkout.html
  order_success.html
  admin/
    login.html
    products.html
    product_form.html
static/
  styles.css
```

## Notes

- This app is for demonstration purposes and omits payment integration and robust authentication.
- Do not use the default admin password in production. Configure `PHARMACY_ADMIN_PASSWORD`.