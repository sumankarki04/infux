from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from config import Config
import os

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address)
cache = Cache()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    cache.init_app(app, config={'CACHE_TYPE': 'SimpleCache'})

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    from app.routes.public import public_bp
    from app.routes.auth import auth_bp
    from app.routes.influencer import influencer_bp
    from app.routes.brand import brand_bp
    from app.routes.admin import admin_bp
    from app.routes.chat import chat_bp
    from app.routes.payments import payments_bp
    from app.routes.reviews import reviews_bp
    from app.routes.notifications import notifications_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(influencer_bp, url_prefix='/influencer')
    app.register_blueprint(brand_bp, url_prefix='/brand')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(chat_bp, url_prefix='/chat')
    app.register_blueprint(payments_bp, url_prefix='/pay')
    app.register_blueprint(reviews_bp, url_prefix='/reviews')
    app.register_blueprint(notifications_bp, url_prefix='/notifications')

    # chat send (POST) is CSRF-protected via the X-CSRFToken header the client
    # sends (see chat.html); GET poll/inbox need no token. No exemption.

    @app.context_processor
    def inject_notifications():
        from flask_login import current_user
        if current_user.is_authenticated:
            from app.models.notification import Notification
            count = Notification.query.filter_by(
                user_id=current_user.user_id, is_read=False).count()
            recent = Notification.query.filter_by(
                user_id=current_user.user_id
            ).order_by(Notification.created_at.desc()).limit(5).all()
            return {'unread_notif_count': count, 'recent_notifications': recent}
        return {'unread_notif_count': 0, 'recent_notifications': []}

    with app.app_context():
        from app.models import payment  # noqa: ensure Payment table created
        from app.models import notification as _notif_model  # noqa
        db.create_all()
        from app.utils.seed import seed_data
        seed_data()

    @app.after_request
    def security_headers(response):
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    return app
