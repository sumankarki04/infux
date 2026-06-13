from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.notification import Notification

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('/')
@login_required
def index():
    notifications = Notification.query.filter_by(
        user_id=current_user.user_id
    ).order_by(Notification.created_at.desc()).limit(50).all()

    # Mark all as read
    Notification.query.filter_by(
        user_id=current_user.user_id, is_read=False
    ).update({'is_read': True})
    db.session.commit()

    return render_template('notifications/index.html', notifications=notifications)


@notifications_bp.route('/<int:notif_id>/read', methods=['POST'])
@login_required
def mark_read(notif_id):
    notification = Notification.query.get_or_404(notif_id)
    if notification.user_id != current_user.user_id:
        return jsonify({'ok': False}), 403
    notification.is_read = True
    db.session.commit()
    return jsonify({'ok': True})


@notifications_bp.route('/count')
def count():
    if not current_user.is_authenticated:
        return jsonify({'count': 0})
    unread = Notification.query.filter_by(
        user_id=current_user.user_id, is_read=False
    ).count()
    return jsonify({'count': unread})
