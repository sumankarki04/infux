from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import db, limiter
from app.models.user import User
from app.models.influencer import Influencer
from app.models.brand import Brand
from app.utils.helpers import clean

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit('10 per minute')
def login():
    if current_user.is_authenticated:
        return _dashboard_redirect(current_user)
    if request.method == 'POST':
        email    = clean(request.form.get('email', '')).lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been suspended.', 'danger')
                return render_template('auth/login.html')
            login_user(user)
            return _dashboard_redirect(user)
        flash('Invalid email or password.', 'danger')
    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit('5 per minute')
def register():
    if current_user.is_authenticated:
        return _dashboard_redirect(current_user)
    if request.method == 'POST':
        user_type    = clean(request.form.get('user_type', ''))
        first_name   = clean(request.form.get('first_name', ''))
        last_name    = clean(request.form.get('last_name', ''))
        email        = clean(request.form.get('email', '')).lower()
        password     = request.form.get('password', '')
        confirm      = request.form.get('confirm_password', '')
        city         = clean(request.form.get('city', ''))
        phone        = clean(request.form.get('phone', ''))

        if user_type not in ('brand', 'influencer'):
            flash('Invalid account type.', 'danger')
            return render_template('auth/register.html')
        if '@' not in email or '.' not in email:
            flash('Enter a valid email address.', 'danger')
            return render_template('auth/register.html')
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('auth/register.html')
        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('auth/register.html')

        user = User(email=email, user_type=user_type,
                    first_name=first_name, last_name=last_name,
                    city=city, phone=phone)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        if user_type == 'influencer':
            niche = clean(request.form.get('niche', ''))
            inf = Influencer(user_id=user.user_id, niche=niche)
            db.session.add(inf)
        else:
            company_name = clean(request.form.get('company_name', ''))
            industry     = clean(request.form.get('industry', ''))
            br = Brand(user_id=user.user_id,
                       company_name=company_name or first_name,
                       industry=industry)
            db.session.add(br)

        db.session.commit()
        login_user(user)
        flash('Welcome to INFUX!', 'success')
        return _dashboard_redirect(user)

    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('public.home'))


def _dashboard_redirect(user):
    if user.user_type == 'admin':
        return redirect(url_for('admin.dashboard'))
    if user.user_type == 'brand':
        return redirect(url_for('brand.dashboard'))
    return redirect(url_for('influencer.dashboard'))
