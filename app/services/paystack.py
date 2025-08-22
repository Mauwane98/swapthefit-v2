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

    def initialize_payment(self, email, amount, metadata=None):
        url = f"{self.base_url}/transaction/initialize"
        payload = {
            "email": email,
            "amount": int(amount * 100), # Paystack expects amount in kobo (cents)
            "metadata": metadata
        }
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
