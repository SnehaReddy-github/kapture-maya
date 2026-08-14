from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import re


# ============================================================
# KAPTURE FINANCE - MAYA COLLECTIONS VOICEBOT
# BACKEND STATE ENGINE
#
# Steps covered:
# 0. Call initialization
# 1. Contact eligibility / DNC
# 2. Authentication
# 3. Account access
# 4. Intent + entity detection
# 5. Promise-to-pay validation
#
# This is a deterministic backend simulation.
# The LLM/Vapi layer will be connected later.
# ============================================================


# ============================================================
# ENUMS
# ============================================================

class CallState(Enum):
    CALL_INIT = "CALL_INIT"
    INTRODUCTION = "INTRODUCTION"
    AUTHENTICATION = "AUTHENTICATION"
    ACCOUNT_ACCESS = "ACCOUNT_ACCESS"
    INTENT_DETECTION = "INTENT_DETECTION"
    PTP_NEGOTIATION = "PTP_NEGOTIATION"
    PAYMENT_LINK = "PAYMENT_LINK"
    ESCALATION = "ESCALATION"
    TERMINATE = "TERMINATE"
    TERMINATE_DNC = "TERMINATE_DNC"


class AuthState(Enum):
    NOT_VERIFIED = "NOT_VERIFIED"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"


class Intent(Enum):
    WILL_PAY = "WILL_PAY"
    CANNOT_PAY = "CANNOT_PAY"
    DISPUTE = "DISPUTE"
    ALREADY_PAID = "ALREADY_PAID"
    WRONG_PERSON = "WRONG_PERSON"
    CALLBACK_REQUEST = "CALLBACK_REQUEST"
    HOSTILE = "HOSTILE"
    DO_NOT_CALL = "DO_NOT_CALL"
    PAYMENT_LINK = "PAYMENT_LINK"
    UNKNOWN = "UNKNOWN"


# ============================================================
# CUSTOMER DATABASE
# MOCK DATA ONLY
# ============================================================

CUSTOMER_DATABASE = {
    "CUS-1001": {
        "name": "Rahul Sharma",
        "phone": "+91XXXXXXXXXX",
        "loan_type": "Personal Loan",
        "overdue_amount": 8499,
        "days_past_due": 12,
        "registered_mobile_last4": "1234",
        "status": "ACTIVE_COLLECTION",
        "do_not_call": False,
    },

    "CUS-DNC-001": {
        "name": "DNC Customer",
        "phone": "+91XXXXXXXXXX",
        "loan_type": "Personal Loan",
        "overdue_amount": 5000,
        "days_past_due": 20,
        "registered_mobile_last4": "5678",
        "status": "ACTIVE_COLLECTION",
        "do_not_call": True,
    },

    "CUS-PAID-001": {
        "name": "Paid Customer",
        "phone": "+91XXXXXXXXXX",
        "loan_type": "Personal Loan",
        "overdue_amount": 7499,
        "days_past_due": 8,
        "registered_mobile_last4": "2468",
        "status": "ALREADY_PAID",
        "do_not_call": False,
    },
}


# ============================================================
# MOCK PTP DATABASE
# ============================================================

PTP_DATABASE = []


# ============================================================
# CALL CONTEXT
# ============================================================

@dataclass
class CallContext:

    call_id: str
    customer_reference: str
    phone_number: str
    campaign_id: str

    current_state: CallState = CallState.CALL_INIT
    auth_state: AuthState = AuthState.NOT_VERIFIED

    auth_attempts: int = 0
    max_auth_attempts: int = 2

    current_intent: Optional[str] = None
    disposition: Optional[str] = None

    customer_name: Optional[str] = None
    overdue_amount: Optional[int] = None
    days_past_due: Optional[int] = None

    ptp_amount: Optional[int] = None
    ptp_date: Optional[str] = None

    events: list[str] = field(default_factory=list)


# ============================================================
# UTILITY
# ============================================================

def log_event(context: CallContext, event: str):

    context.events.append(event)

    print(f"[EVENT] {event}")


# ============================================================
# STEP 0
# CALL INITIALIZATION
# ============================================================

def initialize_call(
    call_id: str,
    customer_reference: str,
    phone_number: str,
    campaign_id: str
) -> CallContext:

    context = CallContext(
        call_id=call_id,
        customer_reference=customer_reference,
        phone_number=phone_number,
        campaign_id=campaign_id
    )

    print("\n" + "=" * 70)
    print("STEP 0 - CALL INITIALIZATION")
    print("=" * 70)

    print(f"Call ID: {context.call_id}")
    print(f"Customer Reference: {context.customer_reference}")
    print(f"Campaign: {context.campaign_id}")
    print(f"Authentication: {context.auth_state.value}")
    print(f"Current State: {context.current_state.value}")

    log_event(context, "CALL_INITIALIZED")

    return context


# ============================================================
# STEP 1
# CONTACT ELIGIBILITY
# ============================================================

def check_contact_eligibility(context: CallContext) -> bool:

    print("\n" + "=" * 70)
    print("STEP 1 - CONTACT ELIGIBILITY")
    print("=" * 70)

    customer = CUSTOMER_DATABASE.get(context.customer_reference)

    if customer is None:

        print("Customer record not found.")

        context.disposition = "CUSTOMER_NOT_FOUND"
        context.current_state = CallState.TERMINATE

        log_event(context, "CUSTOMER_NOT_FOUND")

        return False

    if customer["do_not_call"] is True:

        print("Contact blocked: DO_NOT_CALL")

        context.disposition = "DO_NOT_CALL"
        context.current_state = CallState.TERMINATE_DNC

        log_event(context, "DNC_BLOCKED")

        return False

    if customer["status"] == "ALREADY_PAID":

        print("Customer account indicates payment may already be completed.")

    print("Contact eligible.")

    context.current_state = CallState.INTRODUCTION

    log_event(context, "CONTACT_ELIGIBLE")

    print(
        f"Transition: CALL_INIT -> {context.current_state.value}"
    )

    return True


# ============================================================
# STEP 2
# INTRODUCTION
# ============================================================

def introduction(context: CallContext):

    print("\n" + "=" * 70)
    print("STEP 2 - INTRODUCTION")
    print("=" * 70)

    if context.current_state != CallState.INTRODUCTION:

        print("BLOCKED: Invalid state for introduction.")
        return False

    print(
        "MAYA:"
    )

    print(
        "Hello, this is Maya calling on behalf of Kapture Finance."
    )

    print(
        "This call is regarding your loan account. "
        "Before I discuss any account details, "
        "I need to verify that I am speaking with the correct customer."
    )

    context.current_state = CallState.AUTHENTICATION

    log_event(context, "INTRODUCTION_COMPLETED")

    print(
        f"Transition: INTRODUCTION -> {context.current_state.value}"
    )

    return True


# ============================================================
# STEP 3
# AUTHENTICATION
# ============================================================

def verify_customer(
    context: CallContext,
    provided_last4: str
) -> bool:

    print("\n" + "=" * 70)
    print("STEP 3 - CUSTOMER AUTHENTICATION")
    print("=" * 70)

    # STATE ENFORCEMENT
    if context.current_state != CallState.AUTHENTICATION:

        print(
            "SECURITY BLOCK: Authentication can only occur "
            "from AUTHENTICATION state."
        )

        log_event(context, "AUTH_STATE_VIOLATION")

        return False

    # Already verified
    if context.auth_state == AuthState.VERIFIED:

        print("Customer already verified.")

        return True

    customer = CUSTOMER_DATABASE.get(
        context.customer_reference
    )

    if customer is None:

        context.auth_state = AuthState.FAILED
        context.disposition = "CUSTOMER_NOT_FOUND"

        log_event(context, "AUTH_CUSTOMER_NOT_FOUND")

        return False

    context.auth_attempts += 1

    print(
        f"Authentication attempt: "
        f"{context.auth_attempts}/{context.max_auth_attempts}"
    )

    expected_last4 = customer["registered_mobile_last4"]

    if provided_last4 == expected_last4:

        context.auth_state = AuthState.VERIFIED

        context.customer_name = customer["name"]

        context.current_state = CallState.ACCOUNT_ACCESS

        log_event(context, "CUSTOMER_VERIFIED")

        print("Authentication successful.")
        print("Debt disclosure is now permitted.")

        print(
            f"Transition: AUTHENTICATION -> "
            f"{context.current_state.value}"
        )

        return True

    context.auth_state = AuthState.FAILED

    log_event(context, "AUTHENTICATION_FAILED")

    print("Authentication failed.")

    if context.auth_attempts >= context.max_auth_attempts:

        context.disposition = "AUTH_FAILED"
        context.current_state = CallState.ESCALATION

        log_event(context, "AUTH_MAX_ATTEMPTS_REACHED")

        print("Maximum authentication attempts reached.")
        print("Routing to secure handling.")

    return False


# ============================================================
# STEP 3A
# ACCOUNT ACCESS
# ============================================================

def get_account_details(
    context: CallContext
) -> Optional[dict]:

    print("\n" + "=" * 70)
    print("ACCOUNT ACCESS")
    print("=" * 70)

    # CRITICAL SECURITY CONTROL
    if context.auth_state != AuthState.VERIFIED:

        print(
            "SECURITY BLOCK: Account details cannot be disclosed "
            "before successful authentication."
        )

        log_event(context, "UNAUTHORIZED_ACCOUNT_ACCESS_BLOCKED")

        return None

    if context.current_state != CallState.ACCOUNT_ACCESS:

        print(
            "SECURITY BLOCK: Invalid state for account access."
        )

        log_event(context, "ACCOUNT_STATE_VIOLATION")

        return None

    customer = CUSTOMER_DATABASE.get(
        context.customer_reference
    )

    if customer is None:
        return None

    context.customer_name = customer["name"]
    context.overdue_amount = customer["overdue_amount"]
    context.days_past_due = customer["days_past_due"]

    print(
        f"Customer: {context.customer_name}"
    )

    print(
        f"Loan Type: {customer['loan_type']}"
    )

    print(
        f"Overdue Amount: ₹{context.overdue_amount}"
    )

    print(
        f"Days Past Due: {context.days_past_due}"
    )

    context.current_state = CallState.INTENT_DETECTION

    log_event(context, "ACCOUNT_DETAILS_ACCESSED")

    print(
        f"Transition: ACCOUNT_ACCESS -> "
        f"{context.current_state.value}"
    )

    return customer


# ============================================================
# STEP 4
# INTENT DETECTION
# ============================================================

def detect_intent(user_text: str) -> Intent:

    text = user_text.lower().strip()

    # DNC should have highest priority
    if any(
        phrase in text
        for phrase in [
            "do not call",
            "don't call",
            "stop calling",
            "remove my number",
            "never call",
            "unsubscribe"
        ]
    ):
        return Intent.DO_NOT_CALL

    if any(
        phrase in text
        for phrase in [
            "already paid",
            "i paid",
            "payment done",
            "payment was made",
            "paid yesterday",
            "paid last week"
        ]
    ):
        return Intent.ALREADY_PAID

    if any(
        phrase in text
        for phrase in [
            "wrong person",
            "wrong number",
            "not rahul",
            "you have the wrong"
        ]
    ):
        return Intent.WRONG_PERSON

    if any(
        phrase in text
        for phrase in [
            "dispute",
            "wrong amount",
            "amount is wrong",
            "i disagree",
            "not my loan",
            "incorrect amount"
        ]
    ):
        return Intent.DISPUTE

    if any(
        phrase in text
        for phrase in [
            "call me later",
            "call later",
            "call tomorrow",
            "busy now",
            "callback",
            "call back"
        ]
    ):
        return Intent.CALLBACK_REQUEST

    if any(
        phrase in text
        for phrase in [
            "cannot pay",
            "can't pay",
            "cannot afford",
            "financial problem",
            "hardship",
            "no money",
            "salary problem",
            "lost my job"
        ]
    ):
        return Intent.CANNOT_PAY

    if any(
        phrase in text
        for phrase in [
            "shut up",
            "idiot",
            "stop bothering",
            "go away",
            "fraud",
            "scam"
        ]
    ):
        return Intent.HOSTILE

    if any(
        phrase in text
        for phrase in [
            "payment link",
            "send link",
            "pay online",
            "link please"
        ]
    ):
        return Intent.PAYMENT_LINK

    if any(
        phrase in text
        for phrase in [
            "i will pay",
            "i'll pay",
            "yes i can pay",
            "i can pay",
            "will pay",
            "i can make the payment"
        ]
    ):
        return Intent.WILL_PAY

    return Intent.UNKNOWN


# ============================================================
# ENTITY EXTRACTION
# ============================================================

def extract_amount(text: str) -> Optional[int]:

    patterns = [
        r"₹\s*([0-9,]+)",
        r"rs\.?\s*([0-9,]+)",
        r"rupees?\s*([0-9,]+)",
        r"pay\s*([0-9,]+)",
        r"([0-9,]+)\s*rupees?"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text.lower()
        )

        if match:

            amount_text = match.group(1)

            amount_text = amount_text.replace(",", "")

            try:
                return int(amount_text)
            except ValueError:
                pass

    return None


def extract_payment_date(text: str) -> Optional[str]:

    text_lower = text.lower()

    if "today" in text_lower:
        return "TODAY"

    if "tomorrow" in text_lower:
        return "TOMORROW"

    if "day after tomorrow" in text_lower:
        return "DAY_AFTER_TOMORROW"

    # Simple DD/MM/YYYY or DD-MM-YYYY
    match = re.search(
        r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
        text
    )

    if match:
        return match.group(1)

    return None


# ============================================================
# STEP 4A
# HANDLE INTENT
# ============================================================

def handle_intent(
    context: CallContext,
    user_text: str
) -> Intent:

    print("\n" + "=" * 70)
    print("STEP 4 - INTENT DETECTION")
    print("=" * 70)

    if context.current_state != CallState.INTENT_DETECTION:

        print(
            "BLOCKED: Intent detection is not allowed "
            "from the current state."
        )

        return Intent.UNKNOWN

    intent = detect_intent(user_text)

    context.current_intent = intent.value

    print(f"User: {user_text}")
    print(f"Detected Intent: {intent.value}")

    log_event(
        context,
        f"INTENT_DETECTED:{intent.value}"
    )

    if intent == Intent.DO_NOT_CALL:

        context.disposition = "DO_NOT_CALL"
        context.current_state = CallState.TERMINATE_DNC

        log_event(context, "DNC_REQUEST")

    elif intent == Intent.ALREADY_PAID:

        context.disposition = "ALREADY_PAID"
        context.current_state = CallState.ESCALATION

        log_event(context, "ALREADY_PAID_REVIEW_REQUIRED")

    elif intent == Intent.WRONG_PERSON:

        context.disposition = "WRONG_PERSON"
        context.current_state = CallState.TERMINATE

        log_event(context, "WRONG_PERSON")

    elif intent == Intent.DISPUTE:

        context.disposition = "DISPUTE"
        context.current_state = CallState.ESCALATION

        log_event(context, "DISPUTE_ESCALATION")

    elif intent == Intent.CANNOT_PAY:

        context.disposition = "HARDSHIP"
        context.current_state = CallState.ESCALATION

        log_event(context, "HARDSHIP_ESCALATION")

    elif intent == Intent.CALLBACK_REQUEST:

        context.disposition = "CALLBACK_REQUEST"
        context.current_state = CallState.TERMINATE

        log_event(context, "CALLBACK_REQUEST")

    elif intent == Intent.HOSTILE:

        context.disposition = "HOSTILE"
        context.current_state = CallState.ESCALATION

        log_event(context, "HOSTILE_ESCALATION")

    elif intent == Intent.PAYMENT_LINK:

        context.current_state = CallState.PAYMENT_LINK

        log_event(context, "PAYMENT_LINK_REQUEST")

    elif intent == Intent.WILL_PAY:

        context.current_state = CallState.PTP_NEGOTIATION

        log_event(context, "PTP_NEGOTIATION_STARTED")

    else:

        log_event(context, "INTENT_REQUIRES_CLARIFICATION")

    print(
        f"Next State: {context.current_state.value}"
    )

    return intent


# ============================================================
# STEP 5
# PROMISE-TO-PAY VALIDATION
# ============================================================

@dataclass
class PTPValidationResult:

    valid: bool
    reason: str

    amount: Optional[int] = None
    date: Optional[str] = None


def validate_ptp(
    context: CallContext,
    amount: Optional[int],
    payment_date: Optional[str]
) -> PTPValidationResult:

    print("\n" + "=" * 70)
    print("STEP 5 - PROMISE-TO-PAY VALIDATION")
    print("=" * 70)

    # --------------------------------------------------------
    # SECURITY CHECK
    # --------------------------------------------------------

    if context.auth_state != AuthState.VERIFIED:

        print(
            "SECURITY BLOCK: PTP cannot be created "
            "before customer verification."
        )

        log_event(
            context,
            "PTP_BLOCKED_NOT_VERIFIED"
        )

        return PTPValidationResult(
            valid=False,
            reason="CUSTOMER_NOT_VERIFIED"
        )

    # --------------------------------------------------------
    # STATE CHECK
    # --------------------------------------------------------

    if context.current_state != CallState.PTP_NEGOTIATION:

        print(
            "STATE BLOCK: PTP is only allowed "
            "during PTP_NEGOTIATION."
        )

        log_event(
            context,
            "PTP_INVALID_STATE"
        )

        return PTPValidationResult(
            valid=False,
            reason="INVALID_STATE"
        )

    # --------------------------------------------------------
    # AMOUNT CHECK
    # --------------------------------------------------------

    if amount is None:

        return PTPValidationResult(
            valid=False,
            reason="PAYMENT_AMOUNT_REQUIRED"
        )

    if amount <= 0:

        return PTPValidationResult(
            valid=False,
            reason="PAYMENT_AMOUNT_MUST_BE_POSITIVE"
        )

    if context.overdue_amount is not None:

        if amount > context.overdue_amount:

            return PTPValidationResult(
                valid=False,
                reason="AMOUNT_EXCEEDS_OVERDUE_BALANCE"
            )

    # --------------------------------------------------------
    # DATE CHECK
    # --------------------------------------------------------

    if not payment_date:

        return PTPValidationResult(
            valid=False,
            reason="PAYMENT_DATE_REQUIRED"
        )

    # --------------------------------------------------------
    # VALID
    # --------------------------------------------------------

    context.ptp_amount = amount
    context.ptp_date = payment_date

    context.current_state = CallState.PAYMENT_LINK

    log_event(
        context,
        "PTP_VALIDATED"
    )

    print(
        f"PTP Amount: ₹{amount}"
    )

    print(
        f"PTP Date: {payment_date}"
    )

    print("PTP validation successful.")

    return PTPValidationResult(
        valid=True,
        reason="PTP_VALID",
        amount=amount,
        date=payment_date
    )


# ============================================================
# LOG PROMISE TO PAY
# ============================================================

def log_promise_to_pay(
    context: CallContext
) -> bool:

    if context.auth_state != AuthState.VERIFIED:

        print(
            "SECURITY BLOCK: Cannot log PTP "
            "for unverified customer."
        )

        return False

    if context.ptp_amount is None:
        return False

    if context.ptp_date is None:
        return False

    record = {
        "call_id": context.call_id,
        "customer_reference": context.customer_reference,
        "amount": context.ptp_amount,
        "date": context.ptp_date,
        "status": "PROMISED"
    }

    PTP_DATABASE.append(record)

    context.disposition = "PTP_COMMITTED"

    log_event(
        context,
        "PTP_LOGGED"
    )

    print("\nPTP successfully logged:")
    print(record)

    return True


# ============================================================
# PAYMENT LINK
# ============================================================

def send_payment_link(
    context: CallContext
) -> bool:

    if context.auth_state != AuthState.VERIFIED:

        print(
            "SECURITY BLOCK: Payment link cannot be generated "
            "before authentication."
        )

        log_event(
            context,
            "PAYMENT_LINK_BLOCKED_NOT_VERIFIED"
        )

        return False

    print(
        "\nMock payment link generated."
    )

    print(
        f"https://pay.kapture.finance/{context.customer_reference}"
    )

    context.disposition = "PAYMENT_LINK_SENT"

    log_event(
        context,
        "PAYMENT_LINK_SENT"
    )

    return True


# ============================================================
# ESCALATION
# ============================================================

def escalate_to_agent(
    context: CallContext,
    reason: str
):

    context.current_state = CallState.ESCALATION
    context.disposition = reason

    log_event(
        context,
        f"ESCALATED:{reason}"
    )

    print(
        f"\nEscalating to human agent."
    )

    print(
        f"Reason: {reason}"
    )


# ============================================================
# DISPOSITION
# ============================================================

def mark_disposition(
    context: CallContext,
    disposition: str
):

    context.disposition = disposition

    log_event(
        context,
        f"DISPOSITION:{disposition}"
    )

    print(
        f"\nFinal disposition: {disposition}"
    )


# ============================================================
# FINAL CONTEXT
# ============================================================

def print_final_context(
    context: CallContext
):

    print("\n" + "=" * 70)
    print("FINAL CALL CONTEXT")
    print("=" * 70)

    print(
        f"Call ID: {context.call_id}"
    )

    print(
        f"Customer Reference: {context.customer_reference}"
    )

    print(
        f"Current State: {context.current_state.value}"
    )

    print(
        f"Authentication: {context.auth_state.value}"
    )

    print(
        f"Intent: {context.current_intent}"
    )

    print(
        f"PTP Amount: {context.ptp_amount}"
    )

    print(
        f"PTP Date: {context.ptp_date}"
    )

    print(
        f"Disposition: {context.disposition}"
    )

    print("\nEvent Log:")

    for event in context.events:
        print(
            f"  - {event}"
        )


# ============================================================
# TEST 1
# NORMAL SUCCESSFUL PTP
# ============================================================

def test_successful_ptp():

    print("\n\n")
    print("#" * 70)
    print("TEST 1 - SUCCESSFUL PROMISE TO PAY")
    print("#" * 70)

    context = initialize_call(
        call_id="CALL-001",
        customer_reference="CUS-1001",
        phone_number="+91XXXXXXXXXX",
        campaign_id="COLLECTIONS-DEMO"
    )

    if not check_contact_eligibility(context):
        return

    introduction(context)

    # Correct authentication
    verify_customer(
        context,
        provided_last4="1234"
    )

    # Account disclosure AFTER verification
    get_account_details(context)

    # Customer promises to pay
    handle_intent(
        context,
        "Yes, I will pay tomorrow."
    )

    # Extract entities
    text = "I will pay ₹8499 tomorrow."

    amount = extract_amount(text)
    payment_date = extract_payment_date(text)

    print(
        f"\nExtracted amount: ₹{amount}"
    )

    print(
        f"Extracted date: {payment_date}"
    )

    result = validate_ptp(
        context,
        amount=amount,
        payment_date=payment_date
    )

    print(
        f"\nPTP valid: {result.valid}"
    )

    print(
        f"Reason: {result.reason}"
    )

    if result.valid:

        log_promise_to_pay(context)

        send_payment_link(context)

        mark_disposition(
            context,
            "PTP_COMMITTED"
        )

    print_final_context(context)


# ============================================================
# TEST 2
# ALREADY PAID
# ============================================================

def test_already_paid():

    print("\n\n")
    print("#" * 70)
    print("TEST 2 - ALREADY PAID EDGE CASE")
    print("#" * 70)

    context = initialize_call(
        call_id="CALL-002",
        customer_reference="CUS-1001",
        phone_number="+91XXXXXXXXXX",
        campaign_id="COLLECTIONS-DEMO"
    )

    if not check_contact_eligibility(context):
        return

    introduction(context)

    verify_customer(
        context,
        provided_last4="1234"
    )

    get_account_details(context)

    handle_intent(
        context,
        "I already paid this EMI."
    )

    print_final_context(context)


# ============================================================
# TEST 3
# DO NOT CALL
# ============================================================

def test_dnc():

    print("\n\n")
    print("#" * 70)
    print("TEST 3 - DO NOT CALL")
    print("#" * 70)

    context = initialize_call(
        call_id="CALL-003",
        customer_reference="CUS-DNC-001",
        phone_number="+91XXXXXXXXXX",
        campaign_id="COLLECTIONS-DEMO"
    )

    eligible = check_contact_eligibility(context)

    if not eligible:

        print(
            "\nDNC protection worked."
        )

    print_final_context(context)


# ============================================================
# TEST 4
# DISPUTE
# ============================================================

def test_dispute():

    print("\n\n")
    print("#" * 70)
    print("TEST 4 - DISPUTE")
    print("#" * 70)

    context = initialize_call(
        call_id="CALL-004",
        customer_reference="CUS-1001",
        phone_number="+91XXXXXXXXXX",
        campaign_id="COLLECTIONS-DEMO"
    )

    if not check_contact_eligibility(context):
        return

    introduction(context)

    verify_customer(
        context,
        provided_last4="1234"
    )

    get_account_details(context)

    handle_intent(
        context,
        "I dispute this amount. The amount is incorrect."
    )

    print_final_context(context)


# ============================================================
# TEST 5
# PRE-AUTHORIZATION SECURITY TEST
# ============================================================

def test_pre_auth_security():

    print("\n\n")
    print("#" * 70)
    print("TEST 5 - PRE-AUTH SECURITY")
    print("#" * 70)

    context = initialize_call(
        call_id="CALL-005",
        customer_reference="CUS-1001",
        phone_number="+91XXXXXXXXXX",
        campaign_id="COLLECTIONS-DEMO"
    )

    # Attempt to access debt before authentication
    result = get_account_details(context)

    if result is None:

        print(
            "\n[PASS] PRE-AUTH SECURITY BLOCK"
        )

    else:

        print(
            "\n[FAIL] SECURITY VULNERABILITY"
        )

    print_final_context(context)


# ============================================================
# TEST 6
# AUTHENTICATION FAILURE
# ============================================================

def test_auth_failure():

    print("\n\n")
    print("#" * 70)
    print("TEST 6 - AUTHENTICATION FAILURE")
    print("#" * 70)

    context = initialize_call(
        call_id="CALL-006",
        customer_reference="CUS-1001",
        phone_number="+91XXXXXXXXXX",
        campaign_id="COLLECTIONS-DEMO"
    )

    if not check_contact_eligibility(context):
        return

    introduction(context)

    verify_customer(
        context,
        provided_last4="9999"
    )

    verify_customer(
        context,
        provided_last4="8888"
    )

    print_final_context(context)


# ============================================================
# TEST 7
# WRONG PERSON
# ============================================================

def test_wrong_person():

    print("\n\n")
    print("#" * 70)
    print("TEST 7 - WRONG PERSON")
    print("#" * 70)

    context = initialize_call(
        call_id="CALL-007",
        customer_reference="CUS-1001",
        phone_number="+91XXXXXXXXXX",
        campaign_id="COLLECTIONS-DEMO"
    )

    if not check_contact_eligibility(context):
        return

    introduction(context)

    # In a real call the person answering can say they are not Rahul.
    # No debt details are disclosed.
    context.current_state = CallState.INTENT_DETECTION

    handle_intent(
        context,
        "You have the wrong person."
    )

    print_final_context(context)


# ============================================================
# TEST RUNNER
# ============================================================

def run_all_tests():

    print("\n")
    print("=" * 70)
    print("KAPTURE FINANCE - MAYA COLLECTIONS BACKEND")
    print("STATE MACHINE + SECURITY TEST SUITE")
    print("=" * 70)

    test_successful_ptp()

    test_already_paid()

    test_dnc()

    test_dispute()

    test_pre_auth_security()

    test_auth_failure()

    test_wrong_person()

    print("\n")
    print("=" * 70)
    print("ALL DEMONSTRATION TESTS COMPLETED")
    print("=" * 70)

    print(
        f"\nPTP records created: {len(PTP_DATABASE)}"
    )

    for record in PTP_DATABASE:
        print(record)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    run_all_tests()