from flask import Blueprint, render_template, redirect, url_for, flash, abort, current_app
from flask_login import login_required, current_user
from app.models.swaps import SwapRequest
from app.models.listings import Listing
from app.models.notifications import Notification # For sending notifications
from app.blueprints.swaps.forms import ProposeSwapForm, AcceptSwapForm, RejectSwapForm, CancelSwapForm, CompleteSwapForm
from app.utils.security import roles_required
from datetime import datetime
from app.services.user_reputation_service import increment_transaction_count # Import for updating user trust score
from app.services.badge_service import badge_service # Import badge_service


swaps_bp = Blueprint('swaps', __name__)

@swaps_bp.route('/propose/<string:listing_id>', methods=['GET', 'POST'])
@login_required
@roles_required('parent') # Only parents can propose swaps for now (as they are individual users)
def propose_swap(listing_id):
    """
    Allows a user to propose a swap for a specific listing.
    The user selects one of their own listings to offer in exchange.
    """
    desired_listing = Listing.objects(id=listing_id).first()
    if not desired_listing:
        abort(404)

    # Prevent proposing a swap for your own listing
    if desired_listing.user.id == current_user.id:
        flash('You cannot propose a swap for your own listing.', 'danger')
        return redirect(url_for('listings.listing_detail', listing_id=desired_listing.id))
    
    # Ensure the desired listing is actually available for swap
    if desired_listing.listing_type != 'swap' or not desired_listing.is_available:
        flash('This item is not available for swap.', 'danger')
        return redirect(url_for('listings.listing_detail', listing_id=desired_listing.id))

    form = ProposeSwapForm()
    # Populate the choices for the select field
    form.your_listing_id.choices = [
        (str(listing.id), f"{listing.title} ({listing.size}) - {listing.condition}")
        for listing in Listing.objects(user=current_user.id, is_available=True, listing_type='swap')
    ]
    # Add an empty default choice
    form.your_listing_id.choices.insert(0, ('', 'Select your item to offer'))


    if form.validate_on_submit():
        offered_listing = Listing.objects(id=form.your_listing_id.data).first()

        if not offered_listing:
            flash('The item you offered for swap could not be found.', 'danger')
            return redirect(url_for('swaps.propose_swap', listing_id=listing_id))

        # Check for existing pending swap request between these two specific listings
        existing_request = SwapRequest.objects(
            requester=current_user.id,
            requester_listing=offered_listing.id,
            responder=desired_listing.user.id,
            responder_listing=desired_listing.id,
            status='pending'
        ).first()

        if existing_request:
            flash('You already have a pending swap request for these items.', 'info')
            return redirect(url_for('listings.listing_detail', listing_id=listing.id))

        swap_request = SwapRequest(
            requester=current_user.id,
            requester_listing=offered_listing.id,
            responder=desired_listing.user.id,
            responder_listing=desired_listing.id,
            message=form.message.data
        )
        swap_request.save()

        # Update status of both listings to 'pending_swap'
        offered_listing.is_available = False
        offered_listing.save()
        desired_listing.is_available = False
        desired_listing.save()

        # Create a notification for the responder
        notification = Notification(
            user=desired_listing.user,
            message=f"{current_user.username} has proposed a swap for your item: '{desired_listing.title}' with their item: '{offered_listing.title}'.",
            notification_type='swap_request',
            payload={
                'swap_request_id': str(swap_request.id),
                'sender_id': str(current_user.id),
                'link': url_for('swaps.view_swap_request', swap_request_id=swap_request.id)
            }
        )
        notification.save()
        current_app.logger.info(f"Notification sent to {desired_listing.user.username}")

        # Emit a SocketIO event to the recipient to notify them of a new swap request
        current_app.extensions['socketio'].emit(
            'new_notification',
            {'message': notification.message, 'count': Notification.objects(user=desired_listing.user, is_read=False).count()},
            room=str(desired_listing.user.id)
        )

        flash('Swap request sent successfully!', 'success')
        return redirect(url_for('listings.listing_detail', listing_id=listing_id))
    
    return render_template('swaps/propose_swap.html', form=form, desired_listing=desired_listing)


@swaps_bp.route('/manage', methods=['GET'])
@login_required
def manage_swaps():
    """
    Displays all swap requests where the current user is either the requester or the responder.
    """
    # Swap requests where current user is the requester
    sent_requests = SwapRequest.objects(requester=current_user.id).order_by('-requested_date')
    current_app.logger.info(f"User ID: {current_user.id}")
    current_app.logger.info(f"Sent requests count: {sent_requests.count()}")
    
    # Swap requests where current user is the responder
    received_requests = SwapRequest.objects(responder=current_user.id).order_by('-requested_date')
    current_app.logger.info(f"Received requests count: {received_requests.count()}")
    
    return render_template(
        'swaps/manage_swaps.html', 
        sent_requests=sent_requests, 
        received_requests=received_requests
    )

@swaps_bp.route('/view_request/<string:swap_request_id>')
@login_required
def view_swap_request(swap_request_id):
    """
    Displays the details of a specific swap request.
    Only accessible by requester or responder.
    """
    swap_request = SwapRequest.objects(id=swap_request_id).first()
    if not swap_request:
        abort(404)

    # Ensure only parties involved can view the request
    if current_user.id != swap_request.requester.id and current_user.id != swap_request.responder.id:
        flash('You do not have permission to view this swap request.', 'danger')
        return redirect(url_for('swaps.manage_swaps'))
    
    accept_form = AcceptSwapForm()
    reject_form = RejectSwapForm()
    cancel_form = CancelSwapForm()
    complete_form = CompleteSwapForm()

    return render_template('swaps/view_swap_request.html', 
                           swap=swap_request,
                           accept_form=accept_form,
                           reject_form=reject_form,
                           cancel_form=cancel_form,
                           complete_form=complete_form)


@swaps_bp.route('/accept/<string:swap_request_id>', methods=['POST'])
@login_required
@roles_required('parent', 'school') # Only parents/schools (as responders) can accept
def accept_swap(swap_request_id):
    """
    Accepts a pending swap request.
    """
    swap_request = SwapRequest.objects(id=swap_request_id).first()
    form = AcceptSwapForm()
    if not swap_request:
        flash('Swap request not found.', 'danger')
        return redirect(url_for('swaps.manage_swaps'))
    if form.validate_on_submit():

        # Ensure current user is the responder and the request is pending
        if current_user.id != swap_request.responder.id or swap_request.status != 'pending':
            flash('You do not have permission to accept this request or it is not pending.', 'danger')
            return redirect(url_for('swaps.manage_swaps'))

        swap_request.status = 'accepted'
        swap_request.updated_date = datetime.utcnow()
        swap_request.save()

        # Update statuses of both listings to reflect the accepted swap
        # They remain 'pending_swap' as logistics are still to be handled
        # listing statuses are already 'pending_swap', they don't need to change again here.

        # Notify the requester that their swap request has been accepted
        notification = Notification(
            user=swap_request.requester,
            message=f"Your swap request for '{swap_request.responder_listing.title}' has been ACCEPTED by {current_user.username}!",
            notification_type='swap_status_update',
            payload={
                'swap_request_id': str(swap_request.id),
                'sender_id': str(current_user.id),
                'link': url_for('swaps.view_swap_request', swap_request_id=swap_request.id)
            }
        )
        notification.save()
        current_app.extensions['socketio'].emit(
            'new_notification',
            {'message': notification.message, 'count': Notification.objects(user=swap_request.requester, is_read=False).count()},
            room=str(swap_request.requester.id)
        )

        flash('Swap request accepted! Please arrange logistics.', 'success')
        return redirect(url_for('swaps.view_swap_request', swap_request_id=swap_request.id))


@swaps_bp.route('/reject/<string:swap_request_id>', methods=['POST'])
@login_required
@roles_required('parent', 'school') # Only parents/schools (as responders) can reject
def reject_swap(swap_request_id):
    """
    Rejects a pending swap request.
    """
    swap_request = SwapRequest.objects(id=swap_request_id).first()
    form = RejectSwapForm()
    if not swap_request:
        flash('Swap request not found.', 'danger')
        return redirect(url_for('swaps.manage_swaps'))
    if form.validate_on_submit():

        # Ensure current user is the responder and the request is pending
        if current_user.id != swap_request.responder.id or swap_request.status != 'pending':
            flash('You do not have permission to reject this request or it is not pending.', 'danger')
            return redirect(url_for('swaps.manage_swaps'))

        swap_request.status = 'rejected'
        swap_request.updated_date = datetime.utcnow()
        swap_request.save()

        # Change listing statuses back to 'available' as the swap is off
        swap_request.requester_listing.is_available = True
        swap_request.requester_listing.save()
        swap_request.responder_listing.is_available = True
        swap_request.responder_listing.save()

        # Notify the requester that their swap request has been rejected
        notification = Notification(
            user=swap_request.requester,
            message=f"Your swap request for '{swap_request.responder_listing.title}' has been REJECTED by {current_user.username}.",
            notification_type='swap_status_update',
            payload={
                'swap_request_id': str(swap_request.id),
                'sender_id': str(current_user.id),
                'link': url_for('swaps.view_swap_request', swap_request_id=swap_request.id)
            }
        )
        notification.save()
        current_app.extensions['socketio'].emit(
            'new_notification',
            {'message': notification.message, 'count': Notification.objects(user=swap_request.requester, is_read=False).count()},
            room=str(swap_request.requester.id)
        )

        flash('Swap request rejected.', 'info')
        return redirect(url_for('swaps.view_swap_request', swap_request_id=swap_request.id))


@swaps_bp.route('/cancel/<string:swap_request_id>', methods=['POST'])
@login_required
@roles_required('parent', 'school') # Only parents/schools (as requester) can cancel
def cancel_swap(swap_request_id):
    """
    Cancels a pending or accepted swap request (by the requester).
    """
    swap_request = SwapRequest.objects(id=swap_request_id).first()
    form = CancelSwapForm()
    if not swap_request:
        flash('Swap request not found.', 'danger')
        return redirect(url_for('swaps.manage_swaps'))
    if form.validate_on_submit():

        # Ensure current user is the requester and the request is not yet completed
        if current_user.id != swap_request.requester.id or swap_request.status == 'completed':
            flash('You do not have permission to cancel this request or it is already completed.', 'danger')
            return redirect(url_for('swaps.manage_swaps'))

        swap_request.status = 'cancelled'
        swap_request.updated_date = datetime.utcnow()
        swap_request.save()

        # Change listing statuses back to 'available' as the swap is off
        swap_request.requester_listing.is_available = True
        swap_request.requester_listing.save()
        swap_request.responder_listing.is_available = True
        swap_request.responder_listing.save()

        # Notify the responder that the swap request has been cancelled
        notification = Notification(
            user=swap_request.responder,
            message=f"{current_user.username} has CANCELLED the swap request for '{swap_request.requester_listing.title}'.",
            notification_type='swap_status_update',
            payload={
                'swap_request_id': str(swap_request.id),
                'sender_id': str(current_user.id),
                'link': url_for('swaps.view_swap_request', swap_request_id=swap_request.id)
            }
        )
        notification.save()
        current_app.extensions['socketio'].emit(
            'new_notification',
            {'message': notification.message, 'count': Notification.objects(user=swap_request.responder, is_read=False).count()},
            room=str(swap_request.responder.id)
        )

        flash('Swap request cancelled.', 'info')
        return redirect(url_for('swaps.manage_swaps'))


@swaps_bp.route('/complete/<string:swap_request_id>', methods=['POST'])
@login_required
@roles_required('parent', 'school') # Both requester and responder can confirm completion
def complete_swap(swap_request_id):
    """
    Marks a swap request as completed.
    This would typically happen after logistics (pickup/delivery) are confirmed.
    """
    swap_request = SwapRequest.objects(id=swap_request_id).first()
    form = CompleteSwapForm()
    if not swap_request:
        flash('Swap request not found.', 'danger')
        return redirect(url_for('swaps.manage_swaps'))
    if form.validate_on_submit():

        # Ensure current user is involved in the swap and it's accepted
        if (current_user.id != swap_request.requester.id and current_user.id != swap_request.responder.id) or swap_request.status != 'accepted':
            flash('You do not have permission to complete this request or it is not accepted.', 'danger')
            return redirect(url_for('swaps.manage_swaps'))

        swap_request.status = 'completed'
        swap_request.updated_date = datetime.utcnow()
        swap_request.save()

        # Check and award badges for both requester and responder
        badge_service.check_and_award_badges(swap_request.requester)
        badge_service.check_and_award_badges(swap_request.responder)

        # Update listings status to 'swapped'
        swap_request.requester_listing.is_available = False
        swap_request.requester_listing.save()
        swap_request.responder_listing.is_available = False
        swap_request.responder_listing.save()

        # Notify both parties about completion
        message_to_requester = f"Your swap for '{swap_request.responder_listing.title}' with '{swap_request.requester_listing.title}' has been successfully COMPLETED!"
        message_to_responder = f"Your swap for '{swap_request.responder_listing.title}' with '{swap_request.requester_listing.title}' has been successfully COMPLETED!"

        notification_req = Notification(
            user=swap_request.requester,
            message=message_to_requester,
            notification_type='swap_status_update',
            payload={
                'swap_request_id': str(swap_request.id),
                'sender_id': str(current_user.id),
                'link': url_for('swaps.view_swap_request', swap_request_id=swap_request.id)
            }
        )
        notification_req.save()
        current_app.extensions['socketio'].emit(
            'new_notification',
            {'message': notification_req.message, 'count': Notification.objects(user=swap_request.requester, is_read=False).count()},
            room=str(swap_request.requester.id)
        )

        notification_res = Notification(
            user=swap_request.responder,
            message=message_to_responder,
            notification_type='swap_status_update',
            payload={
                'swap_request_id': str(swap_request.id),
                'sender_id': str(current_user.id),
                'link': url_for('swaps.view_swap_request', swap_request_id=swap_request.id)
            }
        )
        notification_res.save()
        current_app.extensions['socketio'].emit(
            'new_notification',
            {'message': notification_res.message, 'count': Notification.objects(user=swap_request.responder, is_read=False).count()},
            room=str(swap_request.responder.id)
        )

        flash('Swap marked as completed! Congratulations!', 'success')
        return redirect(url_for('swaps.manage_swaps'))