from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models.campaign import Campaign
from app.models.application import Application
from app.models.influencer import Influencer
from app.models.brand import Brand
from app.utils.helpers import clean, save_upload

brand_bp = Blueprint('brand', __name__)


def require_brand(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.user_type != 'brand':
            flash('Access denied.', 'danger')
            return redirect(url_for('public.home'))
        return f(*args, **kwargs)
    return decorated


@brand_bp.route('/dashboard')
@login_required
@require_brand
def dashboard():
    br = current_user.brand
    campaigns = Campaign.query.filter_by(brand_id=br.brand_id)\
                    .order_by(Campaign.created_at.desc()).limit(5).all()
    total_applications = sum(len(c.applications) for c in br.campaigns)
    return render_template('brand/dashboard.html',
                           br=br, campaigns=campaigns,
                           total_applications=total_applications)


@brand_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@require_brand
def profile():
    br = current_user.brand
    if request.method == 'POST':
        current_user.first_name = clean(request.form.get('first_name', ''))
        current_user.last_name  = clean(request.form.get('last_name', ''))
        current_user.city       = clean(request.form.get('city', ''))
        phone = clean(request.form.get('phone', ''))
        if phone and (not phone.isdigit() or len(phone) not in (10, 11)):
            flash('Phone must be 10-11 digits.', 'danger')
            return render_template('brand/profile.html', br=br)
        current_user.phone = phone

        br.company_name = clean(request.form.get('company_name', ''))
        br.industry     = clean(request.form.get('industry', ''))
        br.website      = clean(request.form.get('website', ''))
        br.description  = clean(request.form.get('description', ''))

        logo = request.files.get('logo')
        saved = save_upload(logo, prefix='brand')
        if saved:
            br.logo = saved

        db.session.commit()
        flash('Profile updated!', 'success')
        return redirect(url_for('brand.profile'))

    return render_template('brand/profile.html', br=br)


@brand_bp.route('/campaigns')
@login_required
@require_brand
def my_campaigns():
    br = current_user.brand
    status = request.args.get('status', 'all')
    query = Campaign.query.filter_by(brand_id=br.brand_id)
    if status != 'all':
        query = query.filter_by(status=status)
    campaigns = query.order_by(Campaign.created_at.desc()).all()
    return render_template('brand/campaigns.html', campaigns=campaigns, status=status)


@brand_bp.route('/campaigns/create', methods=['GET', 'POST'])
@login_required
@require_brand
def create_campaign():
    from app.routes.public import NICHES, PLATFORMS
    br = current_user.brand
    if request.method == 'POST':
        title        = clean(request.form.get('title', ''))
        description  = clean(request.form.get('description', ''))
        platform     = clean(request.form.get('platform', ''))
        niche        = clean(request.form.get('niche', ''))
        deliverables = clean(request.form.get('deliverables', ''))
        location     = clean(request.form.get('location', 'Nepal'))
        deadline_str = request.form.get('deadline', '')

        if not title:
            flash('Title is required.', 'danger')
            return render_template('brand/create_campaign.html', niches=NICHES, platforms=PLATFORMS)

        try:
            budget        = float(request.form.get('budget', 0) or 0)
            min_followers = int(request.form.get('min_followers', 0) or 0)
            max_followers = int(request.form.get('max_followers', 0) or 0)
            deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date() if deadline_str else None
        except (ValueError, TypeError):
            flash('Invalid number or date.', 'danger')
            return render_template('brand/create_campaign.html', niches=NICHES, platforms=PLATFORMS)

        if budget <= 0:
            flash('Budget must be greater than 0.', 'danger')
            return render_template('brand/create_campaign.html', niches=NICHES, platforms=PLATFORMS)
        if max_followers and min_followers > max_followers:
            flash('Min followers cannot exceed max followers.', 'danger')
            return render_template('brand/create_campaign.html', niches=NICHES, platforms=PLATFORMS)
        if deadline and deadline < datetime.utcnow().date():
            flash('Deadline cannot be in the past.', 'danger')
            return render_template('brand/create_campaign.html', niches=NICHES, platforms=PLATFORMS)

        c = Campaign(brand_id=br.brand_id, title=title, description=description,
                     platform=platform, niche=niche, budget=budget,
                     deliverables=deliverables, deadline=deadline,
                     min_followers=min_followers, max_followers=max_followers,
                     location=location)
        db.session.add(c)
        db.session.commit()
        flash('Campaign created!', 'success')
        return redirect(url_for('brand.my_campaigns'))

    return render_template('brand/create_campaign.html', niches=NICHES, platforms=PLATFORMS, now=datetime.utcnow())


@brand_bp.route('/campaigns/<int:campaign_id>')
@login_required
@require_brand
def campaign_detail(campaign_id):
    br = current_user.brand
    campaign = Campaign.query.filter_by(campaign_id=campaign_id, brand_id=br.brand_id).first_or_404()
    return render_template('brand/campaign_detail.html', campaign=campaign)


@brand_bp.route('/applications/<int:application_id>/<action>', methods=['POST'])
@login_required
@require_brand
def handle_application(application_id, action):
    app = db.get_or_404(Application, application_id)
    if app.campaign.brand_id != current_user.brand.brand_id:
        flash('Not authorised.', 'danger')
        return redirect(url_for('brand.dashboard'))
    if action == 'accept':
        app.status = 'accepted'
        flash('Application accepted!', 'success')
    elif action == 'reject':
        app.status = 'rejected'
        flash('Application rejected.', 'info')
    db.session.commit()
    return redirect(url_for('brand.campaign_detail', campaign_id=app.campaign_id))


@brand_bp.route('/campaigns/<int:campaign_id>/close', methods=['POST'])
@login_required
@require_brand
def close_campaign(campaign_id):
    br = current_user.brand
    c = Campaign.query.filter_by(campaign_id=campaign_id, brand_id=br.brand_id).first_or_404()
    c.status = 'closed'
    db.session.commit()
    flash('Campaign closed.', 'info')
    return redirect(url_for('brand.my_campaigns'))
