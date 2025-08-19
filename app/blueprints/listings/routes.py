# app/blueprints/listings/routes.py
from flask import Blueprint, render_template, url_for, flash, redirect, request, current_app
from flask_login import login_required, current_user
from app.models.listings import Listing
from app.models.users import User
from app.models.wishlist import WishlistItem
from app.models.saved_search import SavedSearch
from app.extensions import db
from app.blueprints.listings.forms import ListingForm
from werkzeug.utils import secure_filename
import os
import secrets
import json
from urllib.parse import parse_qs
from app.models.swaps import SwapRequest # Import SwapRequest model
from mongoengine.errors import NotUniqueError
from mongoengine.queryset.visitor import Q # Import Q for complex queries

# Import the add_notification helper function
from app.blueprints.notifications.routes import add_notification
# Import the activity logger
from app.utils.activity_logger import log_activity

listings_bp = Blueprint('listings', __name__)

def save_picture(form_picture):
    """
    Saves the uploaded picture to the static/uploads directory.
    Generates a random filename to prevent collisions.
    """
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/uploads', picture_fn)

    try:
        form_picture.save(picture_path)
        return picture_fn
    except Exception as e:
        current_app.logger.error(f"Error saving picture {form_picture.filename}: {e}")
        flash('Failed to save image. Please try again.', 'danger')
        return None

@listings_bp.route("/listing/new", methods=['GET', 'POST'])
@login_required
def create_listing():
    """
    Handles the creation of new listings.
    Renders a form for users to input listing details.
    Also triggers notifications for matching saved searches.
    Logs listing creation activity.
    """
    form = ListingForm()
    if form.validate_on_submit():
        picture_file = 'default.jpg'
        if form.image.data:
            picture_file = save_picture(form.image.data)
            if picture_file is None:
                return render_template('listings/create_listings.html', title='Create Listing', form=form)

        try:
            listing = Listing(
                title=form.title.data,
                description=form.description.data,
                price=form.price.data,
                uniform_type=form.uniform_type.data,
                condition=form.condition.data,
                size=form.size.data,
                gender=form.gender.data,
                school_name=form.school_name.data,
                location=form.location.data,
                listing_type=form.listing_type.data,
                brand=form.brand.data,
                color=form.color.data,
                image_file=picture_file,
                user=current_user
            )
            listing.save()

            flash('Your listing has been created!', 'success')

            # Log listing creation activity
            log_activity(
                user_id=current_user.id,
                action_type='listing_created',
                description=f"Created new listing: '{listing.title}' (ID: {listing.id})",
                payload={'listing_id': str(listing.id), 'listing_type': listing.listing_type},
                request_obj=request
            )

            # --- Trigger Saved Search Notifications ---
            all_saved_searches = SavedSearch.objects()
            for saved_search in all_saved_searches:
                saved_params = parse_qs(saved_search.search_query_params)
                
                match = True
                if 'search_term' in saved_params and saved_params['search_term'][0].lower() not in listing.title.lower() and \
                   saved_params['search_term'][0].lower() not in listing.description.lower() and \
                   saved_params['search_term'][0].lower() not in (listing.school_name or '').lower() and \
                   saved_params['search_term'][0].lower() not in (listing.brand or '').lower():
                    match = False
                
                if 'location' in saved_params and saved_params['location'][0].lower() not in listing.location.lower():
                    match = False
                
                if 'uniform_type' in saved_params and saved_params['uniform_type'][0] != 'All' and \
                   saved_params['uniform_type'][0] != listing.uniform_type:
                    match = False

                if 'brand' in saved_params and saved_params['brand'][0] != 'All' and \
                   saved_params['brand'][0].lower() not in (listing.brand or '').lower():
                    match = False

                if 'color' in saved_params and saved_params['color'][0] != 'All' and \
                   saved_params['color'][0].lower() not in (listing.color or '').lower():
                    match = False

                if 'condition' in saved_params and saved_params['condition'][0] != 'All' and \
                   saved_params['condition'][0] != listing.condition:
                    match = False
                
                if 'listing_type' in saved_params and saved_params['listing_type'][0] != 'All' and \
                   saved_params['listing_type'][0] != listing.listing_type:
                    match = False
                
                if 'gender' in saved_params and saved_params['gender'][0] != 'All' and \
                   saved_params['gender'][0] != listing.gender:
                    match = False

                if 'size' in saved_params and saved_params['size'][0] != 'All' and \
                   saved_params['size'][0] != listing.size:
                    match = False
                
                if 'min_price' in saved_params and listing.price is not None and \
                   float(saved_params['min_price'][0]) > listing.price:
                    match = False
                
                if 'max_price' in saved_params and listing.price is not None and \
                   float(saved_params['max_price'][0]) < listing.price:
                    match = False
                
                if match and saved_search.user.id != current_user.id:
                    add_notification(
                        user_id=saved_search.user.id,
                        message=f"New listing matching your saved search '{saved_search.name or 'Unnamed Search'}': {listing.title}",
                        notification_type='saved_search_match',
                        payload={'listing_id': str(listing.id)}
                    )

            return redirect(url_for('listings.dashboard'))
        except NotUniqueError as e:
            flash(f'A listing with this title already exists. Please choose a different title.', 'danger')
            current_app.logger.error(f"Listing creation failed due to duplicate title: {e}")
        except Exception as e:
            flash(f'An unexpected error occurred while creating your listing: {str(e)}', 'danger')
            current_app.logger.error(f"Listing creation general error: {e}")
            log_activity(
                user_id=current_user.id,
                action_type='listing_creation_failed',
                description=f"Failed to create listing: {form.title.data} due to unexpected error.",
                payload={'error': str(e)},
                request_obj=request
            )
    return render_template('listings/create_listings.html', title='Create Listing', form=form)

@listings_bp.route("/marketplace")
def marketplace():
    """
    Displays all available listings with advanced search and filtering capabilities.
    Users can search by keywords and filter by various criteria.
    """
    query = Listing.objects(is_available=True)

    # --- Search and Filtering Logic ---
    search_term = request.args.get('search_term')
    if search_term:
        query = query.filter(
            Q(title__icontains=search_term) |
            Q(description__icontains=search_term) |
            Q(school_name__icontains=search_term) |
            Q(brand__icontains=search_term)
        )

    location_filter = request.args.get('location')
    if location_filter:
        query = query.filter(location__icontains=location_filter)

    uniform_type_filter = request.args.get('uniform_type')
    if uniform_type_filter and uniform_type_filter != 'All':
        query = query.filter(uniform_type=uniform_type_filter)

    brand_filter = request.args.get('brand')
    if brand_filter and brand_filter != 'All':
        query = query.filter(brand__icontains=brand_filter)

    color_filter = request.args.get('color')
    if color_filter and color_filter != 'All':
        query = query.filter(color__icontains=color_filter)

    condition_filter = request.args.get('condition')
    if condition_filter and condition_filter != 'All':
        query = query.filter(condition=condition_filter)

    listing_type_filter = request.args.get('listing_type')
    if listing_type_filter and listing_type_filter != 'All':
        query = query.filter(listing_type=listing_type_filter)
    
    gender_filter = request.args.get('gender')
    if gender_filter and gender_filter != 'All':
        query = query.filter(gender=gender_filter)

    size_filter = request.args.get('size')
    if size_filter and size_filter != 'All':
        query = query.filter(size=size_filter)

    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    if min_price is not None:
        query = query.filter(price__gte=min_price)
    if max_price is not None:
        query = query.filter(price__lte=max_price)
    
    premium_listings = list(query.filter(is_premium=True).order_by('-date_posted'))
    
    non_premium_listings = list(query.filter(is_premium=False).order_by('-date_posted'))

    listings = premium_listings + non_premium_listings

    page = request.args.get('page', 1, type=int)
    per_page = 12
    paginated_listings = listings[(page - 1) * per_page : page * per_page]
    total_pages = (len(listings) + per_page - 1) // per_page

    uniform_types = ['All', 'School Uniform', 'Sports Kit', 'Casual Wear', 'Formal Wear']
    conditions = ['All', 'New', 'Used - Like New', 'Used - Good', 'Used - Fair', 'Used - Poor']
    listing_types = ['All', 'sale', 'swap', 'donation']
    genders = ['All', 'Male', 'Female', 'Unisex']
    sizes = ['All', 'Small', 'Medium', 'Large', 'XS', 'XL', 'XXL', 'Age 2-3', 'Age 4-5', 'Age 6-7', 'Age 8-9', 'Age 10-11', 'Age 12-13', 'Age 14-15', 'Age 16+']
    brands = ['All', 'Nike', 'Adidas', 'Puma', 'Under Armour', 'Reebok', 'School Brand', 'Other']
    colors = ['All', 'Red', 'Blue', 'Green', 'Yellow', 'Black', 'White', 'Grey', 'Brown', 'Pink', 'Purple', 'Orange', 'Multi-color']

    return render_template(
        'listings/marketplace.html',
        listings=paginated_listings,
        page=page,
        total_pages=total_pages,
        search_term=search_term if search_term else '',
        location_filter=location_filter if location_filter else '',
        uniform_type_filter=uniform_type_filter if uniform_type_filter else 'All',
        brand_filter=brand_filter if brand_filter else 'All',
        color_filter=color_filter if color_filter else 'All',
        condition_filter=condition_filter if condition_filter else 'All',
        listing_type_filter=listing_type_filter if listing_type_filter else 'All',
        gender_filter=gender_filter if gender_filter else 'All',
        size_filter=size_filter if size_filter else 'All',
        min_price=min_price,
        max_price=max_price,
        uniform_types=uniform_types,
        conditions=conditions,
        listing_types=listing_types,
        genders=genders,
        sizes=sizes,
        brands=brands,
        colors=colors
    )

@listings_bp.route("/listing/<string:listing_id>")
def listing_detail(listing_id):
    """
    Displays the detailed information for a single listing.
    Also checks if the listing is in the current user's wishlist.
    """
    listing = Listing.objects(id=listing_id).first_or_404()
    in_wishlist = False
    if current_user.is_authenticated:
        in_wishlist = WishlistItem.objects(user=current_user.id, listing=listing.id).first() is not None
    
    return render_template('listings/listing_detail.html', title=listing.title, listing=listing, in_wishlist=in_wishlist)

@listings_bp.route("/listing/<string:listing_id>/update", methods=['GET', 'POST'])
@login_required
def edit_listing(listing_id):
    """
    Allows the user to edit their existing listings.
    Also triggers notifications for wishlist updates.
    Logs listing update activity.
    """
    listing = Listing.objects(id=listing_id).first_or_404()
    if listing.user != current_user:
        flash('You do not have permission to edit this listing.', 'danger')
        return redirect(url_for('listings.listing_detail', listing_id=listing.id))

    form = ListingForm(obj=listing)
    
    old_price = listing.price
    old_condition = listing.condition
    old_is_available = listing.is_available

    if form.validate_on_submit():
        picture_file = listing.image_file
        if form.image.data:
            picture_file = save_picture(form.image.data)
            if picture_file is None:
                return render_template('listings/edit_listing.html', title='Edit Listing', form=form, listing=listing)
            listing.image_file = picture_file
        
        try:
            # Store old values of all fields that can be updated for logging changes
            old_listing_data = {
                'title': listing.title,
                'description': listing.description,
                'price': listing.price,
                'uniform_type': listing.uniform_type,
                'condition': listing.condition,
                'size': listing.size,
                'gender': listing.gender,
                'school_name': listing.school_name,
                'location': listing.location,
                'listing_type': listing.listing_type,
                'is_premium': listing.is_premium,
                'brand': listing.brand,
                'color': listing.color,
                'image_file': listing.image_file,
                'is_available': listing.is_available
            }

            listing.title = form.title.data
            listing.description = form.description.data
            listing.price = form.price.data
            listing.uniform_type = form.uniform_type.data
            listing.condition = form.condition.data
            listing.size = form.size.data
            listing.gender = form.gender.data
            listing.school_name = form.school_name.data
            listing.location = form.location.data
            listing.listing_type = form.listing_type.data
            listing.is_premium = form.is_premium.data
            listing.brand = form.brand.data
            listing.color = form.color.data

            listing.save()
            flash('Your listing has been updated!', 'success')

            # Log listing update activity
            updated_fields = {}
            for field, old_value in old_listing_data.items():
                new_value = getattr(listing, field)
                if old_value != new_value:
                    updated_fields[field] = {'old': old_value, 'new': new_value}

            log_activity(
                user_id=current_user.id,
                action_type='listing_updated',
                description=f"Updated listing: '{listing.title}' (ID: {listing.id})",
                payload={'listing_id': str(listing.id), 'changes': updated_fields},
                request_obj=request
            )

            # --- Trigger Wishlist Notifications ---
            wishlist_items = WishlistItem.objects(listing=listing.id)
            
            for item in wishlist_items:
                user = item.user
                if user.id == current_user.id:
                    continue

                notification_message = []
                payload = {'listing_id': str(listing.id)}

                if listing.price != old_price:
                    notification_message.append(f"Price for '{listing.title}' changed from R{old_price if old_price is not None else 'N/A'} to R{listing.price if listing.price is not None else 'N/A'}.")
                    payload['old_price'] = old_price
                    payload['new_price'] = listing.price
                
                if listing.condition != old_condition:
                    notification_message.append(f"Condition for '{listing.title}' updated from '{old_condition}' to '{listing.condition}'.")
                    payload['old_condition'] = old_condition
                    payload['new_condition'] = listing.condition
                
                if listing.is_available != old_is_available:
                    if not listing.is_available:
                        notification_message.append(f"'{listing.title}' is no longer available.")
                    else:
                        notification_message.append(f"'{listing.title}' is now available again!")
                    payload['old_availability'] = old_is_available
                    payload['new_availability'] = listing.is_available

                if notification_message:
                    add_notification(
                        user_id=user.id,
                        message=" ".join(notification_message),
                        notification_type='wishlist_update',
                        payload=payload
                    )

            return redirect(url_for('listings.listing_detail', listing_id=listing.id))
        except Exception as e:
            flash(f'An unexpected error occurred while updating your listing: {str(e)}', 'danger')
            current_app.logger.error(f"Listing update general error: {e}")
            log_activity(
                user_id=current_user.id,
                action_type='listing_update_failed',
                description=f"Failed to update listing: {listing.title} (ID: {listing.id}) due to unexpected error.",
                payload={'listing_id': str(listing.id), 'error': str(e)},
                request_obj=request
            )
    elif request.method == 'GET':
        form.title.data = listing.title
        form.description.data = listing.description
        form.price.data = listing.price
        form.uniform_type.data = listing.uniform_type
        form.condition.data = listing.condition
        form.size.data = listing.size
        form.gender.data = listing.gender
        form.school_name.data = listing.school_name
        form.location.data = listing.location
        form.listing_type.data = listing.listing_type
        form.is_premium.data = listing.is_premium
        form.brand.data = listing.brand
        form.color.data = listing.color

    return render_template('listings/edit_listing.html', title='Edit Listing', form=form, listing=listing)

@listings_bp.route("/listing/<string:listing_id>/delete", methods=['POST'])
@login_required
def delete_listing(listing_id):
    """
    Allows the user to delete their listings.
    Logs listing deletion activity.
    """
    listing = Listing.objects(id=listing_id).first_or_404()
    if listing.user != current_user:
        flash('You do not have permission to delete this listing.', 'danger')
        return redirect(url_for('listings.dashboard'))
    
    # Delete image file if it's not the default
    if listing.image_file and listing.image_file != 'default.jpg':
        try:
            image_path = os.path.join(current_app.root_path, 'static/uploads', listing.image_file)
            if os.path.exists(image_path):
                os.remove(image_path)
                current_app.logger.info(f"Deleted image file: {listing.image_file}")
            else:
                current_app.logger.warning(f"Image file not found for deletion: {listing.image_file}")
        except Exception as e:
            current_app.logger.error(f"Error deleting image file {listing.image_file}: {e}")
            flash(f'Error deleting associated image file. Listing will still be removed.', 'warning')

    try:
        listing.delete()
        flash('Your listing has been deleted!', 'success')
        # Log successful listing deletion
        log_activity(
            user_id=current_user.id,
            action_type='listing_deleted',
            description=f"Deleted listing: '{listing.title}' (ID: {listing.id})",
            payload={'listing_id': str(listing.id), 'listing_title': listing.title},
            request_obj=request
        )
    except Exception as e:
        flash(f'An unexpected error occurred while deleting your listing: {str(e)}', 'danger')
        current_app.logger.error(f"Listing deletion general error: {e}")
        log_activity(
            user_id=current_user.id,
            action_type='listing_deletion_failed',
            description=f"Failed to delete listing: {listing.title} (ID: {listing.id}) due to unexpected error.",
            payload={'listing_id': str(listing.id), 'error': str(e)},
            request_obj=request
        )
    return redirect(url_for('listings.dashboard'))

@listings_bp.route("/dashboard")
@login_required
def dashboard():
    """
    Displays the current user's dashboard based on their role.
    """
    user_role = current_user.role
    listings = Listing.objects(user=current_user.id).order_by('-date_posted')

    if user_role == 'parent':
        # Fetch pending and accepted swaps for the current user
        pending_swaps = list(SwapRequest.objects(
            (Q(requester=current_user.id) | Q(responder=current_user.id)),
            status='pending'
        ).order_by('-requested_date'))

        accepted_swaps = list(SwapRequest.objects(
            (Q(requester=current_user.id) | Q(responder=current_user.id)),
            status='accepted'
        ).order_by('-requested_date'))

        return render_template('parent_dashboard.html', listings=listings, pending_swaps=pending_swaps, accepted_swaps=accepted_swaps)
    elif user_role == 'school':
        return render_template(
            'school_dashboard.html', 
            listings=listings,
            total_donations_value=current_user.total_donations_value
        )
    elif user_role == 'ngo':
        return render_template(
            'ngo_dashboard.html', 
            listings=listings,
            total_donations_received_count=current_user.total_donations_received_count,
            total_donations_value=current_user.total_donations_value,
            total_families_supported_ytd=current_user.total_families_supported_ytd
        )
    elif user_role == 'admin':
        return render_template('listings/dashboard.html', listings=listings)
    else:
        return render_template('listings/dashboard.html', listings=listings)


@listings_bp.route("/user/<string:user_id>")
def user_profile(user_id):
    """
    Displays the public profile of a user, including their listings.
    """
    user = User.objects(id=user_id).first_or_404()
    listings = Listing.objects(user=user.id, is_available=True).order_by('-date_posted')
    return render_template('listings/user_profile.html', user=user, listings=listings)

@listings_bp.route("/wishlist_placeholder")
@login_required
def wishlist_placeholder():
    """
    Placeholder for the wishlist page. This route will be removed once the
    wishlist blueprint is fully integrated and functioning.
    """
    flash('Please use the new Wishlist page under My Account!', 'info')
    return redirect(url_for('wishlist.wishlist'))