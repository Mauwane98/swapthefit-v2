import requests
from flask import current_app

class PaystackService:
    def __init__(self):
        self.base_url = "https://api.paystack.co"
        self.secret_key = current_app.config.get('PAYSTACK_SECRET_KEY')

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }

    def initialize_payment(self, email, amount, metadata=None, callback_url=None):
        url = f"{self.base_url}/transaction/initialize"
        payload = {
            "email": email,
            "amount": int(amount * 100), # Paystack expects amount in kobo (cents)
            "metadata": metadata
        }
        if callback_url:
            payload['callback_url'] = callback_url
        try:
            response = requests.post(url, headers=self._headers(), json=payload)
            response.raise_for_status() # Raise an exception for HTTP errors
            return response.json()
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Paystack initialize payment error: {e}")
            return {"status": False, "message": str(e)}

    def verify_payment(self, reference):
        url = f"{self.base_url}/transaction/verify/{reference}"
        try:
            response = requests.get(url, headers=self._headers())
            response.raise_for_status() # Raise an exception for HTTP errors
            return response.json()
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Paystack verify payment error: {e}")
            return {"status": False, "message": str(e)}

    def list_banks(self, currency="NGN"):
        """
        Retrieves a list of banks from Paystack.
        Args:
            currency (str): The currency to filter banks by. Defaults to NGN.
        Returns:
            dict: Paystack API response containing a list of banks.
        """
        url = f"{self.base_url}/bank?currency={currency}"
        try:
            response = requests.get(url, headers=self._headers())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Paystack list banks error: {e}")
            return {"status": False, "message": str(e)}

    def resolve_account_number(self, account_number, bank_code):
        """
        Resolves an account number to get account details.
        Args:
            account_number (str): The account number to resolve.
            bank_code (str): The bank code of the account.
        Returns:
            dict: Paystack API response containing account details.
        """
        url = f"{self.base_url}/bank/resolve?account_number={account_number}&bank_code={bank_code}"
        try:
            response = requests.get(url, headers=self._headers())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Paystack resolve account number error: {e}")
            return {"status": False, "message": str(e)}

    def create_transfer_recipient(self, name, account_number, bank_code, currency="NGN", recipient_type="nuban"):
        """
        Creates a transfer recipient on Paystack.
        Args:
            name (str): Name of the recipient.
            account_number (str): Bank account number.
            bank_code (str): Bank code (e.g., from Paystack's list of banks).
            currency (str): Currency, default to NGN.
            recipient_type (str): Type of recipient, default to 'nuban' for Nigerian bank accounts.
        Returns:
            dict: Paystack API response.
        """
        url = f"{self.base_url}/transferrecipient"
        payload = {
            "type": recipient_type,
            "name": name,
            "account_number": account_number,
            "bank_code": bank_code,
            "currency": currency
        }
        try:
            response = requests.post(url, headers=self._headers(), json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Paystack create transfer recipient error: {e}")
            return {"status": False, "message": str(e)}

    def initiate_transfer(self, recipient_code, amount, reason=None, currency="NGN"):
        """
        Initiates a transfer to a Paystack recipient.
        Args:
            recipient_code (str): The recipient code obtained from create_transfer_recipient.
            amount (float): Amount to transfer in kobo (lowest denomination).
            reason (str, optional): Description for the transfer.
            currency (str): Currency, default to NGN.
        Returns:
            dict: Paystack API response.
        """
        url = f"{self.base_url}/transfer"
        payload = {
            "source": "balance", # Always transfer from your Paystack balance
            "reason": reason,
            "amount": int(amount), # Amount should already be in kobo
            "recipient": recipient_code,
            "currency": currency
        }
        try:
            response = requests.post(url, headers=self._headers(), json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Paystack initiate transfer error: {e}")
            return {"status": False, "message": str(e)}
