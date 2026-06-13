from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.influencer import Influencer
from app.models.brand import Brand
from app.models.campaign import Campaign
from app.models.application import Application

admin_bp = Blueprint('admin', __name__)


def require_admin(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.user_type != 'admin':
            flash('Access denied.', 'danger')
            return redirect(url_for('public.home'))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/dashboard')
@login_required
@require_admin
def dashboard():
    stats = {
        'influencers': Influencer.query.count(),
        'brands':      Brand.query.count(),
        'campaigns':   Campaign.query.count(),
        'users':       User.query.count(),
        'pending':     Influencer.query.filter_by(verification_status='pending').count(),
        'open_campaigns': Campaign.query.filter_by(status='open').count(),
    }
    recent_users = User.query.order_by(User.created_at.desc()).limit(8).all()
    recent_campaigns = Campaign.query.order_by(Campaign.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html', stats=stats,
                           recent_users=recent_users, recent_campaigns=recent_campaigns)


@admin_bp.route('/influencers')
@login_required
@require_admin
def influencers():
    status = request.args.get('status', 'pending')
    influencers = Influencer.query.filter_by(verification_status=status).all()
    return render_template('admin/influencers.html', influencers=influencers, status=status)


@admin_bp.route('/influencers/<int:inf_id>/verify', methods=['POST'])
@login_required
@require_admin
def verify_influencer(inf_id):
    inf = Influencer.query.get_or_404(inf_id)
    action = request.form.get('action')
    if action == 'approve':
        inf.verification_status = 'verified'
        flash('Influencer verified.', 'success')
    elif action == 'reject':
        inf.verification_status = 'rejected'
        flash('Influencer rejected.', 'info')
    db.session.commit()
    return redirect(url_for('admin.influencers'))


@admin_bp.route('/brands')
@login_required
@require_admin
def brands():
    brands = Brand.query.order_by(Brand.created_at.desc()).all()
    return render_template('admin/brands.html', brands=brands)


@admin_bp.route('/brands/<int:brand_id>/toggle', methods=['POST'])
@login_required
@require_admin
def toggle_brand(brand_id):
    br = Brand.query.get_or_404(brand_id)
    br.is_verified = not br.is_verified
    db.session.commit()
    flash('Brand status updated.', 'info')
    return redirect(url_for('admin.brands'))


@admin_bp.route('/campaigns')
@login_required
@require_admin
def campaigns():
    status = request.args.get('status', 'all')
    query = Campaign.query
    if status != 'all':
        query = query.filter_by(status=status)
    campaigns = query.order_by(Campaign.created_at.desc()).all()
    return render_template('admin/campaigns.html', campaigns=campaigns, status=status)


@admin_bp.route('/users')
@login_required
@require_admin
def users():
    user_type = request.args.get('type', 'influencer')
    users = User.query.filter_by(user_type=user_type).order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users, user_type=user_type)


@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@require_admin
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    flash(f'User {"activated" if user.is_active else "suspended"}.', 'info')
    return redirect(url_for('admin.users', type=user.user_type))
