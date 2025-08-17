from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models.swaps import SwapRequest
from app.models.notifications import Notification
from app.extensions import mongo
from bson.objectid import ObjectId

swaps_bp = Blueprint('swaps', __name__, url_prefix='/swaps')

@swaps_bp.route('/propose/<listing_id>', methods=['GET', 'POST'])
@login_required
def propose_swap(listing_id):
    requested_listing = mongo.db.listings.find_one_or_404({'_id': ObjectId(listing_id)})
    if request.method == 'POST':
        offered_listing_id = request.form.get('offered_listing_id')
        mongo.db.listings.find_one_or_404({'_id': ObjectId(offered_listing_id)})

        swap_request = SwapRequest(
            proposer_id=current_user.id,
            receiver_id=requested_listing['user_id'],
            requested_listing_id=listing_id,
            offered_listing_id=offered_listing_id
        )
        swap_request.save()

        notification = Notification(
            user_id=requested_listing['user_id'],
            message=f"{current_user.username} has proposed a swap for your item: {requested_listing['item_name']}",
            link=url_for('swaps.manage_swaps', _external=True)
        )
        notification.save()

        flash('Swap request has been sent!', 'success')
        return redirect(url_for('listings.marketplace'))

    user_listings = mongo.db.listings.find({'user_id': current_user.id})
    return render_template('swaps/propose_swap.html', requested_listing=requested_listing, user_listings=user_listings)

@swaps_bp.route('/manage')
@login_required
def manage_swaps():
    incoming_swaps = list(mongo.db.swap_requests.find({'receiver_id': current_user.id}))
    outgoing_swaps = list(mongo.db.swap_requests.find({'proposer_id': current_user.id}))

    for swap in incoming_swaps + outgoing_swaps:
        swap['proposer'] = mongo.db.users.find_one({'_id': ObjectId(swap['proposer_id'])})
        swap['receiver'] = mongo.db.users.find_one({'_id': ObjectId(swap['receiver_id'])})
        swap['requested_listing'] = mongo.db.listings.find_one({'_id': ObjectId(swap['requested_listing_id'])})
        swap['offered_listing'] = mongo.db.listings.find_one({'_id': ObjectId(swap['offered_listing_id'])})

    return render_template('swaps/manage_swaps.html', incoming_swaps=incoming_swaps, outgoing_swaps=outgoing_swaps)

@swaps_bp.route('/respond/<swap_id>/<status>', methods=['POST'])
@login_required
def respond_swap(swap_id, status):
    swap = mongo.db.swap_requests.find_one_or_404({'_id': ObjectId(swap_id)})
    if swap['receiver_id'] != current_user.id:
        flash('You do not have permission to respond to this swap request.', 'danger')
        return redirect(url_for('swaps.manage_swaps'))

    if status in ['accepted', 'declined']:
        mongo.db.swap_requests.update_one({'_id': ObjectId(swap_id)}, {'$set': {'status': status}})

        notification = Notification(
            user_id=swap['proposer_id'],
            message=f"Your swap request for '{mongo.db.listings.find_one({'_id': ObjectId(swap['requested_listing_id'])})['item_name']}' has been {status}.",
            link=url_for('swaps.manage_swaps', _external=True)
        )
        notification.save()

        flash(f'Swap request has been {status}.', 'success')
    else:
        flash('Invalid response.', 'danger')

    return redirect(url_for('swaps.manage_swaps'))