from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models.wishlist import Wishlist
from app.extensions import db
from bson.objectid import ObjectId

wishlist_bp = Blueprint('wishlist', __name__, url_prefix='/wishlist')

@wishlist_bp.route('/')
@login_required
def view_wishlist():
    """
    Displays the current user's wishlist.
    """
    wishlist_items = list(db.wishlist.find({'user_id': current_user.id}))
    for item in wishlist_items:
        item['listing'] = db.listings.find_one({'_id': ObjectId(item['listing_id'])})
    return render_template('listings/wishlist.html', wishlist_items=wishlist_items)

@wishlist_bp.route('/add/<listing_id>', methods=['POST'])
@login_required
def add_to_wishlist(listing_id):
    """
    Adds a listing to the current user's wishlist.
    """
    listing = db.listings.find_one_or_404({'_id': ObjectId(listing_id)})
    
    # Check if the item is already in the wishlist
    existing_item = db.wishlist.find_one({'user_id': current_user.id, 'listing_id': listing_id})
    
    if listing['user_id'] == current_user.id:
        flash('You cannot add your own item to your wishlist.', 'warning')
        return redirect(request.referrer or url_for('listings.marketplace'))

    if existing_item:
        flash('This item is already in your wishlist.', 'info')
    else:
        wishlist_item = Wishlist(user_id=current_user.id, listing_id=listing_id)
        wishlist_item.save()
        flash('Item added to your wishlist!', 'success')
        
    return redirect(request.referrer or url_for('listings.marketplace'))

@wishlist_bp.route('/remove/<wishlist_item_id>', methods=['POST'])
@login_required
def remove_from_wishlist(wishlist_item_id):
    """
    Removes an item from the current user's wishlist.
    """
    wishlist_item = db.wishlist.find_one_or_404({'_id': ObjectId(wishlist_item_id)})
    
    if wishlist_item['user_id'] != current_user.id:
        flash('You do not have permission to remove this item.', 'danger')
        return redirect(url_for('wishlist.view_wishlist'))
        
    db.wishlist.delete_one({'_id': ObjectId(wishlist_item_id)})
    flash('Item removed from your wishlist.', 'success')
    
    return redirect(url_for('wishlist.view_wishlist'))
