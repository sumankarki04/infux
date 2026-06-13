from datetime import datetime
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app import db, limiter
from app.models.user import User
from app.models.message import Message
from app.utils.helpers import clean

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/inbox')
@login_required
def inbox():
    # Get all unique conversation partners
    sent_ids     = {m.receiver_id for m in current_user.sent_messages}
    received_ids = {m.sender_id   for m in current_user.received_messages}
    partner_ids  = sent_ids | received_ids
    partners = User.query.filter(User.user_id.in_(partner_ids)).all()

    conversations = []
    for p in partners:
        last_msg = Message.query.filter(
            db.or_(
                db.and_(Message.sender_id == current_user.user_id,   Message.receiver_id == p.user_id),
                db.and_(Message.sender_id == p.user_id, Message.receiver_id == current_user.user_id)
            )
        ).order_by(Message.created_at.desc()).first()
        unread = Message.query.filter_by(sender_id=p.user_id,
                                         receiver_id=current_user.user_id,
                                         is_read=False).count()
        conversations.append({'partner': p, 'last_msg': last_msg, 'unread': unread})

    conversations.sort(key=lambda x: x['last_msg'].created_at if x['last_msg'] else datetime.min, reverse=True)
    return render_template('chat/inbox.html', conversations=conversations)


@chat_bp.route('/<int:partner_id>')
@login_required
def chat(partner_id):
    partner = User.query.filter_by(user_id=partner_id).first_or_404()
    messages = Message.query.filter(
        db.or_(
            db.and_(Message.sender_id == current_user.user_id,   Message.receiver_id == partner_id),
            db.and_(Message.sender_id == partner_id, Message.receiver_id == current_user.user_id)
        )
    ).order_by(Message.created_at.asc()).all()

    # Mark received as read
    Message.query.filter_by(sender_id=partner_id,
                             receiver_id=current_user.user_id,
                             is_read=False).update({'is_read': True})
    db.session.commit()

    return render_template('chat/chat.html', partner=partner, messages=messages,
                           PARTNER_ID=partner_id)


@chat_bp.route('/<int:partner_id>/send', methods=['POST'])
@login_required
@limiter.limit("60 per minute")
def send(partner_id):
    data    = request.get_json(silent=True) or {}
    content = clean(data.get('content', ''))
    if not content:
        return jsonify({'error': 'empty'}), 400
    if len(content) > 2000:
        return jsonify({'error': 'too long'}), 400

    partner = User.query.filter_by(user_id=partner_id).first()
    if not partner:
        return jsonify({'error': 'not found'}), 404

    msg = Message(sender_id=current_user.user_id,
                  receiver_id=partner_id, content=content)
    db.session.add(msg)
    db.session.commit()
    return jsonify({
        'id':         msg.message_id,
        'content':    msg.content,
        'created_at': msg.created_at.strftime('%H:%M'),
        'sender_id':  msg.sender_id
    })


@chat_bp.route('/<int:partner_id>/messages')
@login_required
def get_messages(partner_id):
    since_id = request.args.get('since', 0, type=int)
    messages = Message.query.filter(
        db.or_(
            db.and_(Message.sender_id == current_user.user_id,   Message.receiver_id == partner_id),
            db.and_(Message.sender_id == partner_id, Message.receiver_id == current_user.user_id)
        ),
        Message.message_id > since_id
    ).order_by(Message.created_at.asc()).all()

    Message.query.filter_by(sender_id=partner_id,
                             receiver_id=current_user.user_id,
                             is_read=False).update({'is_read': True})
    db.session.commit()

    return jsonify([{
        'id':         m.message_id,
        'content':    m.content,
        'sender_id':  m.sender_id,
        'created_at': m.created_at.strftime('%H:%M'),
    } for m in messages])
