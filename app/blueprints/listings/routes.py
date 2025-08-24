# app/blueprints/listings/routes.py
from flask import Blueprint, render_template, url_for, flash, redirect, request, current_app, session, jsonify
from flask_login import login_required, current_user
from app.models.listings import Listing
from app.models.users import User
from app.models.wishlist import WishlistItem
from app.models.saved_search import SavedSearch
from app.extensions import db, csrf
from app.blueprints.listings.forms import ListingForm, BulkUploadForm # Update this import
from app.blueprints.payments.forms import ProcessPaymentForm
from werkzeug.utils import secure_filename
import os
import secrets
import json
from urllib.parse import parse_qs
from app.models.swaps import SwapRequest # Import SwapRequest model
from app.models.orders import Order # Import Order model
from app.models.donations import Donation # Import Donation model
from app.models.reviews import Review # Import Review model
from mongoengine.errors import NotUniqueError, DoesNotExist, ValidationError
from mongoengine.queryset.visitor import Q # Import Q for complex queries
import csv # Add this import at the top
from PIL import Image # Import Image from Pillow

# Import the add_notification helper function
from app.blueprints.notifications.routes import add_notification
# Import the activity logger
from app.utils.activity_logger import log_activity
from app.utils.security import roles_required # Import roles_required
from app.services.fraud_detection_service import FraudDetectionService
from app.services.paystack import PaystackService # Import PaystackService
from app.services.recommendation_service import RecommendationService # Import RecommendationService

listings_bp = Blueprint('listings', __name__)

def save_pictures(form_pictures):
    """
    Saves uploaded pictures to the static/uploads directory.
    Generates random filenames to prevent collisions.
    Resizes images for optimized web display.
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
                # Open the image using Pillow
                img = Image.open(form_picture)

                # Resize image while maintaining aspect ratio
                output_size = (800, 800) # Max width, max height
                img.thumbnail(output_size, Image.Resampling.LANCZOS) # Use LANCZOS for high-quality downsampling

                # Save the resized image
                img.save(picture_path)
                saved_filenames.append(picture_fn)
            except Exception as e:
                current_app.logger.error(f"Error saving or processing picture {form_picture.filename}: {e}")
                flash('Failed to save or process one or more images. Please try again.', 'danger')
                return [] # Return empty list if any save fails
    return saved_filenames



@listings_bp.route("/listing/new", methods=['GET', 'POST'])
@login_required
def create_listing():
    """
    Handles the creation of new listings using a multi-step form.
    Stores partial data in session.
    """
    current_step = int(request.args.get('step', 1))
    form = ListingForm(current_step=current_step)

    if request.method == 'POST':
        if form.validate_on_submit():
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
                    allowed_extensions = {'png', 'jpg', 'jpeg'}
                    for image in form.images.data:
                        if '.' not in image.filename or image.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
                            flash(f'Invalid file type for {image.filename}. Please upload only JPG, PNG, or JPEG files.', 'danger')
                            return render_template('listings/create_listings.html', title='Create Listing', form=form, current_step=current_step)

                    image_files = save_pictures(form.images.data)
                    if not image_files:
                        flash('Failed to save images. Please try again.', 'danger')
                        return render_template('listings/create_listings.html', title='Create Listing', form=form, current_step=current_step)
                listing_data['image_files'] = image_files if image_files else ['default.jpg']
            elif current_step == 3:
                listing_data['price'] = form.price.data
                listing_data['listing_type'] = form.listing_type.data
                if form.listing_type.data == 'donation':
                    listing_data['donation_recipient_type'] = form.donation_recipient_type.data
                listing_data['brand'] = form.brand.data
                listing_data['color'] = form.color.data
                listing_data['is_premium'] = form.is_premium.data
            
            session['listing_data'] = listing_data

            if current_step < 3:
                return redirect(url_for('listings.create_listing', step=current_step + 1))
            else:
                try:
                    listing = Listing(
                        title=listing_data['title'],
                        description=listing_data['description'],
                        price=listing_data.get('price'),
                        uniform_type=listing_data['uniform_type'],
                        condition=listing_data['condition'],
                        size=listing_data['size'],
                        gender=listing_data['gender'],
                        school_name=listing_data.get('school_name'),
                        location=listing_data['location'],
                        listing_type=listing_data['listing_type'],
                        donation_recipient_type=listing_data.get('donation_recipient_type'),
                        brand=listing_data.get('brand'),
                        color=listing_data.get('color'),
                        image_files=listing_data.get('image_files', ['default.jpg']),
                        is_premium=listing_data.get('is_premium', False),
                        user=current_user
                    )
                    listing.save()
                    FraudDetectionService.analyze_listing_for_suspicion(listing.id)

                    flash('Your listing has been created!', 'success')
                    session.pop('listing_data', None)

                    log_activity(
                        user_id=current_user.id,
                        action_type='listing_created',
                        description=f"Created new listing: '{listing.title}' (ID: {listing.id})",
                        payload={'listing_id': str(listing.id), 'listing_type': listing.listing_type},
                        request_obj=request
                    )

                    all_saved_searches = SavedSearch.objects()
                    for saved_search in all_saved_searches:
                        saved_params = parse_qs(saved_search.search_query_params)
                        match = True
                        if 'search_term' in saved_params and not any(term.lower() in (listing.title.lower() or '') or term.lower() in (listing.description.lower() or '') or term.lower() in (listing.school_name.lower() or '') or term.lower() in (listing.brand.lower() or '') for term in saved_params['search_term']):
                            match = False
                        if 'location' in saved_params and saved_params['location'][0].lower() not in listing.location.lower():
                            match = False
                        if 'uniform_type' in saved_params and saved_params['uniform_type'][0] != 'All' and saved_params['uniform_type'][0] != listing.uniform_type:
                            match = False
                        if 'brand' in saved_params and saved_params['brand'][0] != 'All' and saved_params['brand'][0].lower() not in (listing.brand or '').lower():
                            match = False
                        if 'color' in saved_params and saved_params['color'][0] != 'All' and saved_params['color'][0].lower() not in (listing.color or '').lower():
                            match = False
                        if 'condition' in saved_params and saved_params['condition'][0] != 'All' and saved_params['condition'][0] != listing.condition:
                            match = False
                        if 'listing_type' in saved_params and saved_params['listing_type'][0] != 'All' and saved_params['listing_type'][0] != listing.listing_type:
                            match = False
                        if 'gender' in saved_params and saved_params['gender'][0] != 'All' and saved_params['gender'][0] != listing.gender:
                            match = False
                        if 'size' in saved_params and saved_params['size'][0] != 'All' and saved_params['size'][0] != listing.size:
                            match = False
                        if 'min_price' in saved_params and listing.price is not None and float(saved_params['min_price'][0]) > listing.price:
                            match = False
                        if 'max_price' in saved_params and listing.price is not None and float(saved_params['max_price'][0]) < listing.price:
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
                    flash('A listing with this title already exists. Please choose a different title.', 'danger')
                    current_app.logger.error(f"Listing creation failed due to duplicate title: {e}")
                except Exception as e:
                    flash(f'An unexpected error occurred: {str(e)}', 'danger')
                    current_app.logger.error(f"Listing creation error: {e}")
                    log_activity(
                        user_id=current_user.id,
                        action_type='listing_creation_failed',
                        description=f"Failed to create listing: {listing_data.get('title', 'N/A')}",
                        payload={'error': str(e)},
                        request_obj=request
                    )
        else:
            flash('Please correct the errors below.', 'danger')
            current_app.logger.error(f"Form validation errors: {form.errors}")
            listing_data = session.get('listing_data', {})
            form.process(data=listing_data)
    
    elif request.method == 'GET':
        listing_data = session.get('listing_data', {})
        form.process(data=listing_data)

    return render_template('listings/create_listings.html', title='Create Listing', form=form, current_step=current_step)

@listings_bp.route("/listing/<string:listing_id>/update", methods=['GET', 'POST'])
@login_required
def edit_listing(listing_id):
    listing = Listing.objects(id=listing_id).first_or_404()
    if listing.user != current_user:
        flash('You do not have permission to edit this listing.', 'danger')
        return redirect(url_for('listings.listing_detail', listing_id=listing.id))

    form = ListingForm(obj=listing)
    
    if form.validate_on_submit():
        try:
            old_listing_data = listing.to_dict()
            
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
            if form.listing_type.data == 'donation':
                listing.donation_recipient_type = form.donation_recipient_type.data
            else:
                listing.donation_recipient_type = 'any'
            listing.is_premium = form.is_premium.data
            listing.brand = form.brand.data
            listing.color = form.color.data

            listing.save()
            flash('Your listing has been updated!', 'success')

            updated_fields = {k: v for k, v in listing.to_dict().items() if v != old_listing_data.get(k)}
            log_activity(
                user_id=current_user.id,
                action_type='listing_updated',
                description=f"Updated listing: '{listing.title}' (ID: {listing.id})",
                payload={'listing_id': str(listing.id), 'changes': updated_fields},
                request_obj=request
            )

            return redirect(url_for('listings.listing_detail', listing_id=listing.id))
        except Exception as e:
            flash(f'An unexpected error occurred: {str(e)}', 'danger')
            current_app.logger.error(f"Listing update error: {e}")
    
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
        form.donation_recipient_type.data = listing.donation_recipient_type
        form.is_premium.data = listing.is_premium
        form.brand.data = listing.brand
        form.color.data = listing.color

    return render_template('listings/edit_listing.html', title='Edit Listing', form=form, listing=listing)


@listings_bp.route("/listing/<string:listing_id>/initiate_premium_payment", methods=['POST'])
@login_required
def initiate_premium_payment(listing_id):
    listing = Listing.objects(id=listing_id).first_or_404()

    if listing.user != current_user:
        flash('You do not have permission to make this listing premium.', 'danger')
        return redirect(url_for('listings.listing_detail', listing_id=listing.id))

    if listing.is_premium:
        flash('This listing is already premium.', 'info')
        return redirect(url_for('listings.listing_detail', listing_id=listing.id))

    # Assuming a fixed premium amount for now
    premium_amount = 5000  # Example: 50.00 ZAR (in cents)
    callback_url = url_for('listings.verify_premium_payment', listing_id=listing.id, _external=True)

    try:
        paystack_service = PaystackService()
        payment_data = paystack_service.initialize_payment(
            email=current_user.email,
            amount=premium_amount,
            metadata={'listing_id': str(listing.id), 'payment_type': 'premium_listing'},
            callback_url=callback_url
        )
        if payment_data and payment_data.get('status'):
            return redirect(payment_data['data']['authorization_url'])
        else:
            flash('Failed to initiate payment. Please try again.', 'danger')
            current_app.logger.error(f"Paystack initialization failed: {payment_data.get('message', 'Unknown error')}")
    except Exception as e:
        flash(f'An error occurred while initiating payment: {str(e)}', 'danger')
        current_app.logger.error(f"Error initiating premium payment for listing {listing.id}: {e}")

    return redirect(url_for('listings.listing_detail', listing_id=listing.id))


@listings_bp.route("/listing/<string:listing_id>/verify_premium_payment", methods=['GET'])
@login_required
def verify_premium_payment(listing_id):
    listing = Listing.objects(id=listing_id).first_or_404()

    if listing.user != current_user:
        flash('You do not have permission to verify payment for this listing.', 'danger')
        return redirect(url_for('listings.listing_detail', listing_id=listing.id))

    if listing.is_premium:
        flash('This listing is already premium.', 'info')
        return redirect(url_for('listings.listing_detail', listing_id=listing.id))

    reference = request.args.get('reference')
    if not reference:
        flash('Payment reference not found.', 'danger')
        return redirect(url_for('listings.listing_detail', listing_id=listing.id))

    try:
        paystack_service = PaystackService()
        verification_data = paystack_service.verify_payment(reference)
        if verification_data and verification_data.get('status') and verification_data['data']['status'] == 'success':
            # Check if the payment metadata matches the listing and type
            metadata = verification_data['data'].get('metadata', {})
            if metadata.get('listing_id') == str(listing.id) and metadata.get('payment_type') == 'premium_listing':
                listing.is_premium = True
                listing.save()
                flash('Your listing is now premium!', 'success')
                log_activity(
                    user_id=current_user.id,
                    action_type='premium_listing_activated',
                    description=f"Listing '{listing.title}' (ID: {listing.id}) upgraded to premium.",
                    payload={'listing_id': str(listing.id), 'payment_reference': reference},
                    request_obj=request
                )
            else:
                flash('Payment verification failed: Metadata mismatch.', 'danger')
                current_app.logger.error(f"Premium payment verification metadata mismatch for listing {listing.id}. Expected: {{'listing_id': {listing.id}, 'payment_type': 'premium_listing'}}, Got: {metadata}")
        else:
            flash('Payment verification failed. Please try again.', 'danger')
            current_app.logger.error(f"Paystack verification failed for reference {reference}: {verification_data.get('message', 'Unknown error')}")
    except Exception as e:
        flash(f'An error occurred during payment verification: {str(e)}', 'danger')
        current_app.logger.error(f"Error verifying premium payment for listing {listing.id}: {e}")

    return redirect(url_for('listings.listing_detail', listing_id=listing.id))


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
    titles = [listing.title for listing in Listing.objects(title__icontains=query).limit(5)]
    descriptions = [listing.description for listing in Listing.objects(description__icontains=query).limit(5)]
    school_names = [listing.school_name for listing in Listing.objects(school_name__icontains=query).limit(5) if listing.school_name]
    brands = [listing.brand for listing in Listing.objects(brand__icontains=query).limit(5) if listing.brand]

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
    
    is_owner = False
    # Safely get the user object associated with the listing
    # If the referenced user does not exist, listing.user will be None
    try:
        # Attempt to access an attribute to trigger dereferencing
        # If the user doesn't exist, this will raise DoesNotExist
        _ = listing.user.id 
    except DoesNotExist:
        current_app.logger.warning(f"User referenced by listing {listing.id} does not exist. Setting listing.user to None.")
        listing.user = None # Set the reference to None

    if current_user.is_authenticated and listing.user:
        if listing.user.id == current_user.id:
            is_owner = True
    
    process_payment_form = ProcessPaymentForm() # Instantiate the form
    
    return render_template('listings/listing_detail.html', 
                           title=listing.title, 
                           listing=listing, 
                           in_wishlist=in_wishlist, 
                           is_owner=is_owner,
                           process_payment_form=process_payment_form) # Pass the form to the template



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
    current_app.logger.info(f"Request form: {request.form}") # Add this line for debugging
    # try:
    #     csrf.validate_csrf(request.form.get('csrf_token'))
    # except ValidationError as e:
    #     current_app.logger.error(f"CSRF validation failed: {e}")
    #     flash('Invalid CSRF token.', 'danger')
    #     return redirect(url_for('listings.dashboard')) # Or a more appropriate error page

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
        recent_activities = UserActivity.objects(
            user__in=followed_user_ids,
            action_type='listing_created'
        ).order_by('-timestamp').limit(10) # Limit to 10 recent activities

    # Get personalized recommendations
    recommendation_service = RecommendationService()
    recommended_listings = recommendation_service.get_recommendations(current_user)

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
            recent_activities=recent_activities,
            recommended_listings=recommended_listings # Pass recommendations to template
        )
    elif user_role == 'school':
        return render_template(
            'school_dashboard.html', 
            listings=listings,
            total_donations_value=current_user.total_donations_value,
            recent_activities=recent_activities,
            recommended_listings=recommended_listings # Pass recommendations to template
        )
    elif user_role == 'ngo':
        return render_template(
            'ngo_dashboard.html', 
            listings=listings,
            total_donations_received_count=current_user.total_donations_received_count,
            total_donations_value=current_user.total_donations_value,
            total_families_supported_ytd=current_user.total_families_supported_ytd,
            recent_activities=recent_activities,
            recommended_listings=recommended_listings # Pass recommendations to template
        )
    elif user_role == 'admin':
        # Calculate total order value for admin dashboard
        completed_orders = Order.objects(status='completed')
        total_order_value = sum(order.total_amount for order in completed_orders)

        # Calculate total order value for admin dashboard
        completed_orders = Order.objects(status='completed')
        total_order_value = sum(order.total_amount for order in completed_orders)

        # Calculate total donation value for admin dashboard
        completed_donations = Donation.objects(status='completed')
        total_donation_value = sum(donation.amount for donation in completed_donations)

        return render_template(
            'admin/dashboard.html', 
            listings=listings,
            recent_activities=recent_activities,
            total_order_value=total_order_value,
            total_donation_value=total_donation_value,
            recommended_listings=recommended_listings # Pass recommendations to template
        )


@listings_bp.route("/user/<string:user_id>")
def user_profile(user_id):
    """
    Displays the public profile of a user, including their listings.
    """
    user = User.objects(id=user_id).first_or_404()
    listings = Listing.objects(user=user.id, is_available=True).order_by('-date_posted')

    # Fetch reviews received by this user
    reviews_received_query = Review.objects(reviewed_user=user.id).order_by('-date_posted')
    reviews_received = []
    for review in reviews_received_query:
        try:
            # This will trigger the dereference and raise DoesNotExist if the reviewer is gone
            if review.reviewer:
                reviews_received.append(review)
        except DoesNotExist:
            # Log the dangling reference
            current_app.logger.warning(f"Review {review.id} has a dangling reference to a deleted reviewer.")
            continue

    # Fetch past transactions (completed swaps, orders, donations)
    # Swaps where user is either requester or responder and status is 'completed'
    completed_swaps_query = SwapRequest.objects(
        (Q(requester=user.id) | Q(responder=user.id)),
        status='completed'
    ).order_by('-updated_date')

    completed_swaps = []
    for swap in completed_swaps_query:
        try:
            # Trigger dereferencing
            _ = swap.requester.username
            _ = swap.responder.username
            if swap.requester_listing:
                _ = swap.requester_listing.title
            if swap.responder_listing:
                _ = swap.responder_listing.title
            completed_swaps.append(swap)
        except DoesNotExist:
            current_app.logger.warning(f"SwapRequest {swap.id} has a dangling reference to a deleted user or listing.")
            continue

    # Orders where user is either buyer or seller and status is 'completed'
    completed_orders_query = Order.objects(
        (Q(buyer=user.id) | Q(seller=user.id)),
        status='completed'
    ).order_by('-date_created') # Assuming date_created for orders

    completed_orders = []
    for order in completed_orders_query:
        try:
            # Trigger dereferencing
            _ = order.buyer.username
            _ = order.seller.username
            if order.listing:
                _ = order.listing.title
            completed_orders.append(order)
        except DoesNotExist:
            current_app.logger.warning(f"Order {order.id} has a dangling reference to a deleted user or listing.")
            continue

    # Donations where user is either donor or recipient and status is 'completed'
    completed_donations_query = Donation.objects(
        (Q(donor=user.id) | Q(recipient=user.id)),
        status='completed'
    ).order_by('-date_donated') # Assuming date_donated for donations

    completed_donations = []
    for donation in completed_donations_query:
        try:
            # Trigger dereferencing
            _ = donation.donor.username
            _ = donation.recipient.username
            if donation.listing:
                _ = donation.listing.title
            completed_donations.append(donation)
        except DoesNotExist:
            current_app.logger.warning(f"Donation {donation.id} has a dangling reference to a deleted user or listing.")
            continue

    # Calculate Trust Score
    total_reviews = len(reviews_received)
    average_rating = 0
    if total_reviews > 0:
        total_rating = sum([review.rating for review in reviews_received])
        average_rating = total_rating / total_reviews

    total_transactions = len(completed_swaps) + len(completed_orders) + len(completed_donations)

    is_following = False
    if current_user.is_authenticated and current_user.id != user.id:
        # Check if current_user is following the displayed user
        is_following = Follow.objects(follower=current_user.id, followed=user.id).first() is not None

    from app.services.badge_service import badge_service
    user_badges = badge_service.get_user_badges(user)

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
                           total_transactions=total_transactions,
                           is_following=is_following,
                           user_badges=user_badges)

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