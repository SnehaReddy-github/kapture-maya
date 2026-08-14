from .state_machine import CallContext, CallState
from .tools import (
    verify_customer,
    get_account_details,
    log_promise_to_pay,
    send_payment_link,
)


class MayaOrchestrator:
    """
    Deterministic orchestration layer for Maya.

    The LLM may understand customer speech and identify intent,
    but it cannot decide whether sensitive account information
    may be disclosed.

    The state machine controls that decision.
    """

    def __init__(self):
        self.context = CallContext()

    # ========================================================
    # CALL START
    # ========================================================

    def start_call(self):
        if self.context.state != CallState.NEW_CALL:
            raise ValueError("Call has already started.")

        self.context.transition(CallState.DISCLOSURE)

        return {
            "state": self.context.state.value,
            "action": "DISCLOSE_IDENTITY_AND_PURPOSE",
            "message": (
                "Hello, this is Maya calling on behalf of "
                "Kapture Finance. This call is regarding "
                "your loan account."
            ),
        }

    # ========================================================
    # AUTHENTICATION
    # ========================================================

    def begin_authentication(self):
        if self.context.state != CallState.DISCLOSURE:
            raise ValueError(
                "Authentication cannot begin from the current state."
            )

        self.context.transition(CallState.AUTHENTICATION)

        return {
            "state": self.context.state.value,
            "action": "REQUEST_AUTHENTICATION",
        }

    # ========================================================
    # VERIFY CUSTOMER USING TOOL
    # ========================================================

    def verify_customer_identity(
        self,
        customer_reference,
        verification_value,
    ):
        """
        Calls the verification tool.

        No debt information is returned before verification.
        """

        if self.context.state != CallState.AUTHENTICATION:
            raise PermissionError(
                "Customer verification is only allowed "
                "during AUTHENTICATION."
            )

        result = verify_customer(
            customer_reference=customer_reference,
            verification_value=verification_value,
        )

        if not result.success:
            self.context.transition(CallState.ENDED)

            return {
                "success": False,
                "verified": False,
                "state": self.context.state.value,
                "reason": "VERIFICATION_FAILED",
                "can_disclose_debt": False,
            }

        customer_data = {
            "customer_reference": customer_reference,
            "customer_name": result.verified_name,
        }

        self.context.mark_verified(customer_data)

        return {
            "success": True,
            "verified": True,
            "state": self.context.state.value,
            "customer_name": result.verified_name,
            "can_disclose_debt": self.context.can_disclose_debt(),
        }

    # ========================================================
    # VERIFICATION SUCCESS HELPER
    # ========================================================

    def verification_success(self, customer_data):
        """
        Record a successful authentication result.

        This is a deterministic state transition helper.
        """

        if self.context.state != CallState.AUTHENTICATION:
            raise ValueError(
                "Verification success can only occur "
                "during AUTHENTICATION."
            )

        if not customer_data.get("customer_reference"):
            raise ValueError(
                "Customer reference is required."
            )

        if not customer_data.get("customer_name"):
            raise ValueError(
                "Verified customer name is required."
            )

        self.context.mark_verified({
            "customer_reference": customer_data["customer_reference"],
            "customer_name": customer_data["customer_name"],
        })

        return {
            "success": True,
            "verified": True,
            "state": self.context.state.value,
            "customer_reference": customer_data["customer_reference"],
            "customer_name": customer_data["customer_name"],
            "can_disclose_debt": self.context.can_disclose_debt(),
        }

    # ========================================================
    # VERIFICATION FAILURE HELPER
    # ========================================================

    def verification_failed(self):
        """
        Handle failed authentication.

        No debt information is disclosed.
        """

        if self.context.state != CallState.AUTHENTICATION:
            raise ValueError(
                "Verification failure can only occur "
                "during AUTHENTICATION."
            )

        self.context.transition(CallState.ENDED)

        return {
        "success": False,
        "verified": False,
        "state": self.context.state.value,
        "reason": "VERIFICATION_FAILED",
        "action": "END_WITHOUT_DEBT_DISCLOSURE",
        "can_disclose_debt": False,
    }

    # ========================================================
    # GET ACCOUNT DETAILS
    # ========================================================

    def get_verified_account_details(self):
        """
        SECURITY GATE:

        Account/debt information can only be retrieved after
        successful customer verification.
        """

        if not self.context.can_disclose_debt():
            raise PermissionError(
                "Account details cannot be retrieved before "
                "successful customer verification."
            )

        result = get_account_details(
            customer_reference=self.context.customer_reference
        )

        if not result.success:
            return {
                "success": False,
                "state": self.context.state.value,
                "message": result.message,
            }

        self.context.overdue_amount = result.overdue_amount
        self.context.loan_type = result.loan_type
        self.context.days_past_due = result.days_past_due

        return {
            "success": True,
            "state": self.context.state.value,
            "loan_type": result.loan_type,
            "overdue_amount": result.overdue_amount,
            "days_past_due": result.days_past_due,
            "payment_status": result.payment_status,
        }

    # ========================================================
    # BEGIN INTENT CAPTURE
    # ========================================================

    def begin_intent_capture(self):
        if not self.context.can_disclose_debt():
            raise PermissionError(
                "Debt must be verified before intent capture."
            )

        self.context.transition(CallState.INTENT_CAPTURE)

        return {
            "state": self.context.state.value,
            "action": "CAPTURE_CUSTOMER_INTENT",
        }

    # ========================================================
    # CAPTURE INTENT
    # ========================================================

    def capture_intent(self, intent):
        if self.context.state != CallState.INTENT_CAPTURE:
            raise ValueError(
                "Intent can only be captured during "
                "INTENT_CAPTURE."
            )

        self.context.set_intent(intent)

        return {
            "state": self.context.state.value,
            "intent": intent,
        }

    # ========================================================
    # BEGIN RESOLUTION
    # ========================================================

    def begin_resolution(self):
        if self.context.state != CallState.INTENT_CAPTURE:
            raise ValueError(
                "Resolution cannot begin from the current state."
            )

        self.context.transition(CallState.RESOLUTION)

        return {
            "state": self.context.state.value,
            "action": "RESOLVE_COLLECTION_INTENT",
        }

    # ========================================================
    # LOG PROMISE TO PAY
    # ========================================================

    def create_promise_to_pay(
        self,
        amount,
        payment_date,
    ):
        """
        Create PTP only after verification and during
        resolution.
        """

        if not self.context.can_disclose_debt():
            raise PermissionError(
                "PTP cannot be created before customer verification."
            )

        if self.context.state != CallState.RESOLUTION:
            raise ValueError(
                "PTP can only be created during RESOLUTION."
            )

        result = log_promise_to_pay(
            customer_reference=self.context.customer_reference,
            amount=amount,
            payment_date=payment_date,
        )

        if not result.success:
            return {
                "success": False,
                "state": self.context.state.value,
                "message": result.message,
            }

        self.context.ptp_amount = result.amount
        self.context.ptp_date = result.payment_date

        return {
            "success": True,
            "state": self.context.state.value,
            "amount": result.amount,
            "payment_date": result.payment_date,
            "message": result.message,
        }

    # ========================================================
    # SEND PAYMENT LINK
    # ========================================================

    def create_payment_link(self, amount):
        """
        Payment link can only be generated for a verified
        customer.
        """

        if not self.context.can_disclose_debt():
            raise PermissionError(
                "Payment link cannot be generated before "
                "customer verification."
            )

        if self.context.state != CallState.RESOLUTION:
            raise ValueError(
                "Payment link can only be generated during "
                "RESOLUTION."
            )

        result = send_payment_link(
            customer_reference=self.context.customer_reference,
            amount=amount,
        )

        if not result.success:
            return {
                "success": False,
                "state": self.context.state.value,
                "message": result.message,
            }

        return {
            "success": True,
            "state": self.context.state.value,
            "payment_link": result.payment_link,
            "amount": result.amount,
            "message": result.message,
        }

    # ========================================================
    # ESCALATION
    # ========================================================

    def escalate(self, reason):
        if self.context.state == CallState.ENDED:
            raise ValueError("Cannot escalate an ended call.")

        self.context.escalation_reason = reason

        self.context.transition(CallState.ESCALATION)

        return {
            "state": self.context.state.value,
            "action": "ESCALATE_TO_HUMAN",
            "reason": reason,
        }

    # ========================================================
    # DISPOSITION
    # ========================================================

    def record_disposition(self, disposition):
        if self.context.state not in (
            CallState.RESOLUTION,
            CallState.ESCALATION,
        ):
            raise ValueError(
                "Disposition cannot be recorded from "
                "the current state."
            )

        self.context.disposition = disposition

        self.context.transition(CallState.DISPOSITION)

        return {
            "state": self.context.state.value,
            "disposition": disposition,
        }

    # ========================================================
    # END CALL
    # ========================================================

    def end_call(self, disposition=None):
        if self.context.state == CallState.ENDED:
            return {
                "state": CallState.ENDED.value,
                "disposition": self.context.disposition,
            }

        self.context.end_call(disposition)

        return {
            "state": CallState.ENDED.value,
            "disposition": disposition,
        }

    # ========================================================
    # SECURITY CHECK
    # ========================================================

    def debt_disclosure_allowed(self):
        """
        Single security gate for sensitive debt information.
        """

        return self.context.can_disclose_debt()