# Payment Transaction Validator

![CI](https://github.com/YOUR_USERNAME/payment-transaction-validator/actions/workflows/ci.yml/badge.svg)

A Python module that validates payment transactions before processing — covering card number integrity, amount limits, currency support, expiry checks, and daily spending caps.

Built with a full pytest test suite (40+ test cases) and GitHub Actions CI pipeline.

---

## Features

- **Luhn algorithm** — validates card number integrity (industry standard used by Visa, Mastercard)
- **Amount validation** — enforces minimum (₹0.01) and single transaction limit (₹5,000)
- **Currency validation** — supports USD, EUR, GBP, INR, JPY
- **Expiry validation** — MM/YY format check with real-time expiry detection
- **Daily limit enforcement** — blocks transactions that exceed ₹10,000/day cumulative cap
- **Full transaction pipeline** — single `process_transaction()` call runs all validations

---

## Project Structure

```
payment_validator/
├── src/
│   └── validator.py          # Core validation logic
├── tests/
│   └── test_validator.py     # 40+ pytest test cases
├── .github/
│   └── workflows/
│       └── ci.yml            # GitHub Actions CI pipeline
├── requirements.txt
└── README.md
```

---

## Getting Started

```bash
git clone https://github.com/YOUR_USERNAME/payment-transaction-validator.git
cd payment-transaction-validator
pip install -r requirements.txt
```

### Run the validator

```python
from src.validator import process_transaction

result = process_transaction(
    card_number="4532015112830366",
    amount=250.00,
    currency="USD",
    expiry="12/99",
    spent_today=0.0
)
print(result)
# {'status': 'APPROVED', 'message': 'Transaction approved.', 'amount': 250.0, 'currency': 'USD'}
```

### Run tests

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=src --cov-report=term-missing
```

---

## Test Coverage

| Module | Coverage |
|--------|----------|
| `src/validator.py` | 95%+ |

Test categories:
- Unit tests for each validator function
- Boundary value tests (min/max amounts, exact limits)
- Edge cases (None inputs, empty strings, type mismatches)
- Parametrized tests for currency and amount ranges
- Integration tests for end-to-end `process_transaction()` flow

---

## CI/CD

Every push to `main` triggers the GitHub Actions pipeline:
1. Installs dependencies
2. Runs full test suite with coverage
3. Fails build if coverage drops below 80%

---

## Tech Stack

- **Language:** Python 3.11
- **Testing:** pytest, pytest-cov, unittest.mock
- **CI/CD:** GitHub Actions
- **Algorithm:** Luhn (ISO/IEC 7812)
