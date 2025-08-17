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

    all_listings = Listing.objects()
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
    listings = sorted(filtered_listings, key=lambda x: x.created_at, reverse=True)
    
    return render_template('listings/marketplace.html', listings=listings)


@listings_bp.route('/listing/<string:listing_id>')
def listing_detail(listing_id):
    """
    Displays the details of a single listing.
    """
    listing = Listing.objects.get(id=listing_id)
    if not listing:
        abort(404)

    # Review functionality for the listing owner
    owner_user = listing.owner  # Get the User object for the owner
    review_form = ReviewForm()
    reviews = sorted(Review.objects(reviewed_user=owner_user.id), key=lambda x: x.date_posted, reverse=True)
    
    # Calculate average rating for the owner
    avg_rating = Review.get_average_rating(owner_user.id)
    
    # Check if the current user has already reviewed this owner
    has_reviewed = False
    if current_user.is_authenticated:
        has_reviewed = Review.has_reviewed(current_user.id, owner_user.id)

    return render_template(
        'listings/listing_detail.html', 
        listing=listing,
        reviews=reviews,
        review_form=review_form,
        avg_rating=avg_rating,
        has_reviewed=has_reviewed
    )

@listings_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_listing():
    """
    Handles the creation of a new listing.
    """
    form = ListingForm()
    if form.validate_on_submit():
        image_urls = []
        if form.photos.data:
            upload_folder = os.path.join(current_app.root_path, 'static/uploads')
            os.makedirs(upload_folder, exist_ok=True)
            for photo in form.photos.data:
                if photo.filename:
                    filename = secure_filename(photo.filename)
                    photo.save(os.path.join(upload_folder, filename))
                    image_urls.append(filename)
        
        # If no photos were uploaded, use the default placeholder
        if not image_urls:
            image_urls.append('https://placehold.co/400x300/CCCCCC/333333?text=No+Image')

        listing = Listing(
            owner=current_user.id,
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            size=form.size.data,
            condition=form.condition.data,
            school_name=form.school_name.data,
            images=image_urls,
            desired_swap_items=form.desired_swap_items.data
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
    listing = Listing.objects.get(id=listing_id)
    if not listing:
        abort(404)
    if listing.user_id != current_user.id:
        flash('You do not have permission to edit this listing.', 'danger')
        return redirect(url_for('listings.marketplace'))
    
    form = EditListingForm(obj=listing)
    if form.validate_on_submit():
        image_urls = []
        if form.photos.data:
            upload_folder = os.path.join(current_app.root_path, 'static/uploads')
            os.makedirs(upload_folder, exist_ok=True)
            for photo in form.photos.data:
                if photo.filename:
                    filename = secure_filename(photo.filename)
                    photo.save(os.path.join(upload_folder, filename))
                    image_urls.append(filename)
        
        if image_urls: # Only update images if new ones were uploaded
            listing.images = image_urls

        listing.title = form.title.data
        listing.description = form.description.data
        listing.category = form.category.data
        listing.size = form.size.data
        listing.condition = form.condition.data
        listing.school_name = form.school_name.data
        listing.desired_swap_items = form.desired_swap_items.data
        listing.save()
        flash('Your listing has been updated!', 'success')
        return redirect(url_for('listings.listing_detail', listing_id=listing.id))
    elif request.method == 'GET':
        form.title.data = listing.title
        form.description.data = listing.description
        form.category.data = listing.category
        form.size.data = listing.size
        form.condition.data = listing.condition
        form.school_name.data = listing.school_name
        form.desired_swap_items.data = listing.desired_swap_items
    
    return render_template('listings/edit_listing.html', form=form, listing=listing)

@listings_bp.route('/delete/<string:listing_id>', methods=['POST'])
@login_required
def delete_listing(listing_id):
    """
    Handles the deletion of a listing.
    """
    listing = Listing.objects.get(id=listing_id)
    if not listing:
        abort(404)
    if listing.owner.id != current_user.id:
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
    user = User.objects(id=user_id).first()
    if not user:
        abort(404)
    listings = Listing.objects(owner=user.id)
    
    # Review functionality
    review_form = ReviewForm()
    reviews = sorted(Review.objects(reviewed_user=user.id), key=lambda x: x.date_posted, reverse=True)
    
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