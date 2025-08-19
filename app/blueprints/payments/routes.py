# app/blueprints/payments/routes.py
from flask import Blueprint, render_template, url_for, flash, redirect, request, abort, current_app
from flask_login import login_required, current_user
from app.models.payments import Order
from app.models.listings import Listing
from app.models.users import User
from app.models.notifications import Notification
from app.blueprints.payments.forms import ProcessPaymentForm, PremiumListingPurchaseForm
from app.extensions import db
from app.blueprints.notifications.routes import add_notification
from datetime import datetime, timedelta
import secrets # For simulating transaction IDs

payments_bp = Blueprint('payments', __name__)

# Define platform fee rate (e.g., 5% of the sale price)
PLATFORM_FEE_RATE = 0.05

# Define premium package pricing and duration
PREMIUM_PACKAGES = {
    '7_days_50': {'duration_days': 7, 'cost': 50.00},
    '14_days_90': {'duration_days': 14, 'cost': 90.00},
    '30_days_150': {'duration_days': 30, 'cost': 150.00}
}

@payments_bp.route("/process_payment/<string:listing_id>", methods=['GET', 'POST'])
@login_required
def process_payment(listing_id):
    """
    Handles the payment process for a specific listing (sale).
    """
    listing = Listing.objects(id=listing_id).first_or_404()

    # Ensure listing is for sale and available
    if listing.listing_type != 'sale' or not listing.is_available:
        flash('This listing is not available for sale.', 'danger')
        return redirect(url_for('listings.listing_detail', listing_id=listing.id))
    
    # Prevent buying own listing
    if listing.user_id == current_user.id:
        flash('You cannot purchase your own listing.', 'danger')
        return redirect(url_for('listings.listing_detail', listing_id=listing.id))

    form = ProcessPaymentForm()
    if form.validate_on_submit():
        # --- Simulate Payment Gateway Interaction ---
        # In a real application, this would involve API calls to PayFast, PayPal, etc.
        # For now, we'll simulate success.
        payment_successful = True # Assume payment is successful for simulation
        gateway_transaction_id = secrets.token_urlsafe(16) # Simulate a unique transaction ID

        if payment_successful:
            # Calculate fees
            platform_fee = listing.price * PLATFORM_FEE_RATE
            seller_payout = listing.price - platform_fee
            amount_paid_total = listing.price # For simple sales, total paid is listing price

            # Create Order record
            order = Order(
                buyer_id=current_user.id,
                seller_id=listing.user_id,
                listing_id=listing.id,
                price_at_purchase=listing.price,
                status='completed', # Mark as completed upon successful payment
                transaction_id_gateway=gateway_transaction_id,
                payment_gateway=form.payment_gateway.data,
                amount_paid_total=amount_paid_total,
                platform_fee=platform_fee,
                seller_payout_amount=seller_payout,
                payout_status='pending' # Payout to seller is pending initially
            )
            db.session.add(order)

            # Update listing status
            listing.is_available = False
            listing.status = 'sold' # Mark listing as sold
            db.session.commit()

            flash('Payment successful! Your order has been placed.', 'success')

            # Notify seller about the sale
            add_notification(
                user_id=listing.user_id,
                message=f"Your listing '{listing.title}' has been sold to {current_user.username} for R{listing.price:.2f}!",
                notification_type='listing_sold',
                payload={'order_id': order.id, 'listing_id': listing.id, 'buyer_id': current_user.id}
            )
            # Notify buyer about successful purchase
            add_notification(
                user_id=current_user.id,
                message=f"You successfully purchased '{listing.title}' from {listing.user.username} for R{listing.price:.2f}.",
                notification_type='listing_purchased',
                payload={'order_id': order.id, 'listing_id': listing.id, 'seller_id': listing.user_id}
            )

            return redirect(url_for('payments.view_order', order_id=order.id))
        else:
            flash('Payment failed. Please try again.', 'danger')

    return render_template('payments/process_payment.html', title='Process Payment', form=form, listing=listing)

@payments_bp.route("/purchase_premium", methods=['GET', 'POST'])
@login_required
def purchase_premium_listing():
    """
    Allows a user to purchase premium visibility for one of their listings.
    """
    form = PremiumListingPurchaseForm()
    
    # Dynamically populate listing choices (only user's own listings)
    user_listings = Listing.objects(user=current_user.id)
    form.listing_id.choices = [(str(l.id), f"{l.title} (ID: {l.id})") for l in user_listings]
    form.listing_id.choices.insert(0, ('', 'Select your listing'))

    if form.validate_on_submit():
        listing_to_promote = Listing.objects(id=form.listing_id.data).first()

        # Validate that the listing belongs to the current user
        if not listing_to_promote or listing_to_promote.user_id != current_user.id:
            flash('Invalid listing selected or you do not own this listing.', 'danger')
            return render_template('payments/purchase_premium.html', title='Purchase Premium', form=form)

        premium_package_key = form.premium_package.data
        package_details = PREMIUM_PACKAGES.get(premium_package_key)

        if not package_details:
            flash('Invalid premium package selected.', 'danger')
            return render_template('payments/purchase_premium.html', title='Purchase Premium', form=form)

        cost = package_details['cost']
        duration_days = package_details['duration_days']

        # --- Simulate Payment Gateway Interaction for Premium ---
        payment_successful = True # Assume payment is successful for simulation
        gateway_transaction_id = secrets.token_urlsafe(16) # Simulate a unique transaction ID

        if payment_successful:
            # Calculate premium expiry date
            new_expiry_date = datetime.utcnow() + timedelta(days=duration_days)
            
            # If already premium, extend the expiry date
            if listing_to_promote.is_premium and listing_to_promote.premium_expiry_date and listing_to_promote.premium_expiry_date > datetime.utcnow():
                new_expiry_date = listing_to_promote.premium_expiry_date + timedelta(days=duration_days)

            # Update listing to premium
            listing_to_promote.is_premium = True
            listing_to_promote.premium_expiry_date = new_expiry_date
            db.session.commit()

            # Create an Order record for the premium purchase
            # Note: For premium purchases, the 'seller' is essentially the platform,
            # but we'll use a dummy seller_id or current_user.id for simplicity if necessary.
            # Or, if you have a dedicated 'platform' user, use that ID.
            # For now, we'll set seller_id to current_user.id as a placeholder,
            # but ideally this should be a system/platform account if tracking platform income.
            order = Order(
                buyer_id=current_user.id,
                seller_id=current_user.id, # Placeholder: In a real app, this might be a system account
                listing_id=listing_to_promote.id, # Link to the listing being promoted
                price_at_purchase=cost,
                status='completed',
                transaction_id_gateway=gateway_transaction_id,
                payment_gateway=form.payment_gateway.data,
                amount_paid_total=cost,
                platform_fee=cost, # Entire amount is platform fee for premium purchase
                seller_payout_amount=0.0, # No payout to seller for premium purchase
                payout_status='paid', # Already "paid" to platform
                is_premium_listing_purchase=True,
                premium_listing_id=listing_to_promote.id
            )
            db.session.add(order)
            db.session.commit()

            flash(f'Premium visibility purchased successfully for "{listing_to_promote.title}"! It is now premium until {new_expiry_date.strftime("%b %d, %Y")}.', 'success')

            # Notify user about premium upgrade
            add_notification(
                user_id=current_user.id,
                message=f"Your listing '{listing_to_promote.title}' is now premium until {new_expiry_date.strftime('%b %d, %Y')}.",
                notification_type='premium_purchased',
                payload={'listing_id': listing_to_promote.id, 'expiry_date': new_expiry_date.isoformat()}
            )

            return redirect(url_for('listings.dashboard')) # Redirect to user's dashboard
        else:
            flash('Payment failed for premium purchase. Please try again.', 'danger')

    return render_template('payments/purchase_premium.html', title='Purchase Premium', form=form)


@payments_bp.route("/manage_orders")
@login_required
def manage_orders():
    """
    Displays orders relevant to the current user (as buyer or seller).
    """
    # Orders where current user is the buyer
    purchased_orders = Order.query.filter_by(buyer_id=current_user.id, is_premium_listing_purchase=False).order_by(Order.order_date.desc()).all()
    # Orders where current user is the seller
    sold_orders = Order.query.filter_by(seller_id=current_user.id, is_premium_listing_purchase=False).order_by(Order.order_date.desc()).all()
    # Premium purchases made by the current user
    premium_purchases = Order.query.filter_by(buyer_id=current_user.id, is_premium_listing_purchase=True).order_by(Order.order_date.desc()).all()

    return render_template(
        'payments/manage_orders.html', 
        purchased_orders=purchased_orders, 
        sold_orders=sold_orders,
        premium_purchases=premium_purchases,
        title="Manage Orders"
    )

@payments_bp.route("/view_order/<int:order_id>")
@login_required
def view_order(order_id):
    """
    Displays the details of a specific order.
    Only accessible by buyer, seller, or admin.
    """
    order = Order.query.get_or_404(order_id)

    # Ensure current user is authorized
    if not (current_user.id == order.buyer_id or 
            current_user.id == order.seller_id or 
            current_user.role == 'admin'):
        flash('You do not have permission to view this order.', 'danger')
        return redirect(url_for('payments.manage_orders'))
    
    return render_template('payments/view_order.html', title='Order Details', order=order)

# --- Admin Routes for Payments (Optional, can be integrated into admin blueprint) ---
# @payments_bp.route("/admin/manage_payments")
# @login_required
# @roles_required('admin')
# def admin_manage_payments():
#     """Admin route to view and manage all orders/payments."""
#     orders = Order.query.order_by(Order.order_date.desc()).all()
#     return render_template('admin/manage_payments.html', title='Manage Payments', orders=orders)

