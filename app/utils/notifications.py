from app import db
from app.models.notification import Notification


def notify(user_id, title, notif_type='system', body=None, link=None):
    """Create a notification. Safe to call anywhere — silently ignores errors."""
    try:
        n = Notification(user_id=user_id, title=title,
                         notif_type=notif_type, body=body, link=link)
        db.session.add(n)
        # Don't commit here — caller commits their own transaction
    except Exception:
        pass
