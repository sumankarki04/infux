from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db, limiter
from app.models.campaign import Campaign
from app.models.application import Application
from app.models.influencer import Influencer
from app.utils.helpers import clean, save_upload

influencer_bp = Blueprint('influencer', __name__)


def require_influencer(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.user_type != 'influencer':
            flash('Access denied.', 'danger')
            return redirect(url_for('public.home'))
        return f(*args, **kwargs)
    return decorated


@influencer_bp.route('/dashboard')
@login_required
@require_influencer
def dashboard():
    inf = current_user.influencer
    applications = Application.query.filter_by(influencer_id=inf.influencer_id)\
                       .order_by(Application.applied_at.desc()).limit(5).all()
    open_campaigns = Campaign.query.filter_by(status='open').count()
    return render_template('influencer/dashboard.html',
                           inf=inf, applications=applications,
                           open_campaigns=open_campaigns)


@influencer_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@require_influencer
def profile():
    inf = current_user.influencer
    if request.method == 'POST':
        current_user.first_name = clean(request.form.get('first_name', ''))
        current_user.last_name  = clean(request.form.get('last_name', ''))
        current_user.city       = clean(request.form.get('city', ''))
        phone = clean(request.form.get('phone', ''))
        if phone and (not phone.isdigit() or len(phone) not in (10, 11)):
            flash('Phone must be 10-11 digits.', 'danger')
            return render_template('influencer/profile.html', inf=inf)
        current_user.phone = phone

        inf.bio               = clean(request.form.get('bio', ''))
        inf.niche             = clean(request.form.get('niche', ''))
        inf.portfolio_url     = clean(request.form.get('portfolio_url', ''))
        inf.instagram_handle  = clean(request.form.get('instagram_handle', ''))
        inf.tiktok_handle     = clean(request.form.get('tiktok_handle', ''))
        inf.youtube_handle    = clean(request.form.get('youtube_handle', ''))
        inf.facebook_handle   = clean(request.form.get('facebook_handle', ''))

        try:
            inf.instagram_followers  = int(request.form.get('instagram_followers', 0) or 0)
            inf.tiktok_followers     = int(request.form.get('tiktok_followers', 0) or 0)
            inf.youtube_subscribers  = int(request.form.get('youtube_subscribers', 0) or 0)
            inf.facebook_followers   = int(request.form.get('facebook_followers', 0) or 0)
            inf.engagement_rate      = float(request.form.get('engagement_rate', 0) or 0)
        except (ValueError, TypeError):
            flash('Invalid number values.', 'danger')
            return render_template('influencer/profile.html', inf=inf)

        # Recompute creator score
        inf.creator_score = round(inf.engagement_rate * 0.4 + inf.total_followers() / 100000 * 0.6, 1)

        pic = request.files.get('profile_picture')
        saved = save_upload(pic, prefix='inf')
        if saved:
            current_user.profile_picture = saved

        db.session.commit()
        flash('Profile updated!', 'success')
        return redirect(url_for('influencer.profile'))

    return render_template('influencer/profile.html', inf=inf)


@influencer_bp.route('/campaigns')
@login_required
@require_influencer
def browse_campaigns():
    inf = current_user.influencer
    applied_ids = {a.campaign_id for a in inf.applications}
    campaigns = Campaign.query.filter_by(status='open')\
                    .order_by(Campaign.created_at.desc()).all()
    return render_template('influencer/campaigns.html',
                           campaigns=campaigns, applied_ids=applied_ids)


@influencer_bp.route('/apply/<int:campaign_id>', methods=['POST'])
@login_required
@require_influencer
@limiter.limit("20 per hour")
def apply(campaign_id):
    inf = current_user.influencer
    campaign = db.get_or_404(Campaign, campaign_id)

    if Application.query.filter_by(campaign_id=campaign_id,
                                   influencer_id=inf.influencer_id).first():
        flash('Already applied.', 'warning')
        return redirect(url_for('influencer.browse_campaigns'))

    message = clean(request.form.get('message', ''))
    app = Application(campaign_id=campaign_id,
                      influencer_id=inf.influencer_id,
                      message=message)
    db.session.add(app)
    db.session.commit()
    flash('Application submitted!', 'success')
    return redirect(url_for('influencer.my_applications'))


@influencer_bp.route('/applications')
@login_required
@require_influencer
def my_applications():
    from app.models.review import Review
    inf = current_user.influencer
    applications = Application.query.filter_by(influencer_id=inf.influencer_id)\
                       .order_by(Application.applied_at.desc()).all()
    reviewed_campaign_ids = {
        r.campaign_id for r in
        Review.query.filter_by(reviewer_id=current_user.user_id).all()
    }
    return render_template('influencer/applications.html',
                           applications=applications,
                           reviewed_campaign_ids=reviewed_campaign_ids)


@influencer_bp.route('/verify-social', methods=['POST'])
@login_required
@require_influencer
def verify_social():
    """Trigger live follower count verification from Instagram or TikTok."""
    from app.services.social import verify_instagram, verify_tiktok
    platform = request.form.get('platform', '').lower()
    inf      = current_user.influencer

    if platform == 'instagram':
        username = inf.instagram_handle or ''
        if not username:
            flash('Add your Instagram username in your profile first.', 'warning')
            return redirect(url_for('influencer.profile'))
        result = verify_instagram(username)
        if result['verified']:
            inf.instagram_followers = result['followers']
            db.session.commit()
            flash(f"Instagram verified: {result['followers']:,} followers.", 'success')
        else:
            flash(f"Instagram verification failed: {result['error']}", 'warning')

    elif platform == 'tiktok':
        username = inf.tiktok_handle or ''
        if not username:
            flash('Add your TikTok username in your profile first.', 'warning')
            return redirect(url_for('influencer.profile'))
        result = verify_tiktok(username)
        if result['verified']:
            inf.tiktok_followers = result['followers']
            db.session.commit()
            flash(f"TikTok verified: {result['followers']:,} followers.", 'success')
        else:
            flash(f"TikTok verification failed: {result['error']}", 'warning')
    else:
        flash('Unknown platform.', 'danger')

    return redirect(url_for('influencer.profile'))
