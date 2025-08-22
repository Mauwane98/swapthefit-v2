from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user
from app.models.donations import Donation
from app.models.listings import Listing
from app.models.users import User
from app.models.notifications import Notification
from app.blueprints.donations.forms import ProposeDonationForm, ConfirmDonationReceiptForm, MarkDonationDistributedForm
from app.utils.security import roles_required
from datetime import datetime
from mongoengine.queryset.visitor import Q # For complex queries


donations_bp = Blueprint('donations', __name__)

@donations_bp.route('/propose/<string:listing_id>', methods=['GET', 'POST'])
@login_required
@roles_required('parent') # Only parents can propose donations for now
def propose_donation(listing_id):
    """
    Allows a user to propose donating a specific listing to a school or NGO.
    Now captures quantity and estimated value.
    """
    listing_to_donate = Listing.objects(id=listing_id).first()
    if not listing_to_donate:
        abort(404)

    # Ensure the listing belongs to the current user
    if listing_to_donate.owner.id != current_user.id:
        flash('You can only donate your own listings.', 'danger')
        return redirect(url_for('listings.listing_detail', listing_id=listing_id))
    
    # Ensure the listing is available for donation
    if listing_to_donate.listing_type != 'donation' or listing_to_donate.status != 'available':
        flash('This item is not marked for donation or is unavailable.', 'danger')
        return redirect(url_for('listings.listing_detail', listing_id=listing_id))

    form = ProposeDonationForm()
    # Populate the choices for the recipient select field
    recipients = User.objects(Q(roles='school') | Q(roles='ngo'), active=True)
    form.recipient_id.choices = [
        (str(user.id), user.username) for user in recipients
    ]
    form.recipient_id.choices.insert(0, ('', 'Select a recipient')) # Add a default empty choice

    if form.validate_on_submit():
        recipient_user = User.objects(id=form.recipient_id.data).first()
        if not recipient_user:
            flash('Selected recipient not found.', 'danger')
            return redirect(url_for('donations.propose_donation', listing_id=listing_id))

        # Create the Donation record with new quantity and estimated_value
        donation = Donation(
            donor=current_user.id,
            donated_listing=listing_to_donate.id,
            recipient=recipient_user.id,
            notes=form.message.data,
            quantity=form.quantity.data, # New field
            estimated_value=form.estimated_value.data # New field
        )
        donation.save()

        # Update the listing status to 'pending_pickup'
        listing_to_donate.status = 'pending_pickup'
        listing_to_donate.save()

        # Create a notification for the recipient (school/NGO)
        notification_message = f"{current_user.username} has proposed to donate '{listing_to_donate.title}' (Quantity: {donation.quantity}, Value: R{donation.estimated_value:.2f}) to you!"
        notification = Notification(
            recipient=recipient_user.id,
            sender=current_user.id,
            message=notification_message,
            link=url_for('donations.view_donation_request', donation_id=donation.id),
            notification_type='new_donation',
            payload={'donation_id': str(donation.id)}
        )
        notification.save()
        current_app.extensions['socketio'].emit(
            'new_notification',
            {'message': notification.message, 'count': Notification.objects(recipient=recipient_user.id, read=False).count()},
            room=str(recipient_user.id)
        )

        flash('Donation proposed successfully! The recipient has been notified.', 'success')
        return redirect(url_for('listings.listing_detail', listing_id=listing_id))
    
    return render_template('donations/propose_donation.html', form=form, listing=listing_to_donate)


@donations_bp.route('/manage', methods=['GET'])
@login_required
def manage_donations():
    """
    Displays donations relevant to the current user (sent by them or received by their school/NGO).
    """
    sent_donations = Donation.objects(donor=current_user.id).order_by('-donation_date')
    
    received_donations = []
    if current_user.has_role('school') or current_user.has_role('ngo'):
        received_donations = Donation.objects(recipient=current_user.id).order_by('-donation_date')
    
    return render_template(
        'donations/manage_donations.html', 
        sent_donations=sent_donations, 
        received_donations=received_donations
    )

@donations_bp.route('/impact_report')
@login_required
@roles_required('ngo') # Only NGOs can view their impact report
def impact_report():
    """
    Displays the donation impact report for the current NGO user.
    """
    # The relevant data is already stored in the current_user object
    # total_donations_received_count
    # total_donations_value
    # total_families_supported_ytd

    return render_template('donations/impact_report.html',
                           title='Donation Impact Report',
                           user=current_user) # Pass current_user to access metrics

@donations_bp.route('/view_request/<string:donation_id>')
@login_required
def view_donation_request(donation_id):
    """
    Displays the details of a specific donation request.
    Only accessible by donor or recipient.
    """
    donation = Donation.objects(id=donation_id).first()
    if not donation:
        abort(404)

    # Ensure only donor or recipient can view
    if current_user.id != donation.donor.id and current_user.id != donation.recipient.id:
        flash('You do not have permission to view this donation request.', 'danger')
        return redirect(url_for('donations.manage_donations'))
    
    confirm_form = ConfirmDonationReceiptForm()
    distribute_form = MarkDonationDistributedForm() # New form for distribution

    # Pre-populate confirm form with proposed values for convenience
    if request.method == 'GET':
        confirm_form.quantity_received.data = donation.quantity
        confirm_form.estimated_value_received.data = donation.estimated_value

    return render_template(
        'donations/view_donation_request.html', 
        donation=donation,
        confirm_form=confirm_form,
        distribute_form=distribute_form,
        cancel_form=CancelDonationForm()
    )

@donations_bp.route('/confirm_receipt/<string:donation_id>', methods=['POST'])
@login_required
@roles_required('school', 'ngo') # Only schools/NGOs can confirm receipt
def confirm_receipt(donation_id):
    """
    Allows a school or NGO to confirm receipt of a donated item.
    Updates donation record and recipient's impact metrics.
    """
    donation = Donation.objects(id=donation_id).first()
    if not donation:
        flash('Donation not found.', 'danger')
        return redirect(url_for('donations.manage_donations'))

    # Ensure current user is the recipient and status is pending_pickup
    if current_user.id != donation.recipient.id or donation.status != 'pending_pickup':
        flash('You cannot confirm receipt for this donation.', 'danger')
        return redirect(url_for('donations.manage_donations'))
    
    form = ConfirmDonationReceiptForm()
    if form.validate_on_submit():
        # Store the old values before updating for notification comparison
        old_quantity = donation.quantity
        old_value = donation.estimated_value

        donation.status = 'received'
        donation.notes = form.notes.data # Update notes with recipient's input
        donation.quantity = form.quantity_received.data # Update with confirmed quantity
        donation.estimated_value = form.estimated_value_received.data # Update with confirmed value
        donation.updated_date = datetime.utcnow()
        donation.save()

        # Update the listing status to 'donated'
        donation.donated_listing.status = 'donated'
        donation.donated_listing.is_active = False # Mark as inactive
        donation.donated_listing.save()

        # --- Update Recipient (NGO/School) User's Impact Metrics ---
        recipient_user = donation.recipient
        recipient_user.total_donations_received_count += donation.quantity
        recipient_user.total_donations_value += donation.estimated_value
        recipient_user.save() # Save updated user metrics

        # Notify the donor
        notification_message = f"Your donation of '{donation.donated_listing.title}' (Quantity: {donation.quantity}, Value: R{donation.estimated_value:.2f}) has been RECEIVED by {current_user.username}! (Previously proposed: Quantity {old_quantity}, Value R{old_value:.2f})"
        notification = Notification(
            recipient=donation.donor.id,
            sender=current_user.id,
            message=notification_message,
            link=url_for('donations.view_donation_request', donation_id=donation.id),
            notification_type='donation_status_update',
            payload={'donation_id': str(donation.id)}
        )
        notification.save()
        current_app.extensions['socketio'].emit(
            'new_notification',
            {'message': notification.message, 'count': Notification.objects(recipient=donation.donor.id, read=False).count()},
            room=str(donation.donor.id)
        )

        flash('Donation receipt confirmed and impact metrics updated!', 'success')
        return redirect(url_for('donations.view_donation_request', donation_id=donation.id))
    
    # If form validation fails, re-render the view_donation_request template
    return render_template(
        'donations/view_donation_request.html', 
        donation=donation,
        confirm_form=form, # Pass the form with validation errors
        distribute_form=MarkDonationDistributedForm() # Re-initialize other form
    )

@donations_bp.route('/distribute/<string:donation_id>', methods=['POST'])
@login_required
@roles_required('school', 'ngo') # Only schools/NGOs can mark as distributed
def mark_distributed(donation_id):
    """
    Allows a school or NGO to mark a received donated item as distributed.
    Updates donation record and recipient's families supported metric.
    """
    donation = Donation.objects(id=donation_id).first()
    if not donation:
        flash('Donation not found.', 'danger')
        return redirect(url_for('donations.manage_donations'))

    # Ensure current user is the recipient and status is 'received'
    if current_user.id != donation.recipient.id or donation.status != 'received':
        flash('You cannot mark this donation as distributed.', 'danger')
        return redirect(url_for('donations.manage_donations'))
    
    form = MarkDonationDistributedForm()
    if form.validate_on_submit():
        donation.status = 'distributed'
        # Append distribution notes to existing notes, or create if none exist
        if donation.notes:
            donation.notes += f"\nDistribution Notes: {form.distribution_notes.data}"
        else:
            donation.notes = f"Distribution Notes: {form.distribution_notes.data}"
        
        donation.families_supported = form.families_supported.data # Update with families supported
        donation.updated_date = datetime.utcnow()
        donation.save()

        # No change needed to listing status, it's already 'donated' and inactive

        # --- Update Recipient (NGO/School) User's Families Supported YTD Metric ---
        recipient_user = donation.recipient
        recipient_user.total_families_supported_ytd += donation.families_supported
        recipient_user.save() # Save updated user metrics

        # Notify the donor that their item has been distributed
        notification_message = f"Great news! Your donated item '{donation.donated_listing.title}' has been successfully DISTRIBUTED by {current_user.username}, supporting {donation.families_supported} families/individuals."
        notification = Notification(
            recipient=donation.donor.id,
            sender=current_user.id,
            message=notification_message,
            link=url_for('donations.view_donation_request', donation_id=donation.id),
            notification_type='donation_status_update',
            payload={'donation_id': str(donation.id)}
        )
        notification.save()
        current_app.extensions['socketio'].emit(
            'new_notification',
            {'message': notification.message, 'count': Notification.objects(recipient=donation.donor.id, read=False).count()},
            room=str(donation.donor.id)
        )

        flash('Donation marked as distributed and impact metrics updated!', 'success')
        return redirect(url_for('donations.view_donation_request', donation_id=donation.id))

    # If form validation fails, re-render the view_donation_request template
    return render_template(
        'donations/view_donation_request.html', 
        donation=donation,
        confirm_form=ConfirmDonationReceiptForm(), # Re-initialize other form
        distribute_form=form # Pass the form with validation errors
    )

@donations_bp.route('/cancel/<string:donation_id>', methods=['POST'])
@login_required
@roles_required('parent', 'admin') # Only the donor or an admin can cancel a pending donation
def cancel_donation(donation_id):
    """
    Allows a donor to cancel a pending donation request.
    """
    donation = Donation.objects(id=donation_id).first()
    if not donation:
        flash('Donation request not found.', 'danger')
        return redirect(url_for('donations.manage_donations'))

    # Ensure current user is the donor and the status is 'pending_pickup'
    if current_user.id != donation.donor.id and not current_user.has_role('admin'):
        flash('You do not have permission to cancel this donation.', 'danger')
        return redirect(url_for('donations.manage_donations'))
    
    if donation.status != 'pending_pickup':
        flash(f"Donation cannot be cancelled because its status is '{donation.status}'.", 'danger')
        return redirect(url_for('donations.view_donation_request', donation_id=donation.id))

    donation.status = 'cancelled' # Add 'cancelled' as a possible status if not already
    donation.updated_date = datetime.utcnow()
    donation.save()

    # Change the associated listing status back to 'available'
    donation.donated_listing.status = 'available'
    donation.donated_listing.save()

    # Notify the recipient (school/NGO) that the donation has been cancelled
    notification_message = f"The donation of '{donation.donated_listing.title}' by {donation.donor.username} has been CANCELLED."
    notification = Notification(
        recipient=donation.recipient.id,
        sender=current_user.id,
        message=notification_message,
        link=url_for('donations.view_donation_request', donation_id=donation.id),
        notification_type='donation_status_update',
        payload={'donation_id': str(donation.id)}
    )
    notification.save()
    current_app.extensions['socketio'].emit(
            'new_notification',
            {'message': notification.message, 'count': Notification.objects(recipient=donation.recipient.id, read=False).count()},
            room=str(donation.recipient.id)
    )

    flash('Donation cancelled successfully.', 'info')
    return redirect(url_for('donations.manage_donations'))