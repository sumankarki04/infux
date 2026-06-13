from app import db
from datetime import datetime


class Influencer(db.Model):
    __tablename__ = 'influencers'

    influencer_id      = db.Column(db.Integer, primary_key=True)
    user_id            = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    bio                = db.Column(db.Text)
    niche              = db.Column(db.String(60))   # tech, fashion, food, travel, etc.
    instagram_handle   = db.Column(db.String(80))
    tiktok_handle      = db.Column(db.String(80))
    youtube_handle     = db.Column(db.String(80))
    facebook_handle    = db.Column(db.String(80))
    instagram_followers = db.Column(db.Integer, default=0)
    tiktok_followers    = db.Column(db.Integer, default=0)
    youtube_subscribers = db.Column(db.Integer, default=0)
    facebook_followers  = db.Column(db.Integer, default=0)
    engagement_rate    = db.Column(db.Float, default=0.0)
    portfolio_url      = db.Column(db.String(200))
    creator_score      = db.Column(db.Float, default=0.0)
    total_campaigns    = db.Column(db.Integer, default=0)
    average_rating     = db.Column(db.Float, default=0.0)
    verification_status = db.Column(db.String(20), default='pending')  # pending/verified/rejected
    created_at         = db.Column(db.DateTime, default=datetime.utcnow)

    applications = db.relationship('Application', backref='influencer', lazy=True)
    reviews_received = db.relationship('Review', foreign_keys='Review.reviewee_id', backref='reviewee', lazy=True)

    def total_followers(self):
        return (self.instagram_followers or 0) + (self.tiktok_followers or 0) + \
               (self.youtube_subscribers or 0) + (self.facebook_followers or 0)

    def primary_platform(self):
        platforms = {
            'Instagram': self.instagram_followers or 0,
            'TikTok':    self.tiktok_followers    or 0,
            'YouTube':   self.youtube_subscribers or 0,
            'Facebook':  self.facebook_followers  or 0,
        }
        return max(platforms, key=platforms.get)
