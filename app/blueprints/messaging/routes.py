from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.messages import Message
from app.models.listings import Listing
from bson.objectid import ObjectId

messaging_bp = Blueprint('messaging_bp', __name__,
                         template_folder='templates',
                         static_folder='static')

@messaging_bp.route('/send/<listing_id>', methods=['POST'])
@jwt_required()
def send_message(listing_id):
    content = request.form.get('content')
    if not content:
        flash('Message content cannot be empty.', 'danger')
        return redirect(url_for('listings_bp.listing_detail', listing_id=listing_id))

    listing = Listing.find_by_id(listing_id)
    if not listing:
        flash('Listing not found.', 'danger')
        return redirect(url_for('listings_bp.marketplace'))

    sender_id = get_jwt_identity()
    receiver_id = str(listing['owner_id'])

    if sender_id == receiver_id:
        flash("You cannot send a message to yourself.", 'warning')
        return redirect(url_for('listings_bp.listing_detail', listing_id=listing_id))

    Message.create(
        sender_id=sender_id,
        receiver_id=receiver_id,
        listing_id=listing_id,
        content=content
    )

    flash('Your message has been sent!', 'success')
    return redirect(url_for('listings_bp.listing_detail', listing_id=listing_id))

@messaging_bp.route('/inbox')
@jwt_required()
def inbox():
    current_user_id = get_jwt_identity()
    messages = Message.find_by_receiver(current_user_id)
    return render_template('messaging/inbox.html', messages=messages)
