# app/blueprints/wishlist/routes.py
from flask import Blueprint, render_template, url_for, flash, redirect, request
from flask_login import login_required, current_user
from app.models.wishlist import WishlistItem
from app.models.listings import Listing
from app.models.saved_search import SavedSearch
from app.blueprints.wishlist.forms import SavedSearchForm
from app.extensions import db


wishlist_bp = Blueprint('wishlist', __name__)

@wishlist_bp.route("/wishlist")
@login_required
def wishlist():
    """
    Displays the current user's wishlist items.
    """
    wishlist_items = WishlistItem.objects(user=current_user)
    return render_template('wishlist/wishlist.html', wishlist_items=wishlist_items, title="My Wishlist")

@wishlist_bp.route("/wishlist/add/<string:listing_id>", methods=['POST'])
@login_required
def add_to_wishlist(listing_id):
    """
    Adds a listing to the current user's wishlist.
    """
    listing = Listing.objects(id=listing_id).first_or_404()
    if WishlistItem.objects(user=current_user, listing=listing).first():
        flash('This item is already in your wishlist!', 'info')
    else:
        wishlist_item = WishlistItem(user=current_user, listing=listing)
        try:
            wishlist_item.save()
            flash('Item added to wishlist!', 'success')
        except Exception as e:
            flash(f'Error adding item to wishlist: {e}', 'danger')
    return redirect(url_for('listings.listing_detail', listing_id=listing.id))

@wishlist_bp.route("/wishlist/remove/<string:listing_id>", methods=['POST'])
@login_required
def remove_from_wishlist(listing_id):
    """
    Removes a listing from the current user's wishlist.
    """
    wishlist_item = WishlistItem.objects(user=current_user, listing=listing_id).first_or_404()
    wishlist_item.delete()
    flash('Item removed from wishlist.', 'success')
    # Redirect to wishlist page or back to listing detail
    return redirect(url_for('wishlist.wishlist'))


@wishlist_bp.route("/saved_searches")
@login_required
def saved_searches():
    """
    Displays the current user's saved search queries.
    """
    saved_searches = SavedSearch.objects(user=current_user).order_by('-date_saved')
    return render_template('wishlist/saved_searches.html', saved_searches=saved_searches, title="My Saved Searches")

@wishlist_bp.route("/saved_searches/save", methods=['GET', 'POST'])
@login_required
def save_search():
    """
    Allows the user to save their current search criteria.
    The search parameters are passed as query arguments from the marketplace.
    """
    form = SavedSearchForm()
    # Get current search parameters from the request query string
    # We'll use request.query_string to get the raw query parameters
    # and then decode it for storage.
    current_query_params = request.query_string.decode('utf-8')

    # Remove 'name' and 'submit' from query params if they exist from the form itself
    # This ensures only actual search filters are saved
    parsed_params = []
    for param in current_query_params.split('&'):
        if not param.startswith('name=') and not param.startswith('submit='):
            parsed_params.append(param)
    
    clean_query_params = '&'.join(parsed_params)


    if form.validate_on_submit():
        # Check if an identical search query (excluding name) already exists for the user
        existing_search = SavedSearch.objects(
            user=current_user,
            search_query_params=clean_query_params
        ).first()

        if existing_search:
            flash('You already have this search saved!', 'info')
        else:
            new_saved_search = SavedSearch(
                user=current_user,
                name=form.name.data,
                search_query_params=clean_query_params
            )
            new_saved_search.save()
            flash('Search saved successfully!', 'success')
        return redirect(url_for('wishlist.saved_searches'))
        
    # Pre-populate form name for convenience (e.g., from a search term)
    if request.method == 'GET':
        # Attempt to create a sensible default name from search_term or uniform_type
        default_name = "Unnamed Search"
        if request.args.get('search_term'):
            default_name = f"Search for '{request.args.get('search_term')}'"
        elif request.args.get('uniform_type') and request.args.get('uniform_type') != 'All':
            default_name = f"{request.args.get('uniform_type')} Listings"
        elif request.args.get('location'):
            default_name = f"Listings in {request.args.get('location')}"
        
        form.name.data = default_name

    return render_template('wishlist/save_search.html', title='Save Search', form=form, current_query_params=current_query_params)


@wishlist_bp.route("/saved_searches/delete/<string:search_id>", methods=['POST'])
@login_required
def delete_saved_search(search_id):
    """
    Deletes a saved search entry for the current user.
    """
    saved_search = SavedSearch.objects(id=search_id, user=current_user).first_or_404()
    saved_search.delete()
    flash('Saved search deleted.', 'success')
    return redirect(url_for('wishlist.saved_searches'))
