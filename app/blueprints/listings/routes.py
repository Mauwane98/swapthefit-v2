from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from app.models.listings import Listing
from app.models.users import User
from app.blueprints.listings.forms import ListingForm, EditListingForm # Import EditListingForm
from werkzeug.utils import secure_filename
import os
from app.utils.security import roles_required # Import roles_required decorator
from mongoengine.queryset.visitor import Q # Import Q for complex queries

# Import review-related components
from app.blueprints.reviews.forms import ReviewForm
from app.models.reviews import Review
from app.models.swaps import SwapRequest # Import SwapRequest model
from app.models.donations import Donation # Import Donation model
from app.models.payments import Order # Import Order model


listings_bp = Blueprint('listings', __name__)

@listings_bp.route('/marketplace')
def marketplace():
    """
    Displays all listings in the marketplace with search and filtering.
    """
    search_query = request.args.get('search', '').lower()
    size_filter = request.args.get('size', '').lower()
    condition_filter = request.args.get('condition', '').lower()
    listing_type_filter = request.args.get('listing_type', '').lower()
    category_filter = request.args.get('category', '').lower()
    school_filter = request.args.get('school', '').lower()


    # Filter for active and available listings
    all_listings = Listing.objects(is_active=True, status='available')
    filtered_listings = []

    for listing in all_listings:
        match = True
        if search_query:
            if search_query not in listing.title.lower() and \
               search_query not in listing.description.lower() and \
               (listing.school_name and search_query not in listing.school_name.lower()):
                match = False
        if size_filter and listing.size.lower() != size_filter:
            match = False
        if condition_filter and listing.condition.lower() != condition_filter:
            match = False
        if listing_type_filter and listing.listing_type.lower() != listing_type_filter:
            match = False
        if category_filter and listing.category.lower() != category_filter:
            match = False
        if school_filter and listing.school_name and listing.school_name.lower() != school_filter:
            match = False
        
        if match:
            filtered_listings.append(listing)

    # Sort by premium status (premium first), then by creation date in descending order (latest first)
    # This sorting is done in Python as orderBy() can require complex indexing in MongoDB.
    listings = sorted(filtered_listings, key=lambda x: (x.is_premium, x.created_at), reverse=True)
    
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
@roles_required('parent', 'school') # Only parents and schools can create listings
def create_listing():
    """
    Handles the creation of a new listing.
    """
    form = ListingForm()
    if form.validate_on_submit():
        image_urls = []
        if form.photos.data:
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            for photo in form.photos.data:
                if photo.filename:
                    filename = secure_filename(photo.filename)
                    file_path = os.path.join(upload_folder, filename)
                    photo.save(file_path)
                    # Store only the relative path or filename that can be accessed via static URL
                    image_urls.append(url_for('static', filename=f'uploads/{filename}'))
        
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
            school_name=form.school_name.data if form.school_name.data else None,
            images=image_urls,
            desired_swap_items=form.desired_swap_items.data if form.desired_swap_items.data else None,
            listing_type=form.listing_type.data,
            price=form.price.data if form.listing_type.data == 'sale' else None,
            is_premium=form.is_premium.data
        )
        listing.save()
        flash('Your listing has been created!', 'success')
        # Redirect to the parent dashboard after creating a listing
        if current_user.has_role('parent'):
            return redirect(url_for('listings.parent_dashboard'))
        elif current_user.has_role('school'):
            return redirect(url_for('listings.school_dashboard')) # Or a more specific school listings management page
        return redirect(url_for('listings.marketplace'))
    return render_template('listings/create_listings.html', form=form)

@listings_bp.route('/edit/<string:listing_id>', methods=['GET', 'POST'])
@login_required
@roles_required('parent', 'school', 'admin') # Admins can also edit any listing
def edit_listing(listing_id):
    """
    Handles editing an existing listing.
    """
    listing = Listing.objects.get(id=listing_id)
    if not listing:
        abort(404)
    
    # Only the owner or an admin can edit the listing
    if listing.owner.id != current_user.id and not current_user.has_role('admin'):
        flash('You do not have permission to edit this listing.', 'danger')
        return redirect(url_for('listings.marketplace'))
    
    form = EditListingForm(obj=listing) # Populate form with existing listing data
    if form.validate_on_submit():
        # Handle new image uploads
        if form.photos.data:
            new_image_urls = []
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            for photo in form.photos.data:
                if photo.filename:
                    filename = secure_filename(photo.filename)
                    file_path = os.path.join(upload_folder, filename)
                    photo.save(file_path)
                    new_image_urls.append(url_for('static', filename=f'uploads/{filename}'))
            
            # Replace existing images only if new ones were uploaded
            if new_image_urls:
                listing.images = new_image_urls
            # If no new photos and previous images existed, keep them. If no previous and no new, keep placeholder.
            elif not listing.images: # This covers cases where there were no images before and no new ones are uploaded
                listing.images = ['https://placehold.co/400x300/CCCCCC/333333?text=No+Image']

        listing.title = form.title.data
        listing.description = form.description.data
        listing.category = form.category.data
        listing.size = form.size.data
        listing.condition = form.condition.data
        listing.school_name = form.school_name.data if form.school_name.data else None
        listing.desired_swap_items = form.desired_swap_items.data if form.desired_swap_items.data else None
        listing.listing_type = form.listing_type.data
        listing.price = form.price.data if form.listing_type.data == 'sale' else None
        listing.is_premium = form.is_premium.data
        listing.save()
        flash('Your listing has been updated!', 'success')
        return redirect(url_for('listings.listing_detail', listing_id=listing.id))
    elif request.method == 'GET':
        # Populate form fields for GET request
        form.title.data = listing.title
        form.description.data = listing.description
        form.category.data = listing.category
        form.size.data = listing.size
        form.condition.data = listing.condition
        form.school_name.data = listing.school_name
        form.desired_swap_items.data = listing.desired_swap_items
        form.listing_type.data = listing.listing_type
        form.price.data = listing.price
        form.is_premium.data = listing.is_premium
    
    return render_template('listings/edit_listing.html', form=form, listing=listing)

@listings_bp.route('/delete/<string:listing_id>', methods=['POST'])
@login_required
@roles_required('parent', 'school', 'admin') # Only the owner, school admins, or site admins can delete
def delete_listing(listing_id):
    """
    Handles the deletion of a listing.
    """
    listing = Listing.objects.get(id=listing_id)
    if not listing:
        abort(404)
    # Only the owner or an admin can delete the listing
    if listing.owner.id != current_user.id and not current_user.has_role('admin'):
        flash('You do not have permission to delete this listing.', 'danger')
        return redirect(url_for('listings.marketplace'))
    
    # Optionally delete associated images from file system if they are not default
    for image_url in listing.images:
        # Check if it's a local static file and not the placeholder
        if image_url.startswith('/static/uploads/') and 'No+Image' not in image_url:
            filename = image_url.split('/')[-1]
            file_path = os.path.join(current_app.root_path, 'static', 'uploads', filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    current_app.logger.info(f"Deleted image file: {file_path}")
                except OSError as e:
                    current_app.logger.error(f"Error deleting image file {file_path}: {e}")

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
    listings = Listing.objects(owner=user.id, is_active=True) # Only show active listings
    
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

# --- Role-Based Dashboards ---
# The general /listings/dashboard will now redirect based on role.

@listings_bp.route('/dashboard')
@login_required
def dashboard_redirect():
    """
    Redirects authenticated users to their specific role-based dashboard.
    """
    if current_user.has_role('admin'):
        return redirect(url_for('admin.dashboard'))
    elif current_user.has_role('school'):
        return redirect(url_for('listings.school_dashboard'))
    elif current_user.has_role('ngo'):
        return redirect(url_for('listings.ngo_dashboard'))
    else: # Default to parent dashboard
        return redirect(url_for('listings.parent_dashboard'))
    

@listings_bp.route('/parent_dashboard')
@login_required
@roles_required('parent', 'admin') # Admin can also view parent dashboard
def parent_dashboard():
    """
    Displays the parent user's dashboard with their listings, swaps, and payments.
    """
    user_listings = Listing.objects(owner=current_user.id).order_by('-created_at')
    
    # Fetch pending and completed swap requests related to the current user
    # A user can be either the requester or the responder in a swap
    pending_swaps = list(SwapRequest.objects(Q(requester=current_user.id) | Q(responder=current_user.id), status='pending').order_by('-requested_date'))
    accepted_swaps = list(SwapRequest.objects(Q(requester=current_user.id) | Q(responder=current_user.id), status='accepted').order_by('-requested_date'))
    completed_swaps = SwapRequest.objects(Q(requester=current_user.id) | Q(responder=current_user.id), status='completed').order_by('-requested_date')
    
    # Fetch orders where current user is the buyer or seller
    bought_items = Order.objects(buyer=current_user.id).order_by('-order_date')
    sold_items = Order.objects(seller=current_user.id).order_by('-order_date')

    # Fetch donations made by the current user
    sent_donations = Donation.objects(donor=current_user.id).order_by('-donation_date')

    return render_template(
        'parent_dashboard.html', # Using the dedicated parent dashboard template
        user_listings=user_listings,
        pending_swaps=pending_swaps,
        accepted_swaps=accepted_swaps,
        completed_swaps=completed_swaps,
        bought_items=bought_items,
        sold_items=sold_items,
        sent_donations=sent_donations
    )

@listings_bp.route('/school_dashboard')
@login_required
@roles_required('school', 'admin')
def school_dashboard():
    """
    Displays the school's dashboard to manage listings for learners and track donations.
    """
    # Fetch listings owned by the current school user
    school_listings = Listing.objects(owner=current_user.id).order_by('-created_at')
    
    # Fetch donations received by this school
    received_donations = Donation.objects(recipient=current_user.id).order_by('-donation_date')
    
    # Calculate total items received and distributed
    total_received_items = Donation.objects(recipient=current_user.id, status__in=['received', 'distributed']).count()
    total_distributed_items = Donation.objects(recipient=current_user.id, status='distributed').count()

    # Fetch swap requests where the school is the responder
    school_received_swap_requests = SwapRequest.objects(responder=current_user.id).order_by('-requested_date')

    return render_template(
        'school_dashboard.html', # Using the dedicated school dashboard template
        school_listings=school_listings,
        received_donations=received_donations,
        total_received_items=total_received_items,
        total_distributed_items=total_distributed_items,
        school_received_swap_requests=school_received_swap_requests
    )

@listings_bp.route('/ngo_dashboard')
@login_required
@roles_required('ngo', 'admin')
def ngo_dashboard():
    """
    Displays the NGO's dashboard to receive donations, manage distributions, and run impact reports.
    """
    # Fetch donations received by this NGO
    received_donations = Donation.objects(recipient=current_user.id).order_by('-donation_date')

    # Calculate total items received and distributed
    total_received_items = Donation.objects(recipient=current_user.id, status__in=['received', 'distributed']).count()
    total_distributed_items = Donation.objects(recipient=current_user.id, status='distributed').count()

    return render_template(
        'ngo_dashboard.html', # Using the dedicated NGO dashboard template
        received_donations=received_donations,
        total_received_items=total_received_items,
        total_distributed_items=total_distributed_items
    )

