from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.models.user import User
from app.models.influencer import Influencer
from app.models.campaign import Campaign
from app.models.brand import Brand
from app import db

public_bp = Blueprint('public', __name__)


def brands_only(f):
    """Restrict a view to logged-in brand (customer) accounts. MVP launch gate."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in as a brand to browse creators.', 'warning')
            return redirect(url_for('auth.login'))
        if current_user.user_type != 'brand':
            flash('Creator discovery is available to brand accounts only.', 'warning')
            return redirect(url_for('public.home'))
        return f(*args, **kwargs)
    return decorated

NICHES = ['Tech', 'Fashion', 'Food', 'Travel', 'Fitness', 'Beauty',
          'Gaming', 'Education', 'Finance', 'Lifestyle', 'Music', 'Sports']

PLATFORMS = ['Instagram', 'TikTok', 'YouTube', 'Facebook']


@public_bp.route('/health')
def health():
    from sqlalchemy import text
    try:
        db.session.execute(text('SELECT 1'))
        return {'status': 'ok', 'db': 'connected'}, 200
    except Exception as e:
        return {'status': 'error', 'db': str(e)}, 500


@public_bp.route('/')
def home():
    top_influencers = Influencer.query.filter_by(verification_status='verified')\
                         .order_by(Influencer.creator_score.desc()).limit(8).all()
    featured_campaigns = Campaign.query.filter_by(status='open')\
                             .order_by(Campaign.created_at.desc()).limit(6).all()
    stats = {
        'influencers': Influencer.query.filter_by(verification_status='verified').count(),
        'brands':      Brand.query.filter_by(is_verified=True).count(),
        'campaigns':   Campaign.query.count(),
        'niches':      len(NICHES),
    }
    return render_template('public/home.html',
                           top_influencers=top_influencers,
                           featured_campaigns=featured_campaigns,
                           stats=stats,
                           niches=NICHES)


@public_bp.route('/discover')
@login_required
@brands_only
def discover():
    q        = request.args.get('q', '').strip()
    niche    = request.args.get('niche', '')
    platform = request.args.get('platform', '')
    min_f    = request.args.get('min_followers', 0, type=int)
    max_f    = request.args.get('max_followers', 0, type=int)

    query = Influencer.query.filter_by(verification_status='verified')\
                .join(User).filter(User.is_active == True)

    if q:
        query = query.filter(
            db.or_(User.first_name.ilike(f'%{q}%'),
                   User.last_name.ilike(f'%{q}%'),
                   Influencer.niche.ilike(f'%{q}%'),
                   Influencer.bio.ilike(f'%{q}%'))
        )
    if niche:
        query = query.filter(Influencer.niche.ilike(f'%{niche}%'))
    if min_f:
        query = query.filter(
            db.or_(Influencer.instagram_followers >= min_f,
                   Influencer.tiktok_followers >= min_f)
        )
    if max_f:
        query = query.filter(
            db.or_(Influencer.instagram_followers <= max_f,
                   Influencer.tiktok_followers <= max_f)
        )

    influencers = query.order_by(Influencer.creator_score.desc()).all()

    return render_template('public/discover.html',
                           influencers=influencers, q=q,
                           niche=niche, platform=platform,
                           niches=NICHES, platforms=PLATFORMS,
                           min_f=min_f, max_f=max_f)


@public_bp.route('/campaigns')
def campaigns():
    platform = request.args.get('platform', '')
    niche    = request.args.get('niche', '')
    q        = request.args.get('q', '').strip()

    query = Campaign.query.filter_by(status='open').join(Brand).join(User).filter(User.is_active == True)

    if platform:
        query = query.filter(Campaign.platform.ilike(f'%{platform}%'))
    if niche:
        query = query.filter(Campaign.niche.ilike(f'%{niche}%'))
    if q:
        query = query.filter(Campaign.title.ilike(f'%{q}%'))

    campaigns = query.order_by(Campaign.created_at.desc()).all()

    return render_template('public/campaigns.html',
                           campaigns=campaigns, q=q,
                           platform=platform, niche=niche,
                           niches=NICHES, platforms=PLATFORMS)


@public_bp.route('/influencer/<int:user_id>')
def influencer_profile(user_id):
    # Public influencer profiles hidden for MVP launch.
    abort(404)
