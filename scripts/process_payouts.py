import os
import sys
from datetime import datetime
from collections import defaultdict
import click # Import click

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models.orders import Order
from app.models.users import User
from app.services.paystack import PaystackService

# Create a Flask app context
app = create_app()
app.app_context().push()

@click.command() # Add the click decorator
def process_payouts():
    print("Starting automated payout processing...")
    paystack_service = PaystackService()

    # Fetch bank list once
    banks_response = paystack_service.list_banks()
    bank_code_map = {}
    if banks_response and banks_response['status']:
        for bank in banks_response['data']:
            bank_code_map[bank['name'].lower()] = bank['code']
    else:
        print(f"Failed to fetch bank list from Paystack: {banks_response.get('message', 'Unknown error')}")
        print("Aborting payout processing.")
        return

    pending_orders = Order.objects(payout_status='pending', status='completed')

    seller_payouts = defaultdict(float)
    seller_orders = defaultdict(list)

    for order in pending_orders:
        seller_payouts[order.seller.id] += order.total_amount
        seller_orders[order.seller.id].append(order)

    for seller_id, amount_to_payout in seller_payouts.items():
        seller = User.objects.get(id=seller_id)
        print(f"Processing payout for seller: {seller.username} (Amount: {amount_to_payout})")

        if not all([seller.bank_name, seller.account_number, seller.account_name]):
            print(f"Skipping payout for {seller.username}: Missing bank details.")
            continue

        # Get bank code from bank name
        bank_code = bank_code_map.get(seller.bank_name.lower())
        if not bank_code:
            print(f"Skipping payout for {seller.username}: Bank '{seller.bank_name}' not found in Paystack bank list.")
            # Mark orders as failed payout if bank code is not found
            for order in seller_orders[seller_id]:
                order.payout_status = 'failed'
                order.updated_date = datetime.utcnow()
                order.save()
            continue

        # Resolve account number for verification (optional but recommended)
        print(f"Resolving account number for {seller.username}...")
        account_resolve_response = paystack_service.resolve_account_number(
            account_number=seller.account_number,
            bank_code=bank_code
        )
        if account_resolve_response and account_resolve_response['status']:
            resolved_account_name = account_resolve_response['data']['account_name']
            print(f"Account resolved: {resolved_account_name}")
            # You might want to add a check here to compare resolved_account_name with seller.account_name
            # For simplicity, we'll proceed if resolution is successful.
        else:
            print(f"Failed to resolve account number for {seller.username}: {account_resolve_response.get('message', 'Unknown error')}")
            # Mark orders as failed payout if account resolution fails
            for order in seller_orders[seller_id]:
                order.payout_status = 'failed'
                order.updated_date = datetime.utcnow()
                order.save()
            continue

        # Ensure Paystack recipient code exists
        if not seller.paystack_recipient_code:
            print(f"Creating Paystack recipient for {seller.username}...")
            recipient_response = paystack_service.create_transfer_recipient(
                name=seller.account_name,
                account_number=seller.account_number,
                bank_code=bank_code # Use the fetched bank code
            )
            if recipient_response and recipient_response['status']:
                seller.paystack_recipient_code = recipient_response['data']['recipient_code']
                seller.save()
                print(f"Recipient created: {seller.paystack_recipient_code}")
            else:
                print(f"Failed to create recipient for {seller.username}: {recipient_response.get('message', 'Unknown error')}")
                # Mark orders as failed payout if recipient creation fails
                for order in seller_orders[seller_id]:
                    order.payout_status = 'failed'
                    order.updated_date = datetime.utcnow()
                    order.save()
                continue

        # Initiate transfer
        # Paystack expects amount in kobo (lowest denomination), so multiply by 100
        amount_in_kobo = int(amount_to_payout * 100)
        print(f"Initiating transfer for {seller.username} with amount {amount_in_kobo} kobo...")
        transfer_response = paystack_service.initiate_transfer(
            recipient_code=seller.paystack_recipient_code,
            amount=amount_in_kobo,
            reason=f"Payout for orders from SwapTheFit (Seller: {seller.username})"
        )

        if transfer_response and transfer_response['status']:
            transfer_id = transfer_response['data']['transfer_code']
            print(f"Transfer successful for {seller.username}. ID: {transfer_id}")
            for order in seller_orders[seller_id]:
                order.payout_status = 'paid'
                order.payout_transaction_id = transfer_id
                order.updated_date = datetime.utcnow()
                order.save()
        else:
            print(f"Transfer failed for {seller.username}: {transfer_response.get('message', 'Unknown error')}")
            for order in seller_orders[seller_id]:
                order.payout_status = 'failed'
                order.updated_date = datetime.utcnow()
                order.save()

    print("Automated payout processing completed.")

if __name__ == "__main__":
    process_payouts()
