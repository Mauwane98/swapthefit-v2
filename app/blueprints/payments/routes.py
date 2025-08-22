# app/blueprints/payments/routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta

# --- Model Imports ---
# Assuming your models are in app/models/
from app.models.users import User
from app.models.listings import Listing
from app.models.orders import Order
from app.blueprints.payments.forms import ProcessPaymentForm, TopUpCreditsForm

# --- Service and Helper Imports ---
# These would be custom services you build to interact with external APIs or handle business logic.
from app.services.paystack import PaystackService # For interacting with Paystack API
from app.services.notification_service import add_notification # For creating notifications

# --- Mock/Placeholder Implementations for Demonstration ---
# In a real app, these would be in separate files.
# -----------------------------------------------------------------

# --- Constants ---
PLATFORM_FEE_RATE = 0.10  # 10% platform fee
PREMIUM_PACKAGES = {
    '7_days': {'cost': 50.00, 'duration_days': 7, 'name': '7-Day Boost'},
    '30_days': {'cost': 150.00, 'duration_days': 30, 'name': '30-Day Feature'},
}

# --- Blueprint Definition ---
payments_bp = Blueprint(
    'payments', 
    __name__, 
    template_folder='templates', 
    static_folder='static'
)


@payments_bp.route("/create_checkout_session/<string:listing_id>", methods=['POST'])
@login_required
def create_checkout_session(listing_id):
    """
    Initializes a payment session for purchasing a listing, supporting Paystack and Platform Credits.
    """
    listing = Listing.objects(id=listing_id).first_or_404()

    if not listing.is_available:
        flash("This item is no longer available for purchase.", "warning")
        return redirect(url_for('listings.listing_detail', listing_id=listing.id))

    if listing.user.id == current_user.id:
        flash("You cannot purchase your own listing.", "danger")
        return redirect(url_for('listings.listing_detail', listing_id=listing.id))

    form = ProcessPaymentForm() # Assuming this form is used to select payment method
    if form.validate_on_submit():
        payment_gateway_choice = form.payment_gateway.data
        delivery_method = form.delivery_method.data # Get delivery method from form
        
        if payment_gateway_choice == 'Platform_Credits':
            if current_user.credit_balance >= listing.price:
                # Process payment with platform credits
                current_user.credit_balance -= listing.price
                current_user.save()

                platform_fee = listing.price * PLATFORM_FEE_RATE
                seller_payout = listing.price - platform_fee

                order = Order(
                    buyer=current_user.id,
                    seller=listing.user.id,
                    listing=listing.id,
                    price_at_purchase=listing.price,
                    status='completed',
                    transaction_id_gateway='N/A', # No external transaction ID for credit payment
                    payment_gateway='Platform Credits',
                    amount_paid_total=listing.price,
                    platform_fee=platform_fee,
                    seller_payout_amount=seller_payout,
                    payout_status='pending',
                    order_type='sale_listing',
                    delivery_method=delivery_method # Store delivery method
                )
                order.save()

                listing.is_available = False
                listing.status = 'sold'
                listing.save()

                flash('Payment successful using platform credits! Your order has been placed.', 'success')
                add_notification(
                    user_id=listing.user.id,
                    message=f"Your listing '{listing.title}' has been sold to {current_user.username} for R{listing.price:.2f} using platform credits!",
                    notification_type='listing_sold',
                    payload={'order_id': str(order.id), 'listing_id': str(listing.id), 'buyer_id': str(current_user.id)}
                )
                add_notification(
                    user_id=current_user.id,
                    message=f"You successfully purchased '{listing.title}' from {listing.user.username} for R{listing.price:.2f} using platform credits.",
                    notification_type='listing_purchased',
                    payload={'order_id': str(order.id), 'listing_id': str(listing.id), 'seller_id': str(listing.user.id)}
                )
                return redirect(url_for('payments.view_order', order_id=str(order.id)))
            else:
                flash(f"Insufficient platform credits. You have R{current_user.credit_balance:.2f} but need R{listing.price:.2f}.", "danger")
                return redirect(url_for('listings.listing_detail', listing_id=listing.id))
        
        elif payment_gateway_choice == 'Paystack':
            paystack_service = PaystackService()
            
            # Metadata to be sent to Paystack and returned in the callback
            metadata = {
                'listing_id': str(listing.id),
                'buyer_id': str(current_user.id),
                'seller_id': str(listing.user.id),
                'type': 'sale_listing',
                'delivery_method': delivery_method # Pass delivery method to metadata
            }

            # The callback URL Paystack will redirect to after payment
            callback_url = url_for('payments.paystack_callback', _external=True)

            # Paystack expects the amount in the lowest currency unit (kobo for NGN, pesewas for GHS, etc.)
            amount_in_kobo = int(listing.price * 100)

            response = paystack_service.initialize_payment(
                email=current_user.email,
                amount=amount_in_kobo,
                metadata=metadata,
                callback_url=callback_url
            )

            if response['status']:
                # Redirect user to Paystack's payment page
                return redirect(response['data']['authorization_url'])
            else:
                flash("Could not initiate payment. Please try again.", "danger")
                return redirect(url_for('listings.listing_detail', listing_id=listing.id))
        else:
            flash("Invalid payment method selected.", "danger")
            return redirect(url_for('listings.listing_detail', listing_id=listing.id))
    
    # If form is not submitted via POST or validation fails, render the listing detail page
    # This part might need adjustment depending on how the form is rendered in the template
    flash("Please select a payment method.", "danger")
    return redirect(url_for('listings.listing_detail', listing_id=listing.id))


@payments_bp.route("/create_premium_session/<string:listing_id>/<string:package_key>", methods=['POST'])
@login_required
def create_premium_session(listing_id, package_key):
    """
    Initializes a payment session with Paystack for promoting a listing.
    """
    listing = Listing.objects(id=listing_id, user=current_user.id).first_or_404()
    package = PREMIUM_PACKAGES.get(package_key)

    if not package:
        flash("Invalid premium package selected.", "danger")
        return redirect(url_for('listings.listing_detail', listing_id=listing.id))

    paystack_service = PaystackService()
    
    metadata = {
        'listing_id': str(listing.id),
        'buyer_id': str(current_user.id),
        'seller_id': str(current_user.id), # For premium, buyer and seller are the same
        'type': 'premium_purchase',
        'premium_package_key': package_key
    }
    
    callback_url = url_for('payments.paystack_callback', _external=True)
    amount_in_kobo = int(package['cost'] * 100)

    response = paystack_service.initialize_payment(
        email=current_user.email,
        amount=amount_in_kobo,
        metadata=metadata,
        callback_url=callback_url
    )

    if response['status']:
        return redirect(response['data']['authorization_url'])
    else:
        flash("Could not initiate premium payment. Please try again.", "danger")
        return redirect(url_for('listings.listing_detail', listing_id=listing.id))


@payments_bp.route("/top_up_credits", methods=['GET', 'POST'])
@login_required
def top_up_credits():
    """
    Allows a user to top up their platform credit balance.
    """
    form = TopUpCreditsForm()
    if form.validate_on_submit():
        amount = form.amount.data
        paystack_service = PaystackService()

        metadata = {
            'buyer_id': str(current_user.id),
            'type': 'credit_top_up',
            'top_up_amount': amount
        }

        callback_url = url_for('payments.paystack_callback', _external=True)
        amount_in_kobo = int(amount * 100)

        response = paystack_service.initialize_payment(
            email=current_user.email,
            amount=amount_in_kobo,
            metadata=metadata,
            callback_url=callback_url
        )

        if response['status']:
            return redirect(response['data']['authorization_url'])
        else:
            flash("Could not initiate credit top-up. Please try again.", "danger")
            return redirect(url_for('payments.top_up_credits'))
    
    return render_template("payments/top_up_credits.html", form=form)


@payments_bp.route("/paystack_callback")
def paystack_callback():
    """
    Handles the callback from Paystack after a transaction.
    Verifies the payment and finalizes the order.
    """
    reference = request.args.get('trxref') or request.args.get('reference')
    if not reference:
        flash('Payment reference not found.', 'danger')
        return redirect(url_for('listings.marketplace'))

    paystack_service = PaystackService()
    verification_response = paystack_service.verify_payment(reference)

    if verification_response and verification_response['status'] and verification_response['data']['status'] == 'success':
        data = verification_response['data']
        metadata = data.get('metadata', {})
        
        listing_id = metadata.get('listing_id')
        buyer_id = metadata.get('buyer_id')
        seller_id = metadata.get('seller_id')
        transaction_type = metadata.get('type')
        delivery_method = metadata.get('delivery_method') # Get delivery method from metadata

        listing = Listing.objects(id=listing_id).first()
        buyer = User.objects(id=buyer_id).first()
        seller = User.objects(id=seller_id).first()

        if not all([listing, buyer, seller]):
            flash('Error processing payment: associated data not found.', 'danger')
            current_app.logger.error(f"Paystack callback error: Missing data for reference {reference}")
            return redirect(url_for('listings.marketplace'))

        if transaction_type == "sale_listing":
            if not listing.is_available:
                flash('This listing is no longer available.', 'danger')
                return redirect(url_for('listings.listing_detail', listing_id=listing.id))

            platform_fee = listing.price * PLATFORM_FEE_RATE
            seller_payout = listing.price - platform_fee
            amount_paid_total = data['amount'] / 100

            order = Order(
                buyer=buyer.id,
                seller=seller.id,
                listing=listing.id,
                price_at_purchase=listing.price,
                status='completed',
                transaction_id_gateway=reference,
                payment_gateway='Paystack',
                amount_paid_total=amount_paid_total,
                platform_fee=platform_fee,
                seller_payout_amount=seller_payout,
                payout_status='pending',
                delivery_method=delivery_method # Store delivery method
            )
            order.save()

            listing.is_available = False
            listing.status = 'sold'
            listing.save()

            flash('Payment successful! Your order has been placed.', 'success')

            add_notification(
                user_id=seller.id,
                message=f"Your listing '{listing.title}' has been sold to {buyer.username} for R{listing.price:.2f}!",
                notification_type='listing_sold',
                payload={'order_id': str(order.id), 'listing_id': str(listing.id), 'buyer_id': str(buyer.id)}
            )
            add_notification(
                user_id=buyer.id,
                message=f"You successfully purchased '{listing.title}' from {seller.username} for R{listing.price:.2f}.",
                notification_type='listing_purchased',
                payload={'order_id': str(order.id), 'listing_id': str(listing.id), 'seller_id': str(seller.id)}
            )

            return redirect(url_for('payments.view_order', order_id=str(order.id)))
        
        elif transaction_type == "premium_purchase":
            premium_package_key = metadata.get('premium_package_key')
            package_details = PREMIUM_PACKAGES.get(premium_package_key)

            if not package_details:
                flash('Error processing premium purchase: package details missing.', 'danger')
                return redirect(url_for('listings.dashboard'))

            listing.is_premium = True
            listing.premium_expiry_date = datetime.utcnow() + timedelta(days=package_details['duration_days'])
            listing.save()

            order = Order(
                buyer=buyer.id,
                seller=buyer.id,
                listing=listing.id,
                price_at_purchase=package_details['cost'],
                status='completed',
                transaction_id_gateway=reference,
                payment_gateway='Paystack',
                amount_paid_total=data['amount'] / 100,
                platform_fee=0.0,
                seller_payout_amount=0.0,
                payout_status='N/A'
            )
            order.save()

            flash(f'Successfully purchased premium visibility for "{listing.title}"!', 'success')
            add_notification(
                user_id=buyer.id,
                message=f"Your listing '{listing.title}' is now premium until {listing.premium_expiry_date.strftime('%Y-%m-%d')}.",
                notification_type='premium_activated',
                payload={'listing_id': str(listing.id)}
            )
            return redirect(url_for('listings.listing_detail', listing_id=str(listing.id)))
        
        elif transaction_type == "credit_top_up":
            top_up_amount = metadata.get('top_up_amount')
            if not top_up_amount:
                flash('Error processing credit top-up: amount missing.', 'danger')
                return redirect(url_for('payments.top_up_credits'))
            
            # Ensure the buyer is the current user for security
            if str(current_user.id) != buyer_id:
                flash('Security error: Mismatched user for credit top-up.', 'danger')
                current_app.logger.error(f"Security error: Mismatched user {current_user.id} for credit top-up {buyer_id}")
                return redirect(url_for('listings.marketplace'))

            current_user.credit_balance += float(top_up_amount)
            current_user.save()

            order = Order(
                buyer=current_user.id,
                seller=current_user.id, # Self-transaction for top-up
                listing=None, # No listing associated with credit top-up
                price_at_purchase=float(top_up_amount),
                status='completed',
                transaction_id_gateway=reference,
                payment_gateway='Paystack',
                amount_paid_total=data['amount'] / 100,
                platform_fee=0.0,
                seller_payout_amount=0.0,
                payout_status='N/A',
                order_type='credit_top_up' # New field to distinguish order types
            )
            order.save()

            flash(f'Successfully topped up your credit balance with R{float(top_up_amount):.2f}!', 'success')
            add_notification(
                user_id=current_user.id,
                message=f"Your credit balance has been topped up with R{float(top_up_amount):.2f}. Your new balance is R{current_user.credit_balance:.2f}.",
                notification_type='credit_top_up',
                payload={'amount': float(top_up_amount), 'new_balance': current_user.credit_balance}
            )
            return redirect(url_for('profile.profile')) # Redirect to user profile or a credit balance page

            if not package_details:
                flash('Error processing premium purchase: package details missing.', 'danger')
                return redirect(url_for('listings.dashboard'))

            listing.is_premium = True
            listing.premium_expiry_date = datetime.utcnow() + timedelta(days=package_details['duration_days'])
            listing.save()

            order = Order(
                buyer=buyer.id,
                seller=buyer.id,
                listing=listing.id,
                price_at_purchase=package_details['cost'],
                status='completed',
                transaction_id_gateway=reference,
                payment_gateway='Paystack',
                amount_paid_total=data['amount'] / 100,
                platform_fee=0.0,
                seller_payout_amount=0.0,
                payout_status='N/A'
            )
            order.save()

            flash(f'Successfully purchased premium visibility for "{listing.title}"!', 'success')
            add_notification(
                user_id=buyer.id,
                message=f"Your listing '{listing.title}' is now premium until {listing.premium_expiry_date.strftime('%Y-%m-%d')}.",
                notification_type='premium_activated',
                payload={'listing_id': str(listing.id)}
            )
            return redirect(url_for('listings.listing_detail', listing_id=str(listing.id)))

    else:
        message = verification_response.get('message', 'Payment verification failed.')
        flash(f'Payment failed: {message}', 'danger')
        current_app.logger.error(f"Paystack verification failed for reference {reference}: {message}")
        return redirect(url_for('listings.marketplace'))


@payments_bp.route("/order/<string:order_id>")
@login_required
def view_order(order_id):
    """
    Displays the details of a specific order.
    Ensures the current user is either the buyer or seller.
    """
    order = Order.objects(id=order_id).first_or_404()
    
    if current_user.id not in [order.buyer.id, order.seller.id]:
        flash("You do not have permission to view this order.", "danger")
        return redirect(url_for('listings.dashboard'))
        
    return render_template("view_order.html", order=order)


@payments_bp.route("/order_history")
@login_required
def order_history():
    """
    Displays a history of orders for the current user,
    including items they've purchased and items they've sold.
    """
    purchases = Order.objects(buyer=current_user.id).order_by('-created_at')
    sales = Order.objects(seller=current_user.id).order_by('-created_at')
    
    return render_template("order_history.html", purchases=purchases, sales=sales)