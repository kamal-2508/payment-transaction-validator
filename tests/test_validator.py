"""
Test suite for Payment Transaction Validator
Covers: unit tests, edge cases, integration, boundary values
"""

import pytest
from src.validator import (
    ValidationError,
    luhn_check,
    validate_card_number,
    validate_amount,
    validate_currency,
    validate_expiry,
    validate_daily_limit,
    process_transaction,
    SINGLE_TRANSACTION_LIMIT,
    DAILY_LIMIT,
    MIN_AMOUNT,
)


# ─── LUHN ALGORITHM ──────────────────────────────────────────────────────────

class TestLuhnCheck:
    def test_valid_visa_card(self):
        assert luhn_check("4532015112830366") is True

    def test_valid_mastercard(self):
        assert luhn_check("5425233430109903") is True

    def test_invalid_card_fails_luhn(self):
        assert luhn_check("1234567890123456") is False

    def test_too_short_fails(self):
        assert luhn_check("123456789012") is False

    def test_too_long_fails(self):
        assert luhn_check("123456789012345678901") is False

    def test_single_digit_zero(self):
        assert luhn_check("0") is False


# ─── CARD NUMBER VALIDATION ───────────────────────────────────────────────────

class TestValidateCardNumber:
    def test_valid_card_passes(self):
        assert validate_card_number("4532015112830366") is True

    def test_card_with_spaces_passes(self):
        assert validate_card_number("4532 0151 1283 0366") is True

    def test_card_with_dashes_passes(self):
        assert validate_card_number("4532-0151-1283-0366") is True

    def test_empty_string_raises(self):
        with pytest.raises(ValidationError, match="non-empty string"):
            validate_card_number("")

    def test_none_raises(self):
        with pytest.raises(ValidationError):
            validate_card_number(None)

    def test_letters_raise(self):
        with pytest.raises(ValidationError, match="only digits"):
            validate_card_number("4532ABCD12830366")

    def test_invalid_luhn_raises(self):
        with pytest.raises(ValidationError, match="Luhn"):
            validate_card_number("1234567890123456")


# ─── AMOUNT VALIDATION ────────────────────────────────────────────────────────

class TestValidateAmount:
    def test_valid_amount(self):
        assert validate_amount(100.00) is True

    def test_minimum_amount(self):
        assert validate_amount(MIN_AMOUNT) is True

    def test_maximum_amount(self):
        assert validate_amount(SINGLE_TRANSACTION_LIMIT) is True

    def test_zero_raises(self):
        with pytest.raises(ValidationError, match="below minimum"):
            validate_amount(0)

    def test_negative_raises(self):
        with pytest.raises(ValidationError, match="below minimum"):
            validate_amount(-50)

    def test_exceeds_limit_raises(self):
        with pytest.raises(ValidationError, match="exceeds single transaction limit"):
            validate_amount(SINGLE_TRANSACTION_LIMIT + 0.01)

    def test_string_amount_raises(self):
        with pytest.raises(ValidationError, match="must be a number"):
            validate_amount("100")

    def test_none_raises(self):
        with pytest.raises(ValidationError, match="must be a number"):
            validate_amount(None)

    @pytest.mark.parametrize("amount", [0.01, 1.0, 999.99, 5000.0])
    def test_boundary_amounts_pass(self, amount):
        assert validate_amount(amount) is True


# ─── CURRENCY VALIDATION ─────────────────────────────────────────────────────

class TestValidateCurrency:
    @pytest.mark.parametrize("currency", ["USD", "EUR", "GBP", "INR", "JPY"])
    def test_all_supported_currencies_pass(self, currency):
        assert validate_currency(currency) is True

    def test_lowercase_currency_passes(self):
        assert validate_currency("usd") is True

    def test_unsupported_currency_raises(self):
        with pytest.raises(ValidationError, match="not supported"):
            validate_currency("AUD")

    def test_empty_currency_raises(self):
        with pytest.raises(ValidationError, match="non-empty string"):
            validate_currency("")

    def test_none_raises(self):
        with pytest.raises(ValidationError):
            validate_currency(None)

    def test_numeric_string_raises(self):
        with pytest.raises(ValidationError, match="not supported"):
            validate_currency("123")


# ─── EXPIRY VALIDATION ────────────────────────────────────────────────────────

class TestValidateExpiry:
    def test_future_date_passes(self):
        assert validate_expiry("12/99") is True

    def test_invalid_format_raises(self):
        with pytest.raises(ValidationError, match="MM/YY"):
            validate_expiry("1299")

    def test_invalid_month_raises(self):
        with pytest.raises(ValidationError, match="Invalid expiry month"):
            validate_expiry("13/99")

    def test_zero_month_raises(self):
        with pytest.raises(ValidationError, match="Invalid expiry month"):
            validate_expiry("00/99")

    def test_past_date_raises(self):
        with pytest.raises(ValidationError, match="expired"):
            validate_expiry("01/20")

    def test_non_numeric_raises(self):
        with pytest.raises(ValidationError, match="numeric"):
            validate_expiry("AB/CD")

    def test_empty_raises(self):
        with pytest.raises(ValidationError, match="non-empty string"):
            validate_expiry("")


# ─── DAILY LIMIT VALIDATION ───────────────────────────────────────────────────

class TestValidateDailyLimit:
    def test_within_limit_passes(self):
        assert validate_daily_limit(500.0, 1000.0) is True

    def test_exact_limit_passes(self):
        assert validate_daily_limit(1000.0, 9000.0) is True

    def test_exceeds_limit_raises(self):
        with pytest.raises(ValidationError, match="daily limit"):
            validate_daily_limit(5000.0, 6000.0)

    def test_zero_spent_passes(self):
        assert validate_daily_limit(100.0, 0.0) is True

    def test_negative_spent_raises(self):
        with pytest.raises(ValidationError, match="non-negative"):
            validate_daily_limit(100.0, -50.0)

    def test_full_daily_limit_single_transaction(self):
        assert validate_daily_limit(DAILY_LIMIT, 0.0) is True


# ─── INTEGRATION: PROCESS TRANSACTION ────────────────────────────────────────

class TestProcessTransaction:
    VALID_CARD = "4532015112830366"
    VALID_EXPIRY = "12/99"

    def test_valid_transaction_approved(self):
        result = process_transaction(self.VALID_CARD, 100.0, "USD", self.VALID_EXPIRY)
        assert result["status"] == "APPROVED"
        assert result["amount"] == 100.0
        assert result["currency"] == "USD"

    def test_invalid_card_declined(self):
        result = process_transaction("1234567890123456", 100.0, "USD", self.VALID_EXPIRY)
        assert result["status"] == "DECLINED"
        assert "Luhn" in result["message"]

    def test_negative_amount_declined(self):
        result = process_transaction(self.VALID_CARD, -10.0, "USD", self.VALID_EXPIRY)
        assert result["status"] == "DECLINED"
        assert "below minimum" in result["message"]

    def test_unsupported_currency_declined(self):
        result = process_transaction(self.VALID_CARD, 100.0, "AUD", self.VALID_EXPIRY)
        assert result["status"] == "DECLINED"
        assert "not supported" in result["message"]

    def test_expired_card_declined(self):
        result = process_transaction(self.VALID_CARD, 100.0, "USD", "01/20")
        assert result["status"] == "DECLINED"
        assert "expired" in result["message"]

    def test_daily_limit_exceeded_declined(self):
        result = process_transaction(
            self.VALID_CARD, 5000.0, "USD", self.VALID_EXPIRY, spent_today=9000.0
        )
        assert result["status"] == "DECLINED"
        assert "daily limit" in result["message"]

    def test_inr_currency_approved(self):
        result = process_transaction(self.VALID_CARD, 200.0, "inr", self.VALID_EXPIRY)
        assert result["status"] == "APPROVED"
        assert result["currency"] == "INR"

    def test_result_always_has_required_keys(self):
        result = process_transaction(self.VALID_CARD, 100.0, "USD", self.VALID_EXPIRY)
        assert all(k in result for k in ["status", "message", "amount", "currency"])

    @pytest.mark.parametrize("amount,expected", [
        (0.01, "APPROVED"),
        (5000.0, "APPROVED"),
        (5000.01, "DECLINED"),
        (-1, "DECLINED"),
    ])
    def test_amount_boundary_conditions(self, amount, expected):
        result = process_transaction(self.VALID_CARD, amount, "USD", self.VALID_EXPIRY)
        assert result["status"] == expected


# ─── PATTERN 4: FIXTURES ─────────────────────────────────────────────────────

@pytest.fixture
def valid_transaction():
    """Shared setup — reused across multiple tests."""
    return {
        "card_number": "4532015112830366",
        "amount": 250.0,
        "currency": "USD",
        "expiry": "12/99",
        "spent_today": 0.0,
    }

def test_fixture_transaction_approved(valid_transaction):
    result = process_transaction(**valid_transaction)
    assert result["status"] == "APPROVED"

def test_fixture_correct_amount(valid_transaction):
    result = process_transaction(**valid_transaction)
    assert result["amount"] == 250.0

def test_fixture_currency_uppercase(valid_transaction):
    result = process_transaction(**valid_transaction)
    assert result["currency"] == "USD"

def test_fixture_has_all_keys(valid_transaction):
    result = process_transaction(**valid_transaction)
    assert all(k in result for k in ["status", "amount", "currency"])


# ─── PATTERN 5: MOCKS ────────────────────────────────────────────────────────

from unittest.mock import patch, MagicMock
from src.validator import luhn_check

def test_mock_luhn_always_true():
    """Mock luhn_check to always return True — isolates card number logic."""
    with patch("src.validator.luhn_check", return_value=True) as mock_luhn:
        result = validate_card_number("0000000000000000")
        assert result is True
        mock_luhn.assert_called_once()

def test_mock_luhn_always_false():
    """Mock luhn_check to always return False — forces Luhn failure."""
    with patch("src.validator.luhn_check", return_value=False):
        with pytest.raises(ValidationError, match="Luhn"):
            validate_card_number("4532015112830366")  # valid card, but mock overrides
