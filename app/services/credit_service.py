# app/services/credit_service.py
from app.models.users import User
from app.models.credit_transactions import CreditTransaction
from app.extensions import db

def earn_credits(user: User, amount: float, source_type: str, source_id: str = None):
    """
    Awards credits to a user and records the transaction.
    """
    if amount <= 0:
        raise ValueError("Amount must be positive to earn credits.")

    user.credit_balance += amount
    user.save()

    transaction = CreditTransaction(
        user=user,
        amount=amount,
        transaction_type='earn',
        source_type=source_type,
        source_id=source_id
    )
    transaction.save()
    print(f"CREDIT_SERVICE: {user.username} earned {amount} credits from {source_type} (ID: {source_id}). New balance: {user.credit_balance}")
    return transaction

def spend_credits(user: User, amount: float, source_type: str, source_id: str = None):
    """
    Deducts credits from a user's balance and records the transaction.
    Raises ValueError if the user has insufficient credits.
    """
    if amount <= 0:
        raise ValueError("Amount must be positive to spend credits.")

    if user.credit_balance < amount:
        raise ValueError("Insufficient credits.")

    user.credit_balance -= amount
    user.save()

    transaction = CreditTransaction(
        user=user,
        amount=-amount, # Store as negative for spending
        transaction_type='spend',
        source_type=source_type,
        source_id=source_id
    )
    transaction.save()
    print(f"CREDIT_SERVICE: {user.username} spent {amount} credits for {source_type} (ID: {source_id}). New balance: {user.credit_balance}")
    return transaction
