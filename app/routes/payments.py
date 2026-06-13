import hmac
import hashlib
import base64
import uuid
import requests
from datetime import datetime
from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, current_app, jsonify)
from flask_login import login_required, current_user

from app import db
from app.models.application import Application
from app.models.payment import Payment
from app.models.campaign import Campaign

payments_bp = Blueprint('payments', __name__)


# ── helpers ──────────────────────────────────────────────────────────────────

def _esewa_signature(secret: str, fields: dict, signed_fields: str) -> str:
    """HMAC-SHA256 over comma-separated values, base64-encoded."""
    message = ",".join(str(fields[k]) for k in signed_fields.split(","))
    sig = hmac.new(secret.encode(), message.encode(), hashlib.sha256).digest()
    return base64.b64encode(sig).decode()


def _require_brand():
    if not current_user.is_authenticated or current_user.user_type != 'brand':
        flash('Access denied.', 'danger')
        return redirect(url_for('public.home'))
    return None


# ── checkout ─────────────────────────────────────────────────────────────────

@payments_bp.route('/checkout/<int:application_id>', methods=['GET'])
@login_required
def checkout(application_id):
    guard = _require_brand()
    if guard:
        return guard

    app_obj = Application.query.get_or_404(application_id)
    if app_obj.campaign.brand_id != current_user.brand.brand_id:
        flash('Not authorised.', 'danger')
        return redirect(url_for('brand.dashboard'))
    if app_obj.status != 'accepted':
        flash('Can only pay for accepted applications.', 'warning')
        return redirect(url_for('brand.campaign_detail',
                                campaign_id=app_obj.campaign_id))

    amount = app_obj.campaign.budget or 0
    existing = Payment.query.filter_by(
        application_id=application_id, status='completed').first()

    return render_template('payments/checkout.html',
                           app_obj=app_obj, amount=amount,
                           already_paid=bool(existing))


# ── eSewa ─────────────────────────────────────────────────────────────────────

@payments_bp.route('/esewa/initiate/<int:application_id>', methods=['POST'])
@login_required
def esewa_initiate(application_id):
    guard = _require_brand()
    if guard:
        return guard

    app_obj = Application.query.get_or_404(application_id)
    if app_obj.campaign.brand_id != current_user.brand.brand_id:
        flash('Not authorised.', 'danger')
        return redirect(url_for('brand.dashboard'))

    amount        = float(app_obj.campaign.budget or 0)
    tx_uuid       = str(uuid.uuid4())
    product_code  = current_app.config.get('ESEWA_PRODUCT_CODE', 'EPAYTEST')
    secret        = current_app.config.get('ESEWA_SECRET', '8gBm/:&EnhH.1/q')
    base_url      = request.host_url.rstrip('/')

    signed_fields = 'total_amount,transaction_uuid,product_code'
    fields = {
        'amount':                    amount,
        'tax_amount':                0,
        'total_amount':              amount,
        'transaction_uuid':          tx_uuid,
        'product_code':              product_code,
        'product_service_charge':    0,
        'product_delivery_charge':   0,
        'success_url':               f"{base_url}{url_for('payments.esewa_success')}",
        'failure_url':               f"{base_url}{url_for('payments.esewa_failed')}",
        'signed_field_names':        signed_fields,
    }
    fields['signature'] = _esewa_signature(secret, fields, signed_fields)

    # Store pending payment
    pmt = Payment(application_id=application_id,
                  payer_id=current_user.user_id,
                  amount=amount, method='esewa',
                  transaction_id=tx_uuid, status='pending')
    db.session.add(pmt)
    db.session.commit()

    esewa_url = current_app.config.get(
        'ESEWA_URL', 'https://rc-epay.esewa.com.np/api/epay/main/v2/form')

    return render_template('payments/esewa_redirect.html',
                           fields=fields, esewa_url=esewa_url)


@payments_bp.route('/esewa/success')
def esewa_success():
    data = request.args.get('data', '')
    try:
        decoded = base64.b64decode(data).decode()
        import json
        resp = json.loads(decoded)
        tx_uuid   = resp.get('transaction_uuid', '')
        ref_id    = resp.get('ref_id', '')
        status    = resp.get('status', '')
    except Exception:
        flash('Invalid eSewa callback.', 'danger')
        return redirect(url_for('brand.dashboard'))

    pmt = Payment.query.filter_by(transaction_id=tx_uuid).first()
    if pmt and status == 'COMPLETE':
        pmt.status  = 'completed'
        pmt.paid_at = datetime.utcnow()
        db.session.commit()
        flash('Payment successful via eSewa!', 'success')
        return render_template('payments/success.html',
                               pmt=pmt, method='eSewa', ref=ref_id)

    flash('eSewa payment not confirmed.', 'warning')
    return redirect(url_for('brand.dashboard'))


@payments_bp.route('/esewa/failed')
def esewa_failed():
    tx_uuid = request.args.get('transaction_uuid', '')
    pmt = Payment.query.filter_by(transaction_id=tx_uuid).first()
    if pmt:
        pmt.status = 'failed'
        db.session.commit()
    flash('eSewa payment failed.', 'danger')
    return render_template('payments/failed.html', method='eSewa')


# ── Khalti ────────────────────────────────────────────────────────────────────

@payments_bp.route('/khalti/initiate/<int:application_id>', methods=['POST'])
@login_required
def khalti_initiate(application_id):
    guard = _require_brand()
    if guard:
        return guard

    app_obj = Application.query.get_or_404(application_id)
    if app_obj.campaign.brand_id != current_user.brand.brand_id:
        flash('Not authorised.', 'danger')
        return redirect(url_for('brand.dashboard'))

    amount_paisa  = int(float(app_obj.campaign.budget or 0) * 100)
    tx_uuid       = str(uuid.uuid4())
    secret_key    = current_app.config.get('KHALTI_SECRET_KEY', 'test_secret_key_dc74e0fd57cb46cd93832aee0a390234')
    base_url      = request.host_url.rstrip('/')

    payload = {
        'return_url':           f"{base_url}{url_for('payments.khalti_verify')}",
        'website_url':          base_url,
        'amount':               amount_paisa,
        'purchase_order_id':    tx_uuid,
        'purchase_order_name':  app_obj.campaign.title[:100],
        'customer_info': {
            'name':  current_user.full_name(),
            'email': current_user.email,
        },
    }
    khalti_url = current_app.config.get(
        'KHALTI_INITIATE_URL', 'https://a.khalti.com/api/v2/epayment/initiate/')

    try:
        resp = requests.post(khalti_url, json=payload,
                             headers={'Authorization': f'Key {secret_key}'},
                             timeout=10)
        resp.raise_for_status()
        data = resp.json()
        payment_url = data.get('payment_url', '')
    except Exception as e:
        flash(f'Khalti initiation failed: {e}', 'danger')
        return redirect(url_for('payments.checkout',
                                application_id=application_id))

    pmt = Payment(application_id=application_id,
                  payer_id=current_user.user_id,
                  amount=float(app_obj.campaign.budget or 0),
                  method='khalti', transaction_id=tx_uuid, status='pending')
    db.session.add(pmt)
    db.session.commit()

    return redirect(payment_url)


@payments_bp.route('/khalti/verify')
def khalti_verify():
    pidx       = request.args.get('pidx', '')
    tx_uuid    = request.args.get('purchase_order_id', '')
    status_str = request.args.get('status', '')

    pmt = Payment.query.filter_by(transaction_id=tx_uuid).first()

    if status_str == 'Completed' and pmt:
        secret_key  = current_app.config.get('KHALTI_SECRET_KEY', '')
        lookup_url  = current_app.config.get(
            'KHALTI_LOOKUP_URL', 'https://a.khalti.com/api/v2/epayment/lookup/')
        try:
            resp = requests.post(lookup_url, json={'pidx': pidx},
                                 headers={'Authorization': f'Key {secret_key}'},
                                 timeout=10)
            data = resp.json()
            if data.get('status') == 'Completed':
                pmt.status  = 'completed'
                pmt.paid_at = datetime.utcnow()
                db.session.commit()
                flash('Payment successful via Khalti!', 'success')
                return render_template('payments/success.html',
                                       pmt=pmt, method='Khalti', ref=pidx)
        except Exception:
            pass

    if pmt:
        pmt.status = 'failed'
        db.session.commit()
    flash('Khalti payment was not completed.', 'danger')
    return render_template('payments/failed.html', method='Khalti')
