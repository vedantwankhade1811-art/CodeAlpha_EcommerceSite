# Cartza — Minimal & Premium E-Commerce Platform

Cartza is a modern, minimal, and premium full-stack e-commerce platform built for the CodeAlpha internship project.

## Tech Stack
- **Frontend**: HTML5, Vanilla CSS3 (custom design system), Vanilla JavaScript
- **Backend**: Python 3.14, Django 5.2
- **Database**: SQLite (Development)
- **Authentication**: Django Built-in Auth
- **Email Backend**: Django Console Email Backend (Development)

## Project Structure
- `core/`: Base layouts, navigation, global components, homepage, newsletter, static pages
- `products/`: Catalog, product details, categories, filtering/search, seed commands
- `accounts/`: User registration, profile management, authentication, password reset
- `cart/`: Shopping cart, server-side validation, session persistence
- `orders/`: Checkout, atomic transactions, idempotency, order tracking & management
- `wishlist/`: User wishlist & saved items

## Setup & Local Run
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env

# 3. Run database migrations
python manage.py migrate

# 4. Seed initial products & categories
python manage.py seed_products

# 5. Start development server
python manage.py runserver
```
