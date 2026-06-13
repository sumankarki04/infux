from app import db
from datetime import datetime


class Payment(db.Model):
    __tablename__ = 'payments'

    payment_id     = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.application_id'), nullable=False)
    payer_id       = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    amount         = db.Column(db.Float, nullable=False)
    method         = db.Column(db.String(20))          # esewa | khalti
    status         = db.Column(db.String(20), default='pending')  # pending | completed | failed
    transaction_id = db.Column(db.String(200))
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at        = db.Column(db.DateTime)

    application = db.relationship('Application', backref='payments', lazy=True)
    payer       = db.relationship('User', foreign_keys=[payer_id], lazy=True)
