"""
Kapture Finance - Maya Collections Voicebot
STEP 6: Collection Tools / Mock API Layer

These functions simulate the backend APIs that Maya
would call during a real collections conversation.

Tools:
1. verify_customer
2. get_account_details
3. log_promise_to_pay
4. send_payment_link
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


# ============================================================
# MOCK CUSTOMER DATABASE
# ============================================================

CUSTOMER_DATABASE = {
    "CUS-1001": {
        "customer_reference": "CUS-1001",
        "name": "Rahul Sharma",
        "loan_type": "PERSONAL_LOAN",
        "overdue_amount": 8499,
        "days_past_due": 12,
        "phone_last_four": "XXXX",
        "account_status": "ACTIVE",
        "payment_status": "OVERDUE",
    },

    "CUS-1002": {
        "customer_reference": "CUS-1002",
        "name": "Priya Verma",
        "loan_type": "PERSONAL_LOAN",
        "overdue_amount": 6250,
        "days_past_due": 8,
        "phone_last_four": "XXXX",
        "account_status": "ACTIVE",
        "payment_status": "OVERDUE",
    },

    "CUS-PAID-001": {
        "customer_reference": "CUS-PAID-001",
        "name": "Amit Kumar",
        "loan_type": "PERSONAL_LOAN",
        "overdue_amount": 0,
        "days_past_due": 0,
        "phone_last_four": "XXXX",
        "account_status": "ACTIVE",
        "payment_status": "PAID",
    },
}


# ============================================================
# MOCK PROMISE-TO-PAY DATABASE
# ============================================================

PTP_DATABASE = []


# ============================================================
# MOCK PAYMENT LINK DATABASE
# ============================================================

PAYMENT_LINK_DATABASE = []


# ============================================================
# RESULT MODELS
# ============================================================

@dataclass
class VerificationResult:
    success: bool
    customer_reference: str
    verified_name: Optional[str] = None
    message: str = ""


@dataclass
class AccountDetailsResult:
    success: bool
    customer_reference: str
    loan_type: Optional[str] = None
    overdue_amount: Optional[int] = None
    days_past_due: Optional[int] = None
    payment_status: Optional[str] = None
    message: str = ""


@dataclass
class PTPResult:
    success: bool
    customer_reference: str
    amount: Optional[int] = None
    payment_date: Optional[str] = None
    message: str = ""


@dataclass
class PaymentLinkResult:
    success: bool
    customer_reference: str
    payment_link: Optional[str] = None
    amount: Optional[int] = None
    message: str = ""


# ============================================================
# TOOL 1 - VERIFY CUSTOMER
# ============================================================

def verify_customer(
    customer_reference: str,
    verification_value: str
) -> VerificationResult:

    customer = CUSTOMER_DATABASE.get(customer_reference)

    if customer is None:
        return VerificationResult(
            success=False,
            customer_reference=customer_reference,
            message="Customer record not found."
        )

    # Demo authentication rule:
    # Customer must provide the expected verification value.
    #
    # In production this could be:
    # - DOB
    # - OTP
    # - masked phone verification
    # - approved knowledge-based authentication

    expected_value = "12"

    if verification_value != expected_value:
        return VerificationResult(
            success=False,
            customer_reference=customer_reference,
            message="Identity verification failed."
        )

    return VerificationResult(
        success=True,
        customer_reference=customer_reference,
        verified_name=customer["name"],
        message="Customer successfully verified."
    )


# ============================================================
# TOOL 2 - GET ACCOUNT DETAILS
# ============================================================

def get_account_details(
    customer_reference: str
) -> AccountDetailsResult:

    customer = CUSTOMER_DATABASE.get(customer_reference)

    if customer is None:
        return AccountDetailsResult(
            success=False,
            customer_reference=customer_reference,
            message="Account not found."
        )

    return AccountDetailsResult(
        success=True,
        customer_reference=customer_reference,
        loan_type=customer["loan_type"],
        overdue_amount=customer["overdue_amount"],
        days_past_due=customer["days_past_due"],
        payment_status=customer["payment_status"],
        message="Account details retrieved successfully."
    )


# ============================================================
# TOOL 3 - LOG PROMISE TO PAY
# ============================================================

def log_promise_to_pay(
    customer_reference: str,
    amount: int,
    payment_date: str
) -> PTPResult:

    customer = CUSTOMER_DATABASE.get(customer_reference)

    if customer is None:
        return PTPResult(
            success=False,
            customer_reference=customer_reference,
            message="Customer account not found."
        )

    overdue_amount = customer["overdue_amount"]

    # Basic validation

    if amount <= 0:
        return PTPResult(
            success=False,
            customer_reference=customer_reference,
            message="Payment amount must be greater than zero."
        )

    if amount > overdue_amount:
        return PTPResult(
            success=False,
            customer_reference=customer_reference,
            message="Payment amount exceeds the current overdue amount."
        )

    # Save commitment

    record = {
        "customer_reference": customer_reference,
        "amount": amount,
        "payment_date": payment_date,
        "created_at": datetime.now().isoformat(),
        "status": "PROMISED",
    }

    PTP_DATABASE.append(record)

    return PTPResult(
        success=True,
        customer_reference=customer_reference,
        amount=amount,
        payment_date=payment_date,
        message="Promise-to-pay successfully recorded."
    )


# ============================================================
# TOOL 4 - SEND PAYMENT LINK
# ============================================================

def send_payment_link(
    customer_reference: str,
    amount: int
) -> PaymentLinkResult:

    customer = CUSTOMER_DATABASE.get(customer_reference)

    if customer is None:
        return PaymentLinkResult(
            success=False,
            customer_reference=customer_reference,
            message="Customer account not found."
        )

    if amount <= 0:
        return PaymentLinkResult(
            success=False,
            customer_reference=customer_reference,
            message="Payment amount must be greater than zero."
        )

    if amount > customer["overdue_amount"]:
        return PaymentLinkResult(
            success=False,
            customer_reference=customer_reference,
            message="Payment amount exceeds overdue amount."
        )

    # Mock payment URL
    payment_link = (
        f"https://pay.kapture-finance.demo/"
        f"{customer_reference}/{amount}"
    )

    record = {
        "customer_reference": customer_reference,
        "amount": amount,
        "payment_link": payment_link,
        "created_at": datetime.now().isoformat(),
        "status": "GENERATED",
    }

    PAYMENT_LINK_DATABASE.append(record)

    return PaymentLinkResult(
        success=True,
        customer_reference=customer_reference,
        payment_link=payment_link,
        amount=amount,
        message="Payment link generated successfully."
    )


# ============================================================
# TOOL TESTS
# ============================================================

def run_tool_tests():

    print("\n")
    print("=" * 70)
    print("STEP 6 - COLLECTION TOOLS TEST")
    print("=" * 70)

    # --------------------------------------------------------
    # TEST 1 - CUSTOMER VERIFICATION
    # --------------------------------------------------------

    print("\n[TEST 1] verify_customer")

    result = verify_customer(
        customer_reference="CUS-1001",
        verification_value="12"
    )

    print(result)

    # --------------------------------------------------------
    # TEST 2 - ACCOUNT DETAILS
    # --------------------------------------------------------

    print("\n[TEST 2] get_account_details")

    result = get_account_details(
        customer_reference="CUS-1001"
    )

    print(result)

    # --------------------------------------------------------
    # TEST 3 - PROMISE TO PAY
    # --------------------------------------------------------

    print("\n[TEST 3] log_promise_to_pay")

    result = log_promise_to_pay(
        customer_reference="CUS-1001",
        amount=8499,
        payment_date="2026-08-15"
    )

    print(result)

    # --------------------------------------------------------
    # TEST 4 - PAYMENT LINK
    # --------------------------------------------------------

    print("\n[TEST 4] send_payment_link")

    result = send_payment_link(
        customer_reference="CUS-1001",
        amount=8499
    )

    print(result)

    # --------------------------------------------------------
    # DATABASE OUTPUT
    # --------------------------------------------------------

    print("\n")
    print("=" * 70)
    print("PTP DATABASE")
    print("=" * 70)

    for record in PTP_DATABASE:
        print(record)

    print("\n")
    print("=" * 70)
    print("PAYMENT LINK DATABASE")
    print("=" * 70)

    for record in PAYMENT_LINK_DATABASE:
        print(record)

    print("\n")
    print("=" * 70)
    print("STEP 6 COMPLETE")
    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    run_tool_tests()