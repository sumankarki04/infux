from app import db
from datetime import datetime


class Campaign(db.Model):
    __tablename__ = 'campaigns'

    campaign_id  = db.Column(db.Integer, primary_key=True)
    brand_id     = db.Column(db.Integer, db.ForeignKey('brands.brand_id'), nullable=False)
    title        = db.Column(db.String(200), nullable=False)
    description  = db.Column(db.Text)
    platform     = db.Column(db.String(40))     # instagram/tiktok/youtube/facebook/any
    niche        = db.Column(db.String(60))
    budget       = db.Column(db.Float, default=0)
    deliverables = db.Column(db.Text)           # what creators must deliver
    deadline     = db.Column(db.Date)
    min_followers = db.Column(db.Integer, default=0)
    max_followers = db.Column(db.Integer, default=0)
    location     = db.Column(db.String(60), default='Nepal')
    status       = db.Column(db.String(20), default='open')  # open/closed/completed
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    applications = db.relationship('Application', backref='campaign', lazy=True)

    def open_applications(self):
        return [a for a in self.applications if a.status == 'pending']

    def accepted_applications(self):
        return [a for a in self.applications if a.status == 'accepted']
