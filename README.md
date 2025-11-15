# 🛒 E-Commerce Backend (Flask + PostgreSQL)

A clean and functional E-Commerce API backend built with Flask, SQLAlchemy, and PostgreSQL.  
Supports products, shopping cart logic, cart expiry, and order management.  
This backend is part of my full-stack practice project (paired with a React frontend).

---

## 🚀 Features

- Product listing & stock management  
- Per-user shopping cart  
- Auto cart expiry (15 minutes)  
- Stock automatically restored on expiry  
- Add / remove items from cart  
- Checkout → creates Order + OrderItem records  
- PostgreSQL + SQLAlchemy ORM  
- CORS enabled for frontend requests  

---

## 📦 Tech Stack

- Python + Flask  
- SQLAlchemy ORM  
- PostgreSQL  
- flask-cors  
- zoneinfo (IST timezone handling)

---

## 🗂 Project Structure

```
ecommerce-backend/
│
├── app.py              # Flask app + routes
├── models.py           # SQLAlchemy models
├── database.py         # DB initialization
├── clear_expiry.py     # Script to clean expired carts manually
└── README.md
```

---

## 🛢 Database Models

- User  
- Product  
- Cart  
- CartItem  
- Order  
- OrderItem  

Each user has one active cart which expires in 15 minutes.  
Expired carts restore all quantities back to product stock.

---

## ▶ Running Locally

### 1️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

### 2️⃣ Setup PostgreSQL
Create a database:
```sql
CREATE DATABASE ecommerce;
```

Update `app.py` with your DB URL if needed.

### 3️⃣ Run the server
```bash
python app.py
```

Backend runs at:
```
http://localhost:5000
```

---

## 📌 API Endpoints

### 📦 Products
```
GET    /products
POST   /products
```

### 👤 Users
```
POST   /users
GET    /users
```

### 🛒 Cart
```
POST   /users/<id>/cart          # create or get active cart
GET    /users/<id>/cart          # view cart
POST   /users/<id>/cart/add      # add item
POST   /users/<id>/cart/remove   # remove item
POST   /users/<id>/cart/checkout # checkout
```

### 📦 Orders
```
GET    /users/<id>/orders
```

---

## 🧹 Cart Expiry

- Cart lifetime: **15 minutes**
- Expired carts automatically free stock
- Manual cleanup:
```bash
python clear_expiry.py
```

---

## 📘 Notes

This backend is intentionally simple and clean.  
It’s meant to be paired with a React frontend and extended later with:

- Authentication (JWT)  
- Admin dashboard  
- Payment integration  
- Inventory management  

---

Happy Building 🚀
