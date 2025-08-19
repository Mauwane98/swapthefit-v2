# app/blueprints/logistics/routes.py
from flask import Blueprint, render_template, url_for, flash, redirect, request, abort
from flask_login import login_required, current_user
from app.models.logistics import Logistics
from app.models.users import User
from app.models.listings import Listing # Needed for context
from app.models.payments import Order # For sales transactions
from app.models.swaps import SwapRequest # For swap transactions
from app.blueprints.logistics.forms import SetupLogisticsForm, UpdateLogisticsStatusForm
from app.extensions import db
from app.blueprints.notifications.routes import add_notification
from datetime import datetime

logistics_bp = Blueprint('logistics', __name__)

@logistics_bp.route("/setup/<string:transaction_type>/<int:transaction_id>", methods=['GET', 'POST'])
@login_required
def setup_logistics(transaction_type, transaction_id):
    """
    Allows the sender (seller for sale, initiator for swap) to set up logistics details.
    """
    form = SetupLogisticsForm()
    transaction = None
    sender_id = None
    receiver_id = None
    listing_title = "item"

    if transaction_type == 'sale':
        transaction = Order.query.get_or_404(transaction_id)
        if current_user.id != transaction.seller_id:
            flash('You are not authorized to set up logistics for this sale.', 'danger')
            return redirect(url_for('payments.view_order', order_id=transaction_id))
        
        sender_id = transaction.seller_id
        receiver_id = transaction.buyer_id
        listing_title = transaction.listing.title if transaction.listing else "item"
        
        # Check if logistics already exist for this transaction
        existing_logistics = Logistics.query.filter_by(transaction_id=transaction_id, transaction_type='sale').first()
        if existing_logistics:
            flash('Logistics for this sale have already been set up. You can view or update them.', 'info')
            return redirect(url_for('logistics.view_logistics', logistics_id=existing_logistics.id))

    elif transaction_type == 'swap':
        transaction = SwapRequest.query.get_or_404(transaction_id)
        # For swaps, both parties are essentially senders/receivers.
        # We'll allow the initiator to set up initial logistics.
        if current_user.id != transaction.initiator_id and current_user.id != transaction.respondent_id:
            flash('You are not authorized to set up logistics for this swap.', 'danger')
            return redirect(url_for('swaps.view_swap_request', swap_id=transaction_id))
        
        # Determine who is the primary sender for initial setup (e.g., initiator of swap)
        sender_id = transaction.initiator_id
        receiver_id = transaction.respondent_id # This might need to be more complex for two-way swaps
        listing_title = f"{transaction.offered_listing.title} for {transaction.requested_listing.title}" if transaction.offered_listing and transaction.requested_listing else "items"

        # Check if logistics already exist for this transaction
        existing_logistics = Logistics.query.filter_by(transaction_id=transaction_id, transaction_type='swap').first()
        if existing_logistics:
            flash('Logistics for this swap have already been set up. You can view or update them.', 'info')
            return redirect(url_for('logistics.view_logistics', logistics_id=existing_logistics.id))

    else:
        flash('Invalid transaction type.', 'danger')
        return redirect(url_for('landing_bp.index'))

    if form.validate_on_submit():
        logistics = Logistics(
            transaction_id=transaction_id,
            transaction_type=transaction_type,
            sender_user_id=sender_id, # The user setting up logistics
            receiver_user_id=receiver_id, # The other party
            shipping_method=form.shipping_method.data,
            courier_name=form.courier_name.data,
            tracking_number=form.tracking_number.data,
            tracking_url=form.tracking_url.data,
            pudo_location_name=form.pudo_location_name.data,
            pudo_address=form.pudo_address.data,
            pudo_code=form.pudo_code.data,
            pickup_address=form.pickup_address.data,
            delivery_address=form.delivery_address.data,
            scheduled_pickup_date=form.scheduled_pickup_date.data,
            scheduled_delivery_date=form.scheduled_delivery_date.data,
            notes=form.notes.data,
            status='pending_pickup' # Initial status
        )
        db.session.add(logistics)
        db.session.commit()

        flash(f'Logistics for {transaction_type} transaction ID {transaction_id} successfully set up!', 'success')

        # Notify the receiver about logistics setup
        add_notification(
            user_id=receiver_id,
            message=f"Logistics have been set up for your {transaction_type} of '{listing_title}' (Transaction ID: {transaction_id}).",
            notification_type='logistics_update',
            payload={'logistics_id': logistics.id, 'transaction_id': transaction_id, 'transaction_type': transaction_type}
        )

        return redirect(url_for('logistics.view_logistics', logistics_id=logistics.id))

    return render_template('logistics/setup_logistics.html', title='Setup Logistics', form=form, 
                           transaction_type=transaction_type, transaction_id=transaction_id, listing_title=listing_title)

@logistics_bp.route("/logistics/<int:logistics_id>")
@login_required
def view_logistics(logistics_id):
    """
    Displays the details of a specific logistics record.
    Accessible by sender, receiver, or admin.
    """
    logistics = Logistics.query.get_or_404(logistics_id)

    # Ensure current user is authorized
    if not (current_user.id == logistics.sender_user_id or
            current_user.id == logistics.receiver_user_id or
            current_user.role == 'admin'):
        flash('You do not have permission to view these logistics details.', 'danger')
        return redirect(url_for('listings.dashboard')) # Redirect to a generic dashboard

    # Get related transaction and listing for context
    related_transaction = None
    related_listing = None
    if logistics.transaction_type == 'sale':
        related_transaction = Order.query.get(logistics.transaction_id)
        related_listing = related_transaction.listing if related_transaction else None
    elif logistics.transaction_type == 'swap':
        related_transaction = SwapRequest.query.get(logistics.transaction_id)
        related_listing = related_transaction.offered_listing if related_transaction else None # Or requested_listing

    update_form = UpdateLogisticsStatusForm()

    return render_template('logistics/view_logistics.html', title='Logistics Details', 
                           logistics=logistics, 
                           related_transaction=related_transaction, 
                           related_listing=related_listing,
                           update_form=update_form)

@logistics_bp.route("/logistics/<int:logistics_id>/update_status", methods=['POST'])
@login_required
def update_logistics_status(logistics_id):
    """
    Allows sender, receiver, or admin to update the status of a logistics record.
    """
    logistics = Logistics.query.get_or_404(logistics_id)

    # Ensure current user is authorized to update status
    # Sender, Receiver, or Admin can update status
    if not (current_user.id == logistics.sender_user_id or
            current_user.id == logistics.receiver_user_id or
            current_user.role == 'admin'):
        flash('You do not have permission to update this logistics status.', 'danger')
        return redirect(url_for('logistics.view_logistics', logistics_id=logistics.id))

    form = UpdateLogisticsStatusForm()
    if form.validate_on_submit():
        old_status = logistics.status
        logistics.status = form.status.data
        logistics.notes = form.notes.data # Update notes with new status notes
        logistics.last_status_update = datetime.utcnow()

        if form.actual_pickup_date.data:
            logistics.actual_pickup_date = form.actual_pickup_date.data
        if form.actual_delivery_date.data:
            logistics.actual_delivery_date = form.actual_delivery_date.data
        
        db.session.commit()
        flash(f'Logistics status updated to "{logistics.status.replace("_", " ").title()}"!', 'success')

        # Notify both sender and receiver about the status update
        message_to_sender = f"Logistics for your {logistics.transaction_type} transaction (ID: {logistics.transaction_id}) updated to '{logistics.status.replace('_', ' ').title()}'."
        add_notification(
            user_id=logistics.sender_user_id,
            message=message_to_sender,
            notification_type='logistics_update',
            payload={'logistics_id': logistics.id, 'new_status': logistics.status}
        )
        
        message_to_receiver = f"Logistics for your {logistics.transaction_type} transaction (ID: {logistics.transaction_id}) updated to '{logistics.status.replace('_', ' ').title()}'."
        add_notification(
            user_id=logistics.receiver_user_id,
            message=message_to_receiver,
            notification_type='logistics_update',
            payload={'logistics_id': logistics.id, 'new_status': logistics.status}
        )

        return redirect(url_for('logistics.view_logistics', logistics_id=logistics.id))
    
    # If validation fails, re-render the detail page with errors
    related_transaction = None
    related_listing = None
    if logistics.transaction_type == 'sale':
        related_transaction = Order.query.get(logistics.transaction_id)
        related_listing = related_transaction.listing if related_transaction else None
    elif logistics.transaction_type == 'swap':
        related_transaction = SwapRequest.query.get(logistics.transaction_id)
        related_listing = related_transaction.offered_listing if related_transaction else None

    return render_template('logistics/view_logistics.html', title='Logistics Details', 
                           logistics=logistics, 
                           related_transaction=related_transaction, 
                           related_listing=related_listing,
                           update_form=form) # Pass form with errors

# --- Admin View for All Logistics (Optional, can be integrated into admin blueprint) ---
@logistics_bp.route("/admin/manage_logistics")
@login_required
def admin_manage_logistics():
    """Admin route to view and manage all logistics records."""
    if current_user.role != 'admin':
        abort(403) # Forbidden
    
    logistics_records = Logistics.query.order_by(Logistics.created_at.desc()).all()
    # Optional: Add filters for status, transaction type, sender/receiver
    
    return render_template('admin/manage_logistics.html', title='Manage Logistics', logistics_records=logistics_records)

