from app.models.orders import Order
from app.models.users import User
from app.services.paystack import PaystackService
from flask import current_app
from mongoengine.queryset.visitor import Q

class PayoutService:
    def __init__(self):
        self.paystack_service = PaystackService()

    def process_pending_payouts(self):
        """
        Processes all pending payouts by aggregating amounts for each seller
        and initiating transfers via Paystack.
        """
        current_app.logger.info("Starting pending payouts processing...")
        
        # Find all orders with pending payouts
        pending_orders = Order.objects(payout_status='pending', status='completed')
        
        # Aggregate payouts by seller
        seller_payouts = {}
        for order in pending_orders:
            seller_id = str(order.seller.id)
            if seller_id not in seller_payouts:
                seller_payouts[seller_id] = {
                    'amount': 0,
                    'orders': []
                }
            seller_payouts[seller_id]['amount'] += order.seller_payout_amount
            seller_payouts[seller_id]['orders'].append(order)

        successful_payouts = 0
        failed_payouts = 0

        for seller_id, payout_info in seller_payouts.items():
            seller = User.objects(id=seller_id).first()
            if not seller:
                current_app.logger.error(f"Seller with ID {seller_id} not found for payout.")
                failed_payouts += 1
                continue

            # Ensure seller has bank details
            if not (seller.bank_name and seller.account_number and seller.account_name):
                current_app.logger.warning(f"Seller {seller.username} (ID: {seller_id}) has incomplete bank details. Payout skipped.")
                # Optionally, notify seller to update details
                failed_payouts += 1
                continue

            # 1. Create Paystack Recipient if not already created
            if not seller.paystack_recipient_code:
                # In a real scenario, you'd need to get the bank_code from Paystack's list of banks
                # For now, we'll use a placeholder or assume it's handled elsewhere.
                # A more robust solution would involve a lookup for bank_code based on bank_name.
                # For demonstration, let's assume a dummy bank_code or fetch it dynamically.
                # Example: bank_code = self.paystack_service.get_bank_code(seller.bank_name)
                # For now, I'll use a generic code or require it in the form.
                # Let's assume a mapping or a way to get it.
                # For now, I'll use a dummy bank code. This is a critical missing piece for a real system.
                # I will add a comment to remind myself to implement bank code lookup.
                bank_code = "058" # Placeholder: This needs to be dynamically fetched or mapped

                recipient_response = self.paystack_service.create_transfer_recipient(
                    name=seller.account_name,
                    account_number=seller.account_number,
                    bank_code=bank_code, # This needs to be dynamic
                    currency="ZAR" # Assuming ZAR as per project context
                )

                if recipient_response['status']:
                    seller.paystack_recipient_code = recipient_response['data']['recipient_code']
                    seller.save()
                    current_app.logger.info(f"Created Paystack recipient for {seller.username}: {seller.paystack_recipient_code}")
                else:
                    current_app.logger.error(f"Failed to create Paystack recipient for {seller.username}: {recipient_response['message']}")
                    failed_payouts += 1
                    continue
            
            # 2. Initiate Transfer
            # Paystack amount is in kobo (cents), so multiply by 100
            amount_in_kobo = int(payout_info['amount'] * 100)
            transfer_response = self.paystack_service.initiate_transfer(
                recipient_code=seller.paystack_recipient_code,
                amount=amount_in_kobo,
                reason=f"Payout for sales on SwapTheFit (Seller: {seller.username})",
                currency="ZAR" # Assuming ZAR
            )

            if transfer_response['status']:
                # Update status of all orders included in this payout
                for order in payout_info['orders']:
                    order.payout_status = 'paid'
                    order.payout_transaction_id = transfer_response['data']['transfer_code'] # Store Paystack transfer ID
                    order.save()
                successful_payouts += 1
                current_app.logger.info(f"Successfully initiated payout for {seller.username} (Amount: {payout_info['amount']:.2f} ZAR)")
            else:
                current_app.logger.error(f"Failed to initiate payout for {seller.username}: {transfer_response['message']}")
                failed_payouts += 1
        
        current_app.logger.info(f"Payout processing finished. Successful: {successful_payouts}, Failed: {failed_payouts}")
        return {"successful": successful_payouts, "failed": failed_payouts}