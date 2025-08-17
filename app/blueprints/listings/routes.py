from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from app.models.listings import Listing
from app.models.users import User
from app.blueprints.listings.forms import ListingForm
from werkzeug.utils import secure_filename
import os

# Import review-related components
from app.blueprints.reviews.forms import ReviewForm
from app.models.reviews import Review


listings_bp = Blueprint('listings', __name__)

@listings_bp.route('/marketplace')
def marketplace():
    """
    Displays all listings in the marketplace with search and filtering.
    """
    search_query = request.args.get('search', '').lower()
    size_filter = request.args.get('size', '').lower()
    condition_filter = request.args.get('condition', '').lower()

    all_listings = Listing.get_all()
    filtered_listings = []

    for listing in all_listings:
        match = True
        if search_query:
            if search_query not in listing.item_name.lower() and search_query not in listing.school_name.lower():
                match = False
        if size_filter and listing.size.lower() != size_filter:
            match = False
        if condition_filter and listing.condition.lower() != condition_filter:
            match = False
        
        if match:
            filtered_listings.append(listing)

    # Sort by date_posted in descending order
    listings = sorted(filtered_listings, key=lambda x: x.date_posted, reverse=True)
    
    return render_template('listings/marketplace.html', listings=listings)


@listings_bp.route('/listing/<string:listing_id>')
def listing_detail(listing_id):
    """
    Displays the details of a single listing.
    """
    listing = Listing.get_by_id(listing_id)
    if not listing:
        abort(404)
    return render_template('listings/listing_detail.html', listing=listing)

@listings_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_listing():
    """
    Handles the creation of a new listing.
    """
    form = ListingForm()
    if form.validate_on_submit():
        filename = None
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            form.image.data.save(os.path.join(current_app.root_path, 'static/uploads', filename))

        listing = Listing(
            item_name=form.item_name.data,
            description=form.description.data,
            price=form.price.data,
            size=form.size.data,
            condition=form.condition.data,
            school_name=form.school_name.data,
            image_url=filename,
            user_id=current_user.id
        )
        listing.save()
        flash('Your listing has been created!', 'success')
        return redirect(url_for('listings.marketplace'))
    return render_template('listings/create_listings.html', form=form)

@listings_bp.route('/edit/<string:listing_id>', methods=['GET', 'POST'])
@login_required
def edit_listing(listing_id):
    """
    Handles editing an existing listing.
    """
    listing = Listing.get_by_id(listing_id)
    if not listing:
        abort(404)
    if listing.user_id != current_user.id:
        flash('You do not have permission to edit this listing.', 'danger')
        return redirect(url_for('listings.marketplace'))
    
    form = ListingForm(obj=listing)
    if form.validate_on_submit():
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            form.image.data.save(os.path.join(current_app.root_path, 'static/uploads', filename))
            listing.image_url = filename

        listing.item_name = form.item_name.data
        listing.description = form.description.data
        listing.price = form.price.data
        listing.size = form.size.data
        listing.condition = form.condition.data
        listing.school_name = form.school_name.data
        listing.save()
        flash('Your listing has been updated!', 'success')
        return redirect(url_for('listings.listing_detail', listing_id=listing.id))
    
    return render_template('listings/edit_listing.html', form=form, listing=listing)

@listings_bp.route('/delete/<string:listing_id>', methods=['POST'])
@login_required
def delete_listing(listing_id):
    """
    Handles the deletion of a listing.
    """
    listing = Listing.get_by_id(listing_id)
    if not listing:
        abort(404)
    if listing.user_id != current_user.id:
        flash('You do not have permission to delete this listing.', 'danger')
        return redirect(url_for('listings.marketplace'))
    
    listing.delete()
    flash('Your listing has been deleted.', 'success')
    return redirect(url_for('listings.marketplace'))

@listings_bp.route('/user/<string:user_id>')
def user_profile(user_id):
    """
    Displays a user's profile, their listings, and their reviews.
    """
    user = User.find_by_id(user_id)
    if not user:
        abort(404)
    listings = Listing.get_by_user_id(user.id)
    
    # Review functionality
    review_form = ReviewForm()
    reviews = sorted(Review.get_by_reviewed_user(user.id), key=lambda x: x.date_posted, reverse=True)
    
    # Calculate average rating
    avg_rating = Review.get_average_rating(user.id)
    
    # Check if the current user has already reviewed this user
    has_reviewed = False
    if current_user.is_authenticated:
        has_reviewed = Review.has_reviewed(current_user.id, user.id)

    return render_template(
        'listings/user_profile.html', 
        user=user, 
        listings=listings,
        reviews=reviews,
        review_form=review_form,
        avg_rating=avg_rating,
        has_reviewed=has_reviewed
    )

@listings_bp.route('/dashboard')
@login_required
def dashboard():
    """
    Displays the user's dashboard.
    """
    return render_template('listings/dashboard.html')
