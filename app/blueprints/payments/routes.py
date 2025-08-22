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
            db.session.commit()

            # Run fraud detection for the payment transaction
            FraudDetectionService.monitor_payment_transaction(order.id)

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

        # --- Simulate Payment Gateway Interaction for Premium Purchase ---
        payment_successful = True  # Assume payment is successful for simulation
        gateway_transaction_id = secrets.token_urlsafe(16)  # Simulate a unique transaction ID

        if payment_successful:
            # Create an Order record for the premium purchase
            order = Order(
                buyer_id=current_user.id,
                seller_id=current_user.id,  # Buyer and seller are the same for premium purchase
                listing_id=listing_to_promote.id,
                price_at_purchase=cost,
                status='completed',  # Mark as completed upon successful payment
                transaction_id_gateway=gateway_transaction_id,
                payment_gateway='Simulated',  # Or form.payment_gateway.data if a form field exists
                amount_paid_total=cost,
                platform_fee=0.0,  # No platform fee for premium purchases
                seller_payout_amount=0.0,  # No payout for premium purchases
                payout_status='N/A'
            )
            db.session.add(order)
            db.session.commit()

            # Run fraud detection for the premium purchase transaction
            FraudDetectionService.monitor_payment_transaction(order.id)

            # Update listing to premium
            listing_to_promote.is_premium = True
            listing_to_promote.premium_until = datetime.utcnow() + timedelta(days=package_details['duration_days'])
            db.session.commit()

            flash(f'Successfully purchased premium visibility for "{listing_to_promote.title}"!', 'success')

            # Notify user about premium activation
            add_notification(
                user_id=current_user.id,
                message=f"Your listing '{listing_to_promote.title}' is now premium until {listing_to_promote.premium_until.strftime('%Y-%m-%d')}.",
                notification_type='premium_activated',
                payload={'listing_id': str(listing_to_promote.id), 'premium_until': listing_to_promote.premium_until.isoformat()}
            )

            return redirect(url_for('listings.listing_detail', listing_id=listing_to_promote.id))
        else:
            flash('Premium purchase failed. Please try again.', 'danger')

    return render_template('payments/purchase_premium.html', title='Purchase Premium', form=form)

@payments_bp.route("/manage_orders")
@login_required
def manage_orders():
    """
    Displays a list of all orders (as buyer or seller) for the current user.
    """
    # Fetch orders where current user is either buyer or seller
    orders_as_buyer = Order.objects(buyer_id=current_user.id).order_by('-date_created')
    orders_as_seller = Order.objects(seller_id=current_user.id).order_by('-date_created')

    # Combine and sort orders (optional, depending on desired display)
    all_orders = sorted(list(orders_as_buyer) + list(orders_as_seller), key=lambda x: x.date_created, reverse=True)

    return render_template('payments/manage_orders.html', title='Manage Orders', orders=all_orders)