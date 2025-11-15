from flask import Flask, jsonify, request
from database import db
from models import *
from datetime import datetime
from zoneinfo import ZoneInfo
from flask_cors import CORS
import os
from dotenv import load_dotenv
from flask_migrate import Migrate

load_dotenv()

IST = ZoneInfo("Asia/Kolkata")

app = Flask(__name__)

CORS(app)

# Configure your database URI
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the database with the app
db.init_app(app)
migrate = Migrate(app, db)

# Create all tables
with app.app_context():
    db.create_all()
    print("✅ Database tables created successfully!")


# ---------------------------
# HELPER FUNCTIONS
# ---------------------------
def get_active_cart(user_id):
    """Return the active (non-expired) cart for a user, or None."""
    now = datetime.now(IST)
    return Cart.query.filter_by(user_id=user_id).filter(Cart.expires_at > now).first()


def release_expired_cart(cart):
    """Return items from expired cart back to product stock."""
    for item in cart.items:
        item.product.available_quantity += item.quantity
    db.session.delete(cart)
    db.session.commit()


def get_or_create_active_cart(user_id):
    """Return active cart or create a new one if expired or none exists."""
    now = datetime.now(IST)

    user = User.query.get(user_id)
    if not user:
        return None, "User not found"

    # 1. Return the existing active cart
    cart = get_active_cart(user_id)
    if cart:
        return cart, None

    # 2. If the latest cart is expired → release it
    expired_cart = (
        Cart.query.filter_by(user_id=user_id).order_by(Cart.created_at.desc()).first()
    )
    if expired_cart and expired_cart.expires_at <= now:
        release_expired_cart(expired_cart)

    # 3. Create a new cart
    new_cart = Cart(user_id=user_id)
    db.session.add(new_cart)
    db.session.commit()

    return new_cart, None


# ---------------------------
# ROUTES
# ---------------------------


@app.route("/")
def home():
    return jsonify({"message": "Welcome to the E-Commerce API"})


# ---------------------------
# PRODUCTS
# ---------------------------


@app.route("/products", methods=["GET"])
def get_products():
    products = Product.query.all()
    result = [
        {
            "id": p.id,
            "name": p.name,
            "price": p.price,
            "available_quantity": p.available_quantity,
        }
        for p in products
    ]
    return jsonify(result)


@app.route("/products", methods=["POST"])
def add_product():
    data = request.get_json()
    name = data.get("name")
    price = data.get("price")
    quantity = data.get("available_quantity", 0)

    if not name or price is None:
        return jsonify({"error": "Missing name or price"}), 400

    product = Product(name=name, price=price, available_quantity=quantity)
    db.session.add(product)
    db.session.commit()
    return jsonify({"message": "✅ Product added", "id": product.id}), 201


# ---------------------------
# USERS
# ---------------------------


@app.route("/users", methods=["POST"])
def create_user():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")

    if not username or not email:
        return jsonify({"error": "Username and email required"}), 400

    user = User(username=username, email=email)
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "✅ User created", "id": user.id}), 201


@app.route("/users", methods=["GET"])
def list_users():
    users = User.query.all()
    result = [{"id": u.id, "username": u.username, "email": u.email} for u in users]
    return jsonify(result)


# ---------------------------
# CART
# ---------------------------


@app.route("/users/<int:user_id>/cart", methods=["POST"])
def create_or_get_cart(user_id):
    """Get or create active cart for a user."""
    cart, error = get_or_create_active_cart(user_id)
    if error:
        return jsonify({"error": error}), 404
    return jsonify({"message": "✅ Active cart ready", "cart_id": cart.id}), 200


@app.route("/users/<int:user_id>/cart/add", methods=["POST"])
def add_to_cart(user_id):
    """Add product to user's active cart."""
    data = request.get_json()
    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)

    cart, error = get_or_create_active_cart(user_id)
    if error:
        return jsonify({"error": error}), 404

    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    if product.available_quantity < quantity:
        return jsonify({"error": "Not enough stock"}), 400

    # Check if item exists in cart
    cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product.id).first()
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(cart_id=cart.id, product_id=product.id, quantity=quantity)
        db.session.add(cart_item)

    # Decrement product availability
    product.available_quantity -= quantity
    db.session.commit()
    return jsonify({"message": "✅ Item added to cart"}), 200


@app.route("/users/<int:user_id>/cart/remove", methods=["POST"])
def remove_from_cart(user_id):
    data = request.get_json()
    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)

    cart = get_active_cart(user_id)
    if not cart:
        return jsonify({"error": "Cart expired"}), 410

    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product.id).first()
    if not cart_item:
        return jsonify({"error": "Item not found in cart"}), 404

    if quantity >= cart_item.quantity:
        product.available_quantity += cart_item.quantity
        db.session.delete(cart_item)
        message = "Item removed from cart"
    else:
        cart_item.quantity -= quantity
        product.available_quantity += quantity
        message = f"Reduced quantity by {quantity}"

    db.session.commit()
    return jsonify({"message": f"✅ {message}"}), 200


@app.route("/users/<int:user_id>/cart", methods=["GET"])
def view_user_cart(user_id):
    cart = get_active_cart(user_id)

    if not cart:
        return (
            jsonify({"items": [], "total": 0, "expires_in": None, "expires_at": None}),
            200,
        )

    # same logic below
    now = datetime.now(IST)
    expires_at = cart.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=IST)

    remaining = expires_at - now
    remaining_minutes = int(remaining.total_seconds() // 60)
    remaining_seconds = int(remaining.total_seconds() % 60)

    items = [
        {
            "product_id": item.product.id,
            "product": item.product.name,
            "price": item.product.price,
            "quantity": item.quantity,
            "subtotal": item.quantity * item.product.price,
        }
        for item in cart.items
    ]
    total = sum(i["subtotal"] for i in items)

    return jsonify(
        {
            "items": items,
            "total": total,
            "expires_in": f"{remaining_minutes}m {remaining_seconds}s",
            "expires_at": expires_at.isoformat(),
        }
    )


@app.route("/users/<int:user_id>/cart/checkout", methods=["POST"])
def checkout_cart(user_id):
    now = datetime.now(IST)

    # Get ACTIVE cart only — do NOT create a new cart
    cart = get_active_cart(user_id)
    if not cart:
        return jsonify({"error": "Cart expired"}), 410

    if not cart.items:
        return jsonify({"error": "Cart is empty"}), 400

    # Calculate total
    total_amount = sum(item.quantity * item.product.price for item in cart.items)

    # Create order
    order = Order(user_id=user_id, total_amount=total_amount)
    db.session.add(order)
    db.session.commit()  # Commit to generate order.id

    # Move cart items to order items
    for item in cart.items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price_at_order=item.product.price,
        )
        db.session.add(order_item)

    # Delete cart (and cart items)
    db.session.delete(cart)
    db.session.commit()

    return (
        jsonify({"message": "✅ Order placed successfully", "order_id": order.id}),
        200,
    )


@app.route("/users/<int:user_id>/orders", methods=["GET"])
def get_user_orders(user_id):
    """Fetch all orders for a specific user."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    orders = (
        Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
    )
    if not orders:
        return jsonify([]), 200

    result = []
    for order in orders:
        order_data = {
            "order_id": order.id,
            "total_amount": order.total_amount,
            "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "items": [],
        }

        for item in order.items:
            order_data["items"].append(
                {
                    "product_name": item.product.name,
                    "price_at_order": item.price_at_order,
                    "quantity": item.quantity,
                    "subtotal": item.quantity * item.price_at_order,
                }
            )

        result.append(order_data)

    return jsonify(result)


# ---------------------------
# RUN APP
# ---------------------------

if __name__ == "__main__":
    # Bind to the hostname 'localhost' (instead of the default 127.0.0.1)
    # You can also use host='0.0.0.0' to listen on all interfaces.
    app.run(host="localhost", debug=True)
