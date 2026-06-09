"""
Payment Transaction Validator
Validates real-world payment transactions before processing.
"""

from datetime import datetime
from enum import Enum


class TransactionStatus(Enum):
    APPROVED = "APPROVED"
    DECLINED = "DECLINED"


class ValidationError(Exception):
    pass


SUPPORTED_CURRENCIES = {"USD", "EUR", "GBP", "INR", "JPY"}
DAILY_LIMIT = 10000.00
SINGLE_TRANSACTION_LIMIT = 5000.00
MIN_AMOUNT = 0.01


def luhn_check(card_number: str) -> bool:
    """Validate card number using Luhn algorithm."""
    digits = [int(d) for d in card_number if d.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    total = 0
    reverse = digits[::-1]
    for i, digit in enumerate(reverse):
        if i % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def validate_card_number(card_number: str) -> bool:
    """Check card number is non-empty, numeric, and passes Luhn."""
    if not card_number or not isinstance(card_number, str):
        raise ValidationError("Card number must be a non-empty string.")
    cleaned = card_number.replace(" ", "").replace("-", "")
    if not cleaned.isdigit():
        raise ValidationError("Card number must contain only digits.")
    if not luhn_check(cleaned):
        raise ValidationError(f"Card number {card_number} failed Luhn check.")
    return True


def validate_amount(amount) -> bool:
    """Check amount is positive and within single transaction limit."""
    if not isinstance(amount, (int, float)):
        raise ValidationError("Amount must be a number.")
    if amount < MIN_AMOUNT:
        raise ValidationError(f"Amount {amount} is below minimum allowed ({MIN_AMOUNT}).")
    if amount > SINGLE_TRANSACTION_LIMIT:
        raise ValidationError(
            f"Amount {amount} exceeds single transaction limit ({SINGLE_TRANSACTION_LIMIT})."
        )
    return True


def validate_currency(currency: str) -> bool:
    """Check currency is in supported list."""
    if not currency or not isinstance(currency, str):
        raise ValidationError("Currency must be a non-empty string.")
    if currency.upper() not in SUPPORTED_CURRENCIES:
        raise ValidationError(
            f"Currency '{currency}' is not supported. Supported: {SUPPORTED_CURRENCIES}"
        )
    return True


def validate_expiry(expiry: str) -> bool:
    """Check card expiry is in MM/YY format and not expired."""
    if not expiry or not isinstance(expiry, str):
        raise ValidationError("Expiry must be a non-empty string.")
    parts = expiry.strip().split("/")
    if len(parts) != 2:
        raise ValidationError("Expiry must be in MM/YY format.")
    try:
        month, year = int(parts[0]), int(parts[1])
    except ValueError:
        raise ValidationError("Expiry month and year must be numeric.")
    if month < 1 or month > 12:
        raise ValidationError(f"Invalid expiry month: {month}.")
    full_year = 2000 + year
    now = datetime.now()
    if full_year < now.year or (full_year == now.year and month < now.month):
        raise ValidationError(f"Card expired: {expiry}.")
    return True


def validate_daily_limit(amount: float, spent_today: float) -> bool:
    """Check transaction won't exceed daily spending limit."""
    if not isinstance(spent_today, (int, float)) or spent_today < 0:
        raise ValidationError("spent_today must be a non-negative number.")
    if spent_today + amount > DAILY_LIMIT:
        raise ValidationError(
            f"Transaction would exceed daily limit. "
            f"Spent: {spent_today}, Requested: {amount}, Limit: {DAILY_LIMIT}."
        )
    return True


def process_transaction(
    card_number: str,
    amount: float,
    currency: str,
    expiry: str,
    spent_today: float = 0.0,
) -> dict:
    """
    Run all validations and return a transaction result dict.

    Returns:
        dict with keys: status, message, amount, currency
    """
    try:
        validate_card_number(card_number)
        validate_amount(amount)
        validate_currency(currency)
        validate_expiry(expiry)
        validate_daily_limit(amount, spent_today)
        return {
            "status": TransactionStatus.APPROVED.value,
            "message": "Transaction approved.",
            "amount": amount,
            "currency": currency.upper(),
        }
    except ValidationError as e:
        return {
            "status": TransactionStatus.DECLINED.value,
            "message": str(e),
            "amount": amount,
            "currency": currency.upper() if currency else "",
        }
