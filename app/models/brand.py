from app import db
from datetime import datetime


class Brand(db.Model):
    __tablename__ = 'brands'

    brand_id     = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, unique=True)
    company_name = db.Column(db.String(120), nullable=False)
    industry     = db.Column(db.String(60))
    website      = db.Column(db.String(200))
    description  = db.Column(db.Text)
    logo         = db.Column(db.String(200), default='brand_default.png')
    is_verified  = db.Column(db.Boolean, default=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    campaigns        = db.relationship('Campaign', backref='brand', lazy=True)
    reviews_received = db.relationship(
        'Review',
        primaryjoin='Brand.user_id == foreign(Review.reviewee_id)',
        backref='brand_reviewee',
        lazy=True,
        viewonly=True,
    )
