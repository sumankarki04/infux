from app import db
from datetime import datetime


class Review(db.Model):
    __tablename__ = 'reviews'

    review_id   = db.Column(db.Integer, primary_key=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    reviewee_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.campaign_id'))
    rating      = db.Column(db.Integer, nullable=False)  # 1-5
    review_text = db.Column(db.Text)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    reviewer = db.relationship('User', foreign_keys=[reviewer_id], backref='reviews_given')
    reviewee = db.relationship('User', foreign_keys=[reviewee_id])
