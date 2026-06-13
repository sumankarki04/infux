from app import db
from datetime import datetime


class Application(db.Model):
    __tablename__ = 'applications'

    application_id = db.Column(db.Integer, primary_key=True)
    campaign_id    = db.Column(db.Integer, db.ForeignKey('campaigns.campaign_id'), nullable=False)
    influencer_id  = db.Column(db.Integer, db.ForeignKey('influencers.influencer_id'), nullable=False)
    message        = db.Column(db.Text)
    status         = db.Column(db.String(20), default='pending')  # pending/accepted/rejected
    applied_at     = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('campaign_id', 'influencer_id', name='unique_application'),
    )

    @property
    def created_at(self):
        return self.applied_at
