from datetime import datetime
from zoneinfo import ZoneInfo
from app import app, db, Cart
from sqlalchemy.exc import OperationalError
import time

IST = ZoneInfo("Asia/Kolkata")


def clear_expired_carts(max_retries=5, retry_delay=1):
    """Deletes expired carts safely, retrying if SQLite is locked."""
    with app.app_context():
        for attempt in range(max_retries):
            try:
                now = datetime.now(IST)
                expired_carts = Cart.query.filter(Cart.expires_at <= now).all()

                if not expired_carts:
                    print(
                        f"✅ No expired carts found at {now.strftime('%Y-%m-%d %H:%M:%S %Z')}"
                    )
                    return

                print(
                    f"🧹 Found {len(expired_carts)} expired carts at {now.strftime('%Y-%m-%d %H:%M:%S %Z')}. Cleaning up..."
                )

                # Disable autoflush to avoid premature writes while looping
                with db.session.no_autoflush:
                    for cart in expired_carts:
                        for item in cart.items:
                            item.product.available_quantity += item.quantity
                        db.session.delete(cart)

                db.session.commit()
                print(
                    f"✅ Cleanup completed successfully at {now.strftime('%Y-%m-%d %H:%M:%S %Z')}"
                )
                return

            except OperationalError as e:
                if "database is locked" in str(e):
                    print(f"⚠️ Database locked, retrying ({attempt+1}/{max_retries})...")
                    time.sleep(retry_delay)
                else:
                    raise  # Raise unexpected errors

        print(
            "❌ Failed to clear expired carts after several retries (DB remained locked)."
        )


if __name__ == "__main__":
    clear_expired_carts()
