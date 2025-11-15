from app import app, db
from models import User
from getpass import getpass

with app.app_context():
    users = User.query.filter(User.password_hash.is_(None)).all()
    for u in users:
        pwd = "changeme123"  # or generate randomly
        u.set_password(pwd)
        print(f"Set password for {u.email} -> {pwd}")
    db.session.commit()