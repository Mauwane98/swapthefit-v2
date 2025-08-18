from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user
from app.models.swaps import SwapRequest
from app.models.donations import Donation
from app.models.payments import Order
from app.models.notifications import Notification
from app.blueprints.logistics.forms import SetLogisticsDetailsForm, UpdateLogisticsStatusForm
from app.utils.security import roles_required
from datetime import datetime
from mongoengine.queryset.visitor import Q

logistics_bp = Blueprint('logistics', __name__)

@logistics_bp.route('/setup/<string:transaction_type>/<string:transaction_id>', methods=['GET', 'POST'])
@login_required
@roles_required('parent', 'school', 'ngo') # Sellers/Donors set up logistics
def setup_logistics(transaction_type, transaction_id):
    """
    Allows a user (seller/donor) to set up logistics details for a transaction.
    transaction_type can be 'order', 'swap', or 'donation'.
    """
    transaction = None
    if transaction_type == 'order':
        transaction = Order.objects(id=transaction_id).first()
    elif transaction_type == 'swap':
        transaction = SwapRequest.objects(id=transaction_id).first()
    elif transaction_type == 'donation':
        transaction = Donation.objects(id=transaction_id).first()
    
    if not transaction:
        abort(404)

    # Ensure current user is the seller/donor for this transaction
    is_owner = False
    if transaction_type == 'order' and transaction.seller.id == current_user.id:
        is_owner = True
    elif transaction_type == 'swap' and (transaction.requester.id == current_user.id or transaction.responder.id == current_user.id):
        # For swaps, both parties might need to set up logistics for their outgoing item
        # For simplicity, let's assume the 'owner' of the listing being sent is responsible for setup.
        # This logic might need refinement based on exact swap flow (e.g., who sends first).
        # For now, if current_user is either party, they can set up logistics for their side.
        is_owner = True
    elif transaction_type == 'donation' and transaction.donor.id == current_user.id:
        is_owner = True

    if not is_owner and not current_user.has_role('admin'):
        flash('You do not have permission to set up logistics for this transaction.', 'danger')
        if transaction_type == 'order':
            return redirect(url_for('payments.view_order', order_id=transaction_id))
        elif transaction_type == 'swap':
            return redirect(url_for('swaps.view_swap_request', swap_request_id=transaction_id))
        elif transaction_type == 'donation':
            return redirect(url_for('donations.view_donation_request', donation_id=transaction_id))

    # Prevent setting up logistics if already delivered or cancelled
    if transaction.logistics_status in ['delivered', 'failed']:
        flash('Logistics for this transaction are already completed or failed.', 'info')
        if transaction_type == 'order':
            return redirect(url_for('payments.view_order', order_id=transaction_id))
        elif transaction_type == 'swap':
            return redirect(url_for('swaps.view_swap_request', swap_request_id=transaction_id))
        elif transaction_type == 'donation':
            return redirect(url_for('donations.view_donation_request', donation_id=transaction_id))

    form = SetLogisticsDetailsForm()
    if form.validate_on_submit():
        transaction.delivery_method = form.delivery_method.data
        transaction.pickup_location_details = form.pickup_location_details.data
        transaction.delivery_address_details = form.delivery_address_details.data
        
        # PUDO specific fields
        if form.delivery_method.data == 'pudo_locker':
            transaction.pickup_location_details = form.pudo_locker_id.data # Store PUDO ID here
            transaction.logistics_provider = form.logistics_provider.data if form.logistics_provider.data else 'PUDO'
        # Courier specific fields
        elif form.delivery_method.data == 'courier_delivery':
            transaction.logistics_provider = form.logistics_provider.data
        
        transaction.logistics_status = 'awaiting_pickup' # Set initial logistics status
        transaction.updated_date = datetime.utcnow()
        transaction.save()

        # Notify the other party about logistics setup
        recipient_user = None
        if transaction_type == 'order':
            recipient_user = transaction.buyer
        elif transaction_type == 'swap':
            recipient_user = transaction.requester if current_user.id == transaction.responder.id else transaction.responder
        elif transaction_type == 'donation':
            recipient_user = transaction.recipient
        
        if recipient_user:
            notification_message = f"Logistics for your transaction involving '{transaction.purchased_listing.title if transaction_type == 'order' else transaction.donated_listing.title if transaction_type == 'donation' else transaction.responder_listing.title}' have been set up by {current_user.username}. Delivery method: {transaction.delivery_method.replace('_', ' ').capitalize()}."
            notification = Notification(
                recipient=recipient_user.id,
                sender=current_user.id,
                message=notification_message,
                link=url_for('logistics.view_logistics', transaction_type=transaction_type, transaction_id=transaction.id),
                notification_type='logistics_update'
            )
            notification.save()
            current_app.extensions['socketio'].emit(
                'new_notification',
                {'message': notification.message, 'count': Notification.objects(recipient=recipient_user.id, read=False).count()},
                room=str(recipient_user.id)
            )

        flash('Logistics details saved successfully!', 'success')
        if transaction_type == 'order':
            return redirect(url_for('payments.view_order', order_id=transaction_id))
        elif transaction_type == 'swap':
            return redirect(url_for('swaps.view_swap_request', swap_request_id=transaction_id))
        elif transaction_type == 'donation':
            return redirect(url_for('donations.view_donation_request', donation_id=transaction_id))
    
    elif request.method == 'GET':
        # Pre-populate form if logistics details already exist
        form.delivery_method.data = transaction.delivery_method
        form.pickup_location_details.data = transaction.pickup_location_details
        form.delivery_address_details.data = transaction.delivery_address_details
        if transaction.delivery_method == 'pudo_locker':
            form.pudo_locker_id.data = transaction.pickup_location_details # PUDO ID is stored here
        form.logistics_provider.data = transaction.logistics_provider

    return render_template('logistics/setup_logistics.html', form=form, transaction=transaction, transaction_type=transaction_type)


@logistics_bp.route('/view/<string:transaction_type>/<string:transaction_id>')
@login_required
def view_logistics(transaction_type, transaction_id):
    """
    Displays logistics details for a specific transaction.
    Accessible by all parties involved in the transaction.
    """
    transaction = None
    if transaction_type == 'order':
        transaction = Order.objects(id=transaction_id).first()
    elif transaction_type == 'swap':
        transaction = SwapRequest.objects(id=transaction_id).first()
    elif transaction_type == 'donation':
        transaction = Donation.objects(id=transaction_id).first()
    
    if not transaction:
        abort(404)

    # Ensure current user is involved in the transaction
    is_involved = False
    if transaction_type == 'order' and (transaction.buyer.id == current_user.id or transaction.seller.id == current_user.id):
        is_involved = True
    elif transaction_type == 'swap' and (transaction.requester.id == current_user.id or transaction.responder.id == current_user.id):
        is_involved = True
    elif transaction_type == 'donation' and (transaction.donor.id == current_user.id or transaction.recipient.id == current_user.id):
        is_involved = True

    if not is_involved and not current_user.has_role('admin'):
        flash('You do not have permission to view logistics for this transaction.', 'danger')
        if transaction_type == 'order':
            return redirect(url_for('payments.manage_orders'))
        elif transaction_type == 'swap':
            return redirect(url_for('swaps.manage_swaps'))
        elif transaction_type == 'donation':
            return redirect(url_for('donations.manage_donations'))
    
    update_form = UpdateLogisticsStatusForm()

    return render_template('logistics/view_logistics.html', 
                           transaction=transaction, 
                           transaction_type=transaction_type,
                           update_form=update_form)


@logistics_bp.route('/update_status/<string:transaction_type>/<string:transaction_id>', methods=['POST'])
@login_required
@roles_required('parent', 'school', 'ngo') # Both parties can update status
def update_logistics_status(transaction_type, transaction_id):
    """
    Allows a user to update the logistics status of a transaction.
    This route handles marking as 'shipped/ready for pickup' or 'delivered'.
    """
    transaction = None
    if transaction_type == 'order':
        transaction = Order.objects(id=transaction_id).first()
    elif transaction_type == 'swap':
        transaction = SwapRequest.objects(id=transaction_id).first()
    elif transaction_type == 'donation':
        transaction = Donation.objects(id=transaction_id).first()
    
    if not transaction:
        flash('Transaction not found.', 'danger')
        if transaction_type == 'order':
            return redirect(url_for('payments.manage_orders'))
        elif transaction_type == 'swap':
            return redirect(url_for('swaps.manage_swaps'))
        elif transaction_type == 'donation':
            return redirect(url_for('donations.manage_donations'))

    # Ensure current user is involved in the transaction
    is_involved = False
    if transaction_type == 'order' and (transaction.buyer.id == current_user.id or transaction.seller.id == current_user.id):
        is_involved = True
    elif transaction_type == 'swap' and (transaction.requester.id == current_user.id or transaction.responder.id == current_user.id):
        is_involved = True
    elif transaction_type == 'donation' and (transaction.donor.id == current_user.id or transaction.recipient.id == current_user.id):
        is_involved = True

    if not is_involved and not current_user.has_role('admin'):
        flash('You do not have permission to update logistics for this transaction.', 'danger')
        if transaction_type == 'order':
            return redirect(url_for('payments.manage_orders'))
        elif transaction_type == 'swap':
            return redirect(url_for('swaps.manage_swaps'))
        elif transaction_type == 'donation':
            return redirect(url_for('donations.manage_donations'))

    form = UpdateLogisticsStatusForm()
    if form.validate_on_submit():
        new_logistics_status = None
        notification_msg = ""
        
        if 'submit_shipped' in request.form:
            # Only allow 'shipped' if current status is 'awaiting_pickup' or 'awaiting_setup'
            if transaction.logistics_status in ['awaiting_setup', 'awaiting_pickup']:
                new_logistics_status = 'in_transit' if transaction.delivery_method == 'courier_delivery' else 'ready_for_collection'
                transaction.tracking_number = form.tracking_number.data if form.tracking_number.data else transaction.tracking_number
                notification_msg = f"Your item '{transaction.purchased_listing.title if transaction_type == 'order' else transaction.donated_listing.title if transaction_type == 'donation' else transaction.responder_listing.title}' is now {new_logistics_status.replace('_', ' ')}."
            else:
                flash(f"Cannot mark as shipped/ready. Current logistics status is '{transaction.logistics_status.replace('_', ' ')}'.", 'warning')

        elif 'submit_received' in request.form:
            # Only allow 'received' if current status is 'in_transit' or 'ready_for_collection'
            if transaction.logistics_status in ['in_transit', 'ready_for_collection']:
                new_logistics_status = 'delivered'
                notification_msg = f"Your item '{transaction.purchased_listing.title if transaction_type == 'order' else transaction.donated_listing.title if transaction_type == 'donation' else transaction.responder_listing.title}' has been successfully delivered!"
            else:
                flash(f"Cannot confirm receipt. Current logistics status is '{transaction.logistics_status.replace('_', ' ')}'.", 'warning')
        
        elif 'submit_cancel_logistics' in request.form:
            # Allow cancellation if not yet delivered/failed
            if transaction.logistics_status not in ['delivered', 'failed']:
                new_logistics_status = 'failed' # Using 'failed' to denote cancelled logistics
                notification_msg = f"Logistics for your transaction involving '{transaction.purchased_listing.title if transaction_type == 'order' else transaction.donated_listing.title if transaction_type == 'donation' else transaction.responder_listing.title}' have been cancelled."
                # Optionally revert listing status if logistics are cancelled at an early stage
                if transaction_type == 'order' and transaction.status in ['paid', 'pending_payment']:
                    transaction.purchased_listing.status = 'available'
                    transaction.purchased_listing.save()
                elif transaction_type == 'swap' and transaction.status in ['accepted', 'pending']:
                    transaction.requester_listing.status = 'available'
                    transaction.requester_listing.save()
                    transaction.responder_listing.status = 'available'
                    transaction.responder_listing.save()
                elif transaction_type == 'donation' and transaction.status == 'pending_pickup':
                    transaction.donated_listing.status = 'available'
                    transaction.donated_listing.save()
            else:
                flash(f"Cannot cancel logistics. Current logistics status is '{transaction.logistics_status.replace('_', ' ')}'.", 'warning')


        if new_logistics_status:
            transaction.logistics_status = new_logistics_status
            transaction.updated_date = datetime.utcnow()
            transaction.save()

            # Trigger main transaction status update if logistics are completed
            if new_logistics_status == 'delivered':
                if transaction_type == 'order':
                    transaction.status = 'completed'
                    transaction.purchased_listing.is_active = False # Mark listing as inactive
                    transaction.purchased_listing.save()
                elif transaction_type == 'swap':
                    transaction.status = 'completed'
                    transaction.requester_listing.is_active = False
                    transaction.requester_listing.save()
                    transaction.responder_listing.is_active = False
                    transaction.responder_listing.save()
                elif transaction_type == 'donation':
                    # Donation status is 'distributed' in the donation blueprint, not 'completed' here
                    # This might need adjustment based on how 'distributed' maps to 'delivered'
                    pass # Handled by mark_distributed in donations_bp

            # Notify the other party
            recipient_user = None
            if transaction_type == 'order':
                recipient_user = transaction.buyer if current_user.id == transaction.seller.id else transaction.seller
            elif transaction_type == 'swap':
                recipient_user = transaction.requester if current_user.id == transaction.responder.id else transaction.responder
            elif transaction_type == 'donation':
                recipient_user = transaction.donor if current_user.id == transaction.recipient.id else transaction.recipient
            
            if recipient_user:
                notification = Notification(
                    recipient=recipient_user.id,
                    sender=current_user.id,
                    message=notification_msg,
                    link=url_for('logistics.view_logistics', transaction_type=transaction_type, transaction_id=transaction.id),
                    notification_type='logistics_update'
                )
                notification.save()
                current_app.extensions['socketio'].emit(
                    'new_notification',
                    {'message': notification.message, 'count': Notification.objects(recipient=recipient_user.id, read=False).count()},
                    room=str(recipient_user.id)
                )
            flash('Logistics status updated successfully!', 'success')
        else:
            flash('Failed to update logistics status. Please check the current status.', 'danger')

    return redirect(url_for('logistics.view_logistics', transaction_type=transaction_type, transaction_id=transaction.id))

