from flask import Blueprint, render_template, redirect, url_for, flash, abort, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson.objectid import ObjectId
import os
from werkzeug.utils import secure_filename

# Define the blueprint object first to avoid circular imports
listings_bp = Blueprint('listings_bp', __name__,
                        template_folder='templates',
                        static_folder='static')

# Now, import the other dependencies that might rely on the app context
from app.extensions import mongo
from app.blueprints.listings.forms import ListingForm, EditListingForm
from app.models.listings import Listing

@listings_bp.route('/marketplace')
def marketplace():
    """Public page to browse all available listings."""
    all_listings = Listing.find_all_available()
    return render_template('listings/marketplace.html', listings=all_listings)

@listings_bp.route('/listing/<listing_id>')
def listing_detail(listing_id):
    """Shows the details for a single listing."""
    listing = Listing.find_by_id(listing_id)
    if not listing:
        flash('Listing not found.', 'danger')
        return redirect(url_for('listings_bp.marketplace'))
    
    owner = mongo.db.users.find_one(
        {'_id': listing['owner_id']},
        {'name': 1, 'email': 1}
    )
    
    return render_template('listings/listing_detail.html', listing=listing, owner=owner)

@listings_bp.route('/dashboard')
@jwt_required()
def dashboard():
    current_user_id = get_jwt_identity()
    user = mongo.db.users.find_one({'_id': ObjectId(current_user_id)})
    user_listings = Listing.find_by_owner(current_user_id)
    return render_template('listings/dashboard.html', user=user, listings=user_listings)

@listings_bp.route('/listings/new', methods=['GET', 'POST'])
@jwt_required()
def create_listing():
    form = ListingForm()
    if form.validate_on_submit():
        current_user_id = get_jwt_identity()
        
        f = form.photos.data
        filename = secure_filename(f.filename)
        upload_path = os.path.join(current_app.root_path, 'static/uploads', filename)
        f.save(upload_path)

        Listing.create(
            owner_id=current_user_id,
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            school=form.school.data,
            size=form.size.data,
            condition=form.condition.data,
            images=[filename]
        )
        
        flash('Your listing has been created!', 'success')
        return redirect(url_for('listings_bp.dashboard'))
        
    return render_template('listings/create_listing.html', title='New Listing', form=form)

@listings_bp.route('/listing/<listing_id>/edit', methods=['GET', 'POST'])
@jwt_required()
def edit_listing(listing_id):
    listing = Listing.find_by_id(listing_id)
    current_user_id = get_jwt_identity()

    if not listing or str(listing['owner_id']) != current_user_id:
        abort(403)

    form = EditListingForm(data=listing)
    if form.validate_on_submit():
        update_data = {
            'title': form.title.data,
            'description': form.description.data,
            'category': form.category.data,
            'school': form.school.data,
            'size': form.size.data,
            'condition': form.condition.data
        }
        if form.photos.data:
            f = form.photos.data
            filename = secure_filename(f.filename)
            upload_path = os.path.join(current_app.root_path, 'static/uploads', filename)
            f.save(upload_path)
            update_data['images'] = [filename]

        Listing.update(listing_id, update_data)
        flash('Your listing has been updated!', 'success')
        return redirect(url_for('listings_bp.dashboard'))
    
    return render_template('listings/edit_listing.html', form=form, listing=listing)

@listings_bp.route('/listing/<listing_id>/delete', methods=['POST'])
@jwt_required()
def delete_listing(listing_id):
    listing = Listing.find_by_id(listing_id)
    current_user_id = get_jwt_identity()

    if not listing or str(listing['owner_id']) != current_user_id:
        abort(403)

    Listing.delete_by_id(listing_id)
    flash('Your listing has been deleted.', 'success')
    return redirect(url_for('listings_bp.dashboard'))
