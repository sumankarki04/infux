from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    user_id    = db.Column(db.Integer, primary_key=True)
    email      = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    user_type  = db.Column(db.String(20), nullable=False)  # admin / brand / influencer
    first_name = db.Column(db.String(60), nullable=False)
    last_name  = db.Column(db.String(60), nullable=False)
    phone      = db.Column(db.String(20))
    city       = db.Column(db.String(60))
    profile_picture = db.Column(db.String(200), default='default.png')
    is_active  = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    influencer = db.relationship('Influencer', backref='user', uselist=False, lazy=True)
    brand      = db.relationship('Brand',      backref='user', uselist=False, lazy=True)

    sent_messages     = db.relationship('Message', foreign_keys='Message.sender_id',   backref='sender',   lazy=True)
    received_messages = db.relationship('Message', foreign_keys='Message.receiver_id', backref='receiver', lazy=True)

    def get_id(self):
        return str(self.user_id)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def avatar_url(self):
        return f'/static/uploads/{self.profile_picture}'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
