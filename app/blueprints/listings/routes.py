# app/blueprints/listings/routes.py
from flask import Blueprint, render_template, url_for, flash, redirect, request, current_app, session
from flask_login import login_required, current_user
from app.models.listings import Listing
from app.models.users import User
from app.models.wishlist import WishlistItem
from app.models.saved_search import SavedSearch
from app.extensions import db
from app.blueprints.listings.forms import ListingForm, BulkUploadForm # Update this import
from werkzeug.utils import secure_filename
import os
import secrets
import json
from urllib.parse import parse_qs
from app.models.swaps import SwapRequest # Import SwapRequest model
from app.models.payments import Order # Import Order model
from app.models.donations import Donation # Import Donation model
from app.models.reviews import Review # Import Review model
from mongoengine.errors import NotUniqueError
from mongoengine.queryset.visitor import Q # Import Q for complex queries
import csv # Add this import at the top

# Import the add_notification helper function
from app.blueprints.notifications.routes import add_notification
# Import the activity logger
from app.utils.activity_logger import log_activity
from app.utils.security import roles_required # Import roles_required
from app.services.fraud_detection_service import FraudDetectionService

listings_bp = Blueprint('listings', __name__)

def save_pictures(form_pictures):
    """
    Saves uploaded pictures to the static/uploads directory.
    Generates random filenames to prevent collisions.
    Returns a list of saved filenames.
    """
    saved_filenames = []
    for form_picture in form_pictures:
        if form_picture:
            random_hex = secrets.token_hex(8)
            _, f_ext = os.path.splitext(form_picture.filename)
            picture_fn = random_hex + f_ext
            picture_path = os.path.join(current_app.root_path, 'static/uploads', picture_fn)

            try:
                form_picture.save(picture_path)
                saved_filenames.append(picture_fn)
            except Exception as e:
                current_app.logger.error(f"Error saving picture {form_picture.filename}: {e}")
                flash('Failed to save one or more images. Please try again.', 'danger')
                return [] # Return empty list if any save fails
    return saved_filenames



@listings_bp.route("/listing/new", methods=['GET', 'POST'])
@login_required
def create_listing():
    """
    Handles the creation of new listings using a multi-step form.
    Stores partial data in session.
    """
    form = ListingForm()
    current_step = int(request.args.get('step', 1)) # Get step from query param or default to 1

    if request.method == 'POST':
        # Load data from session into form before validation
        listing_data = session.get('listing_data', {})
        form.process(data=listing_data) # This will populate fields from session

        # Set the form's step data based on the current_step from the URL
        form.step.data = str(current_step)

        if form.validate_on_submit():
            # Store data in session
            listing_data = session.get('listing_data', {})
            
            if current_step == 1:
                listing_data['title'] = form.title.data
                listing_data['description'] = form.description.data
                listing_data['uniform_type'] = form.uniform_type.data
                listing_data['condition'] = form.condition.data
                listing_data['size'] = form.size.data
                listing_data['gender'] = form.gender.data
                listing_data['school_name'] = form.school_name.data
                listing_data['location'] = form.location.data
            elif current_step == 2:
                image_files = []
                if form.images.data:
                    image_files = save_pictures(form.images.data)
                    if not image_files:
                        flash('Failed to save images. Please try again.', 'danger')
                        return render_template('listings/create_listings.html', title='Create Listing', form=form, current_step=current_step)
                listing_data['image_files'] = image_files if image_files else ['default.jpg']
            elif current_step == 3:
                listing_data['price'] = form.price.data
                listing_data['listing_type'] = form.listing_type.data
                listing_data['brand'] = form.brand.data
                listing_data['color'] = form.color.data
                listing_data['is_premium'] = form.is_premium.data
            
            session['listing_data'] = listing_data

            if current_step < 3:
                return redirect(url_for('listings.create_listing', step=current_step + 1))
            else: # Final step, create listing
                try:
                    listing = Listing(
                        title=listing_data['title'],
                        description=listing_data['description'],
                        price=listing_data.get('price'), # Use .get for optional fields
                        uniform_type=listing_data['uniform_type'],
                        condition=listing_data['condition'],
                        size=listing_data['size'],
                        gender=listing_data['gender'],
                        school_name=listing_data.get('school_name'),
                        location=listing_data['location'],
                        listing_type=listing_data['listing_type'],
                        brand=listing_data.get('brand'),
                        color=listing_data.get('color'),
                        image_files=listing_data.get('image_files', ['default.jpg']),
                        is_premium=listing_data.get('is_premium', False),
                        user=current_user
                    )
                    listing.save()
                    FraudDetectionService.analyze_listing_for_suspicion(listing.id)

                    flash('Your listing has been created!', 'success')

                    # Clear session data
                    session.pop('listing_data', None)

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
                        description=f"Failed to create listing: {listing_data.get('title', 'N/A')} due to unexpected error.",
                        payload={'error': str(e)},
                        request_obj=request
                    )
        else: # Form validation failed
            flash('Please correct the errors in the form.', 'danger')
            current_app.logger.error(f"Form validation errors: {form.errors}") # Add this line for debugging
            # Pre-populate form with session data if available
            listing_data = session.get('listing_data', {})
            form.process(data=listing_data) # This will populate fields from session
            # For images, you might need a custom way to display previously uploaded images
            # if current_step == 2 and 'image_files' in listing_data:
            #     form.images.data = listing_data['image_files'] # This won't work directly for FileField
    
    elif request.method == 'GET':
        # Pre-populate form with data from session if available
        listing_data = session.get('listing_data', {})
        form.process(data=listing_data) # This will populate fields from session
        # For images, you might need a custom way to display previously uploaded images
        # if current_step == 2 and 'image_files' in listing_data:
        #     form.images.data = listing_data['image_files'] # This won't work directly for FileField

    return render_template('listings/create_listings.html', title='Create Listing', form=form, current_step=current_step)

@listings_bp.route("/bulk_upload", methods=['GET', 'POST'])
@login_required
@roles_required('school', 'ngo') # Only schools and NGOs can bulk upload
def bulk_upload():
    """
    Handles bulk uploading of listings via CSV for schools and NGOs.
    """
    form = BulkUploadForm()
    if form.validate_on_submit():
        csv_file = form.csv_file.data
        
        # Read the CSV file
        stream = csv_file.stream.read().decode("utf-8")
        reader = csv.DictReader(stream.splitlines())

        successful_uploads = 0
        failed_uploads = []

        for i, row in enumerate(reader):
            try:
                # Basic validation and type conversion for each field
                title = row.get('title')
                description = row.get('description')
                price = float(row.get('price')) if row.get('price') else None
                uniform_type = row.get('uniform_type')
                condition = row.get('condition')
                size = row.get('size')
                gender = row.get('gender')
                school_name = row.get('school_name')
                location = row.get('location')
                listing_type = row.get('listing_type')
                brand = row.get('brand')
                color = row.get('color')

                # Validate required fields
                if not all([title, description, uniform_type, condition, size, gender, location, listing_type]):
                    raise ValueError(f"Missing required fields in row {i+1}")

                # Create Listing object
                listing = Listing(
                    title=title,
                    description=description,
                    price=price,
                    uniform_type=uniform_type,
                    condition=condition,
                    size=size,
                    gender=gender,
                    school_name=school_name,
                    location=location,
                    listing_type=listing_type,
                    brand=brand,
                    color=color,
                    image_files=['default.jpg'], # Default image for bulk uploads
                    user=current_user
                )
                listing.save()
                successful_uploads += 1
            except Exception as e:
                failed_uploads.append(f"Row {i+1}: {e} - Data: {row}")
                current_app.logger.error(f"Bulk upload error: {e} in row {i+1} - Data: {row}")

        if successful_uploads > 0:
            flash(f'Successfully uploaded {successful_uploads} listings!', 'success')
        if failed_uploads:
            flash(f'Failed to upload {len(failed_uploads)} listings. See logs for details.', 'danger')
            # Optionally, save failed_uploads to a session or file for user download
        
        return redirect(url_for('listings.my_listings')) # Redirect to user's listings

    return render_template('listings/bulk_upload.html', title='Bulk Upload Listings', form=form)

@listings_bp.route("/api/search_suggestions")
def search_suggestions():
    query = request.args.get('query', '')
    if not query:
        return jsonify([])

    # Search for titles, descriptions, school names, brands that match the query
    # Using distinct() to avoid duplicates
    titles = [l.title for l in Listing.objects(title__icontains=query).limit(5)]
    descriptions = [l.description for l in Listing.objects(description__icontains=query).limit(5)]
    school_names = [l.school_name for l in Listing.objects(school_name__icontains=query).limit(5) if l.school_name]
    brands = [l.brand for l in Listing.objects(brand__icontains=query).limit(5) if l.brand]

    suggestions = list(set(titles + descriptions + school_names + brands))
    return jsonify(suggestions)

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

    # Prepare listings for template, ensuring image_files is handled
    listings_for_template = []
    for listing in paginated_listings:
        listing_dict = listing.to_dict() # Use the custom to_dict method
        # Ensure image_file is set to the first image in image_files for compatibility
        listing_dict['image_file'] = listing.image_files[0] if listing.image_files else 'default.jpg'
        listings_for_template.append(listing_dict)

    return render_template(
        'listings/marketplace.html',
        listings=listings_for_template, # Pass the modified list
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
        # Handle image uploads and removals
        # Get existing images that the user wants to keep
        existing_image_filenames_str = request.form.get('existing_image_filenames', '')
        images_to_keep = [f.strip() for f in existing_image_filenames_str.split(',') if f.strip()] if existing_image_filenames_str else []

        # Identify images to delete from the filesystem
        images_to_delete = [img for img in listing.image_files if img not in images_to_keep and img != 'default.jpg']
        for img_fn in images_to_delete:
            img_path = os.path.join(current_app.root_path, 'static/uploads', img_fn)
            if os.path.exists(img_path):
                try:
                    os.remove(img_path)
                    current_app.logger.info(f"Deleted image file: {img_fn}")
                except Exception as e:
                    current_app.logger.error(f"Error deleting image file {img_fn}: {e}")

        # Save newly uploaded images
        newly_uploaded_image_files = []
        if form.images.data:
            newly_uploaded_image_files = save_pictures(form.images.data)
            if not newly_uploaded_image_files:
                flash('Failed to save new images. Please try again.', 'danger')
                return render_template('listings/edit_listing.html', title='Edit Listing', form=form, listing=listing)
        
        # Combine images to keep with newly uploaded images
        listing.image_files = images_to_keep + newly_uploaded_image_files
        # Ensure 'default.jpg' is added if no images are present after all operations
        if not listing.image_files:
            listing.image_files = ['default.jpg']

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
                'image_files': old_listing_data.get('image_files', []), # Capture original image_files for logging
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
            FraudDetectionService.analyze_listing_for_suspicion(listing.id)
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
        # Populate form.images with existing images (if any) for display
        # Note: File input fields cannot be pre-populated for security reasons.
        # You'll need to handle displaying existing images in the template separately.

    return render_template('listings/edit_listing.html', title='Edit Listing', form=form, listing=listing)

@listings_bp.route("/listing/<string:listing_id>/delete", methods=['POST'])
@login_required
def delete_listing(listing_id):
    """
    Allows the user to delete their listings.
    Logs listing deletion activity.
    """
    current_app.logger.info(f"Request method: {request.method}")
    current_app.logger.info(f"Request form: {request.form}")
    current_app.logger.info(f"Request headers: {request.headers}")
    listing = Listing.objects(id=listing_id).first_or_404()
    if listing.user != current_user:
        flash('You do not have permission to delete this listing.', 'danger')
        return redirect(url_for('listings.dashboard'))
    
    try:
        # Use the FraudDetectionService to delete the listing and related data
        FraudDetectionService.delete_listing_and_related_data(listing.id)
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

from app.models.follows import Follow # Import Follow model
from app.models.user_activity import UserActivity # Import UserActivity model

@listings_bp.route("/dashboard")
@login_required
def dashboard():
    """
    Displays the current user's dashboard based on their role.
    Includes activity feed from followed users.
    """
    user_role = current_user.role
    listings = Listing.objects(user=current_user.id).order_by('-date_posted')

    # Fetch followed users' IDs
    followed_users = Follow.objects(follower=current_user.id)
    followed_user_ids = [follow.followed.id for follow in followed_users]

    # Fetch recent activities (e.g., new listings) from followed users
    recent_activities = []
    if followed_user_ids:
        recent_activities = ActivityLog.objects(
            user_id__in=followed_user_ids,
            action_type='listing_created'
        ).order_by('-timestamp').limit(10) # Limit to 10 recent activities

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

        return render_template(
            'parent_dashboard.html', 
            listings=listings, 
            pending_swaps=pending_swaps, 
            accepted_swaps=accepted_swaps,
            recent_activities=recent_activities # Pass activities to template
        )
    elif user_role == 'school':
        return render_template(
            'school_dashboard.html', 
            listings=listings,
            total_donations_value=current_user.total_donations_value,
            recent_activities=recent_activities # Pass activities to template
        )
    elif user_role == 'ngo':
        return render_template(
            'ngo_dashboard.html', 
            listings=listings,
            total_donations_received_count=current_user.total_donations_received_count,
            total_donations_value=current_user.total_donations_value,
            total_families_supported_ytd=current_user.total_families_supported_ytd,
            recent_activities=recent_activities # Pass activities to template
        )
    elif user_role == 'admin':
        # Calculate total order value for admin dashboard
        completed_orders = Order.objects(status='completed')
        total_order_value = sum(order.total_amount for order in completed_orders)

        return render_template(
            'admin/dashboard.html', 
            listings=listings,
            recent_activities=recent_activities, # Pass activities to template
            total_order_value=total_order_value # Pass total order value to template
        )


@listings_bp.route("/user/<string:user_id>")
def user_profile(user_id):
    """
    Displays the public profile of a user, including their listings.
    """
    user = User.objects(id=user_id).first_or_404()
    listings = Listing.objects(user=user.id, is_available=True).order_by('-date_posted')

    # Fetch reviews received by this user
    reviews_received = Review.objects(reviewed_user=user.id).order_by('-date_posted')

    # Fetch past transactions (completed swaps, orders, donations)
    # Swaps where user is either requester or responder and status is 'completed'
    completed_swaps = SwapRequest.objects(
        (Q(requester=user.id) | Q(responder=user.id)),
        status='completed'
    ).order_by('-updated_date')

    # Orders where user is either buyer or seller and status is 'completed'
    completed_orders = Order.objects(
        (Q(buyer=user.id) | Q(seller=user.id)),
        status='completed'
    ).order_by('-date_created') # Assuming date_created for orders

    # Donations where user is either donor or recipient and status is 'completed'
    completed_donations = Donation.objects(
        (Q(donor=user.id) | Q(recipient=user.id)),
        status='completed'
    ).order_by('-date_donated') # Assuming date_donated for donations

    # Calculate Trust Score
    total_reviews = len(reviews_received)
    average_rating = 0
    if total_reviews > 0:
        total_rating = sum([review.rating for review in reviews_received])
        average_rating = total_rating / total_reviews

    total_transactions = len(completed_swaps) + len(completed_orders) + len(completed_donations)

    return render_template('listings/user_profile.html',
                           title=f"{user.username}'s Profile",
                           user=user,
                           listings=listings,
                           reviews_received=reviews_received,
                           completed_swaps=completed_swaps,
                           completed_orders=completed_orders,
                           completed_donations=completed_donations,
                           average_rating=average_rating,
                           total_reviews=total_reviews,
                           total_transactions=total_transactions)

@listings_bp.route("/my_listings")
@login_required
def my_listings():
    """
    Displays all listings created by the current user for management.
    """
    listings = Listing.objects(user=current_user.id).order_by('-date_posted')
    return render_template('listings/my_listings.html', title='My Listings', listings=listings)

@listings_bp.route("/wishlist_placeholder")
@login_required
def wishlist_placeholder():
    """
    Placeholder for the wishlist page. This route will be removed once the
    wishlist blueprint is fully integrated and functioning.
    """
    flash('Please use the new Wishlist page under My Account!', 'info')
    return redirect(url_for('wishlist.wishlist'))