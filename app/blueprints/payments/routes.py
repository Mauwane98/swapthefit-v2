from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user
from app.models.listings import Listing
from app.models.users import User
from app.models.payments import Order # Import the new Order model
from app.models.notifications import Notification # For sending notifications
from app.blueprints.payments.forms import ProcessPaymentForm # Import the payment form
from app.utils.security import roles_required
from datetime import datetime
import os

payments_bp = Blueprint('payments', __name__)

@payments_bp.route('/buy/<string:listing_id>', methods=['GET', 'POST'])
@login_required
@roles_required('parent') # Only parents can buy items
def buy_item(listing_id):
    """
    Initiates the purchase process for a listing.
    This route will typically redirect to a payment gateway or display a payment form.
    """
    listing = Listing.objects(id=listing_id).first()
    if not listing:
        abort(404)

    # Prevent buying your own listing
    if listing.owner.id == current_user.id:
        flash('You cannot buy your own listing.', 'danger')
        return redirect(url_for('listings.listing_detail', listing_id=listing_id))

    # Ensure the listing is for sale and available
    if listing.listing_type != 'sale' or listing.status != 'available' or listing.price is None:
        flash('This item is not available for purchase or is not listed for sale.', 'danger')
        return redirect(url_for('listings.listing_detail', listing_id=listing_id))
    
    # Check if there's already a pending order for this user and listing
    existing_order = Order.objects(
        buyer=current_user.id,
        purchased_listing=listing.id,
        status__in=['pending_payment', 'paid', 'pending_pickup'] # Exclude cancelled/completed
    ).first()

    if existing_order:
        flash(f'You already have an active order for this item (Status: {existing_order.status.replace("_", " ").capitalize()}).', 'info')
        return redirect(url_for('payments.view_order', order_id=existing_order.id))

    # Create a new order with 'pending_payment' status
    order = Order(
        buyer=current_user.id,
        purchased_listing=listing.id,
        seller=listing.owner.id,
        price_at_purchase=listing.price,
        status='pending_payment'
    )
    order.save()

    # Update listing status to indicate it's under pending payment
    listing.status = 'pending_payment'
    listing.save()

    flash(f'Order created for R{listing.price:.2f}. Please complete the payment.', 'info')
    
    # Redirect to a mock payment page or an actual payment gateway integration
    return redirect(url_for('payments.process_payment', order_id=order.id))


@payments_bp.route('/process_payment/<string:order_id>', methods=['GET', 'POST'])
@login_required
@roles_required('parent') # Only the buyer can process the payment for their order
def process_payment(order_id):
    """
    Simulates a payment processing page. In a real scenario, this would be an integration
    with a payment gateway like PayFast or PayPal.
    """
    order = Order.objects(id=order_id).first()
    if not order:
        abort(404)

    if order.buyer.id != current_user.id:
        flash('You do not have permission to process this payment.', 'danger')
        return redirect(url_for('payments.manage_orders'))

    if order.status != 'pending_payment':
        flash(f'This order is already {order.status.replace("_", " ")}.', 'info')
        return redirect(url_for('payments.view_order', order_id=order.id))

    form = ProcessPaymentForm()
    if form.validate_on_submit():
        # Simulate successful payment
        order.status = 'paid'
        order.transaction_id = form.transaction_id.data if form.transaction_id.data else f"MOCK_TXN_{order.id}"
        order.updated_date = datetime.utcnow()
        order.save()

        # Update listing status to 'paid' (or 'pending_pickup' if logistics starts immediately)
        order.purchased_listing.status = 'paid'
        order.purchased_listing.save()

        # Notify the seller that their item has been bought and paid for
        notification_message = f"Your item '{order.purchased_listing.title}' has been bought by {current_user.username} for R{order.price_at_purchase:.2f}! Payment received."
        notification = Notification(
            recipient=order.seller.id,
            sender=current_user.id,
            message=notification_message,
            link=url_for('payments.view_order', order_id=order.id),
            notification_type='payment_received'
        )
        notification.save()
        current_app.extensions['socketio'].emit(
            'new_notification',
            {'message': notification.message, 'count': Notification.objects(recipient=order.seller.id, read=False).count()},
            room=str(order.seller.id)
        )

        flash('Payment confirmed successfully! Seller has been notified.', 'success')
        return redirect(url_for('payments.view_order', order_id=order.id))

    return render_template('payments/process_payment.html', form=form, order=order)


@payments_bp.route('/manage', methods=['GET'])
@login_required
def manage_orders():
    """
    Displays all orders related to the current user (as buyer or seller).
    """
    # Orders where current user is the buyer
    bought_items = Order.objects(buyer=current_user.id).order_by('-order_date')
    
    # Orders where current user is the seller
    sold_items = Order.objects(seller=current_user.id).order_by('-order_date')
    
    return render_template(
        'payments/manage_orders.html', 
        bought_items=bought_items, 
        sold_items=sold_items
    )

@payments_bp.route('/view_order/<string:order_id>')
@login_required
def view_order(order_id):
    """
    Displays the details of a specific order.
    Only accessible by buyer or seller.
    """
    order = Order.objects(id=order_id).first()
    if not order:
        abort(404)

    # Ensure only buyer or seller can view the order
    if current_user.id != order.buyer.id and current_user.id != order.seller.id:
        flash('You do not have permission to view this order.', 'danger')
        return redirect(url_for('payments.manage_orders'))
    
    return render_template('payments/view_order.html', order=order)


@payments_bp.route('/mark_picked_up/<string:order_id>', methods=['POST'])
@login_required
@roles_required('parent', 'school', 'ngo') # Both buyer and seller can mark as picked up/shipped
def mark_picked_up(order_id):
    """
    Allows the seller or buyer to mark an order as picked up/ready for delivery.
    This implies the item is no longer with the seller.
    """
    order = Order.objects(id=order_id).first()
    if not order:
        flash('Order not found.', 'danger')
        return redirect(url_for('payments.manage_orders'))

    # Only the seller or buyer can mark as picked up, and only if paid
    if (current_user.id != order.seller.id and current_user.id != order.buyer.id) or order.status != 'paid':
        flash('You do not have permission to update this order status or it is not in the correct state.', 'danger')
        return redirect(url_for('payments.view_order', order_id=order.id))

    order.status = 'pending_pickup'
    order.updated_date = datetime.utcnow()
    order.save()

    # Listing status should already be 'paid' or similar, keep it.
    
    # Notify both parties
    recipient_user = order.buyer if current_user.id == order.seller.id else order.seller
    notification_message = f"Order for '{order.purchased_listing.title}' has been marked as 'Ready for Pickup/Shipped' by {current_user.username}."
    notification = Notification(
        recipient=recipient_user.id,
        sender=current_user.id,
        message=notification_message,
        link=url_for('payments.view_order', order_id=order.id),
        notification_type='order_status_update'
    )
    notification.save()
    current_app.extensions['socketio'].emit(
        'new_notification',
        {'message': notification.message, 'count': Notification.objects(recipient=recipient_user.id, read=False).count()},
        room=str(recipient_user.id)
    )

    flash('Order status updated to "Ready for Pickup/Shipped".', 'success')
    return redirect(url_for('payments.view_order', order_id=order.id))


@payments_bp.route('/complete_order/<string:order_id>', methods=['POST'])
@login_required
@roles_required('parent', 'school', 'ngo') # Both buyer and seller can confirm completion
def complete_order(order_id):
    """
    Marks an order as completed. This typically means the item has been successfully
    delivered to the buyer.
    """
    order = Order.objects(id=order_id).first()
    if not order:
        flash('Order not found.', 'danger')
        return redirect(url_for('payments.manage_orders'))

    # Only the buyer or seller can complete, and only if pending pickup
    if (current_user.id != order.buyer.id and current_user.id != order.seller.id) or order.status != 'pending_pickup':
        flash('You do not have permission to complete this order or it is not in the correct state.', 'danger')
        return redirect(url_for('payments.view_order', order_id=order.id))

    order.status = 'completed'
    order.updated_date = datetime.utcnow()
    order.save()

    # Mark the listing as inactive and 'sold'
    order.purchased_listing.status = 'sold'
    order.purchased_listing.is_active = False
    order.purchased_listing.save()

    # Notify both parties
    recipient_user = order.buyer if current_user.id == order.seller.id else order.seller
    notification_message = f"Order for '{order.purchased_listing.title}' has been successfully COMPLETED!"
    notification = Notification(
        recipient=recipient_user.id,
        sender=current_user.id,
        message=notification_message,
        link=url_for('payments.view_order', order_id=order.id),
        notification_type='order_status_update'
    )
    notification.save()
    current_app.extensions['socketio'].emit(
        'new_notification',
        {'message': notification.message, 'count': Notification.objects(recipient=recipient_user.id, read=False).count()},
        room=str(recipient_user.id)
    )

    flash('Order marked as completed!', 'success')
    return redirect(url_for('payments.manage_orders'))

@payments_bp.route('/cancel_order/<string:order_id>', methods=['POST'])
@login_required
@roles_required('parent', 'school', 'ngo') # Buyer or seller can cancel if not yet completed
def cancel_order(order_id):
    """
    Allows a buyer or seller to cancel an order if it has not been completed.
    """
    order = Order.objects(id=order_id).first()
    if not order:
        flash('Order not found.', 'danger')
        return redirect(url_for('payments.manage_orders'))

    # Only buyer or seller can cancel, and only if not completed or already cancelled
    if (current_user.id != order.buyer.id and current_user.id != order.seller.id) or order.status == 'completed' or order.status == 'cancelled':
        flash('You do not have permission to cancel this order or it cannot be cancelled at this stage.', 'danger')
        return redirect(url_for('payments.view_order', order_id=order.id))

    order.status = 'cancelled'
    order.updated_date = datetime.utcnow()
    order.save()

    # Return the listing to 'available' status if it was 'pending_payment' or 'paid'
    if order.purchased_listing.status in ['pending_payment', 'paid']:
        order.purchased_listing.status = 'available'
        order.purchased_listing.save()

    # Notify the other party
    recipient_user = order.buyer if current_user.id == order.seller.id else order.seller
    notification_message = f"The order for '{order.purchased_listing.title}' has been CANCELLED by {current_user.username}."
    notification = Notification(
        recipient=recipient_user.id,
        sender=current_user.id,
        message=notification_message,
        link=url_for('payments.view_order', order_id=order.id),
        notification_type='order_status_update'
    )
    notification.save()
    current_app.extensions['socketio'].emit(
        'new_notification',
        {'message': notification.message, 'count': Notification.objects(recipient=recipient_user.id, read=False).count()},
        room=str(recipient_user.id)
    )

    flash('Order cancelled successfully.', 'info')
    return redirect(url_for('payments.manage_orders'))
