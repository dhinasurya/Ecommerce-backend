from app import app, db, User, Product

with app.app_context():
    # Users
    u1 = User(username="dhina", email="dhina@example.com")
    u2 = User(username="john_doe", email="john@example.com")
    u3 = User(username="alice_smith", email="alice@example.com")
    
    # Products (variety of items and prices)
    p1 = Product(name="Laptop", price=80000, available_quantity=10)
    p2 = Product(name="Headphones", price=3000, available_quantity=50)
    p3 = Product(name="Phone", price=45000, available_quantity=15)
    p4 = Product(name="Tablet", price=35000, available_quantity=8)
    p5 = Product(name="Monitor", price=25000, available_quantity=20)

    db.session.add_all([u1, u2, u3, p1, p2, p3, p4, p5])
    db.session.commit()

print("✅ Test data inserted successfully!")