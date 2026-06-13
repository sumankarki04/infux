import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

_IS_PROD = os.environ.get('FLASK_ENV') == 'production'

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'infux-dev-secret-change-in-production')
    DEBUG = not _IS_PROD
    TESTING = False

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f'sqlite:///{os.path.join(BASE_DIR, "infux.db")}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 280,
    } if _IS_PROD else {}

    WTF_CSRF_ENABLED = True
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app', 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    SESSION_COOKIE_SECURE = _IS_PROD
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # eSewa
    ESEWA_URL          = os.environ.get('ESEWA_URL', 'https://rc-epay.esewa.com.np/api/epay/main/v2/form')
    ESEWA_SECRET       = os.environ.get('ESEWA_SECRET', '')
    ESEWA_PRODUCT_CODE = os.environ.get('ESEWA_PRODUCT_CODE', 'EPAYTEST')

    # Khalti
    KHALTI_SECRET_KEY   = os.environ.get('KHALTI_SECRET_KEY', '')
    KHALTI_INITIATE_URL = os.environ.get('KHALTI_INITIATE_URL', 'https://a.khalti.com/api/v2/epayment/initiate/')
    KHALTI_LOOKUP_URL   = os.environ.get('KHALTI_LOOKUP_URL',   'https://a.khalti.com/api/v2/epayment/lookup/')

    # Social media APIs
    INSTAGRAM_ACCESS_TOKEN = os.environ.get('INSTAGRAM_ACCESS_TOKEN', '')
    TIKTOK_CLIENT_KEY      = os.environ.get('TIKTOK_CLIENT_KEY', '')
    TIKTOK_CLIENT_SECRET   = os.environ.get('TIKTOK_CLIENT_SECRET', '')

    # Supabase client (for supabase-py SDK, separate from SQLAlchemy)
    SUPABASE_URL              = os.environ.get('SUPABASE_URL', '')
    SUPABASE_ANON_KEY         = os.environ.get('SUPABASE_ANON_KEY', '')
    SUPABASE_SERVICE_ROLE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
