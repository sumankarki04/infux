from app import db
from datetime import datetime

NOTIF_ICONS = {
    'application': 'fa-paper-plane',
    'accepted':    'fa-check-circle',
    'rejected':    'fa-times-circle',
    'review':      'fa-star',
    'payment':     'fa-money-bill-wave',
    'message':     'fa-comment',
    'system':      'fa-bell',
}

NOTIF_COLORS = {
    'application': '#7c3aed',
    'accepted':    '#10b981',
    'rejected':    '#ef4444',
    'review':      '#f59e0b',
    'payment':     '#10b981',
    'message':     '#0ea5e9',
    'system':      '#6b7280',
}


class Notification(db.Model):
    __tablename__ = 'notifications'

    notification_id = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    notif_type      = db.Column(db.String(30), default='system')
    title           = db.Column(db.String(120), nullable=False)
    body            = db.Column(db.String(300))
    link            = db.Column(db.String(300))
    is_read         = db.Column(db.Boolean, default=False)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('notifications',
                           lazy='dynamic', order_by='Notification.created_at.desc()'))

    @property
    def icon(self):
        return NOTIF_ICONS.get(self.notif_type, 'fa-bell')

    @property
    def color(self):
        return NOTIF_COLORS.get(self.notif_type, '#6b7280')
