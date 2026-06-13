from flask import Blueprint, request, flash, redirect, url_for
from flask_login import login_required, current_user

from app import db, limiter
from app.models.review import Review
from app.models.application import Application
from app.models.campaign import Campaign
from app.utils.helpers import clean

reviews_bp = Blueprint('reviews', __name__)


@reviews_bp.route('/submit', methods=['POST'])
@login_required
@limiter.limit("10 per hour")
def submit():
    redirect_target = request.referrer or url_for('public.home')

    # --- Parse form fields ---
    try:
        reviewee_id = int(request.form.get('reviewee_id', 0))
        campaign_id = int(request.form.get('campaign_id', 0))
        rating      = int(request.form.get('rating', 0))
    except (ValueError, TypeError):
        flash('Invalid submission data.', 'danger')
        return redirect(redirect_target)

    review_text_raw = request.form.get('review_text', '')
    review_text = clean(review_text_raw) if review_text_raw else None

    # 1. Rating range check
    if not (1 <= rating <= 5):
        flash('Rating must be between 1 and 5.', 'danger')
        return redirect(redirect_target)

    # 2. Prevent self-review
    if current_user.user_id == reviewee_id:
        flash('You cannot review yourself.', 'danger')
        return redirect(redirect_target)

    # 3 & 4. Role-based authorisation
    if current_user.user_type == 'brand':
        brand = current_user.brand
        if brand is None:
            flash('Brand profile not found.', 'danger')
            return redirect(redirect_target)

        # Campaign must belong to this brand
        campaign = Campaign.query.filter_by(
            campaign_id=campaign_id, brand_id=brand.brand_id
        ).first()
        if campaign is None:
            flash('Campaign not found or does not belong to your account.', 'danger')
            return redirect(redirect_target)

        # Reviewee's influencer must have an accepted application for this campaign
        accepted = Application.query.join(
            Application.influencer
        ).filter(
            Application.campaign_id == campaign_id,
            Application.status == 'accepted',
            Application.influencer.has(user_id=reviewee_id),
        ).first()
        if accepted is None:
            flash('This influencer does not have an accepted application for that campaign.', 'danger')
            return redirect(redirect_target)

    elif current_user.user_type == 'influencer':
        influencer = current_user.influencer
        if influencer is None:
            flash('Influencer profile not found.', 'danger')
            return redirect(redirect_target)

        # Current user must have an accepted application for this campaign
        accepted = Application.query.filter_by(
            campaign_id=campaign_id,
            influencer_id=influencer.influencer_id,
            status='accepted',
        ).first()
        if accepted is None:
            flash('You do not have an accepted application for that campaign.', 'danger')
            return redirect(redirect_target)

        # Reviewee must be the brand owner of that campaign
        campaign = Campaign.query.get(campaign_id)
        if campaign is None or campaign.brand.user_id != reviewee_id:
            flash('You can only review the brand that owns this campaign.', 'danger')
            return redirect(redirect_target)

    else:
        flash('Only brands and influencers can submit reviews.', 'danger')
        return redirect(redirect_target)

    # 5. Prevent duplicate reviews
    existing = Review.query.filter_by(
        reviewer_id=current_user.user_id,
        campaign_id=campaign_id,
    ).first()
    if existing:
        flash('You have already reviewed this campaign.', 'warning')
        return redirect(redirect_target)

    # --- Create review ---
    review = Review(
        reviewer_id=current_user.user_id,
        reviewee_id=reviewee_id,
        campaign_id=campaign_id,
        rating=rating,
        review_text=review_text,
    )
    db.session.add(review)

    # Notify the reviewee
    from app.models.user import User
    from app.utils.notifications import notify
    reviewee_user = db.session.get(User, reviewee_id)
    notify(
        user_id=reviewee_id,
        title='You received a new review',
        notif_type='review',
        body=f'{current_user.full_name()} left you a {rating}-star review.',
        link=f'/influencer/{reviewee_id}' if reviewee_user and reviewee_user.user_type == 'influencer' else '/brand/dashboard'
    )

    # Update influencer rating stats if reviewee is an influencer
    if reviewee_user and reviewee_user.user_type == 'influencer' and reviewee_user.influencer:
        db.session.flush()  # ensure the new review is visible to the query
        reviewee_user.influencer.update_rating_stats()

    db.session.commit()
    flash('Review submitted!', 'success')
    return redirect(redirect_target)
