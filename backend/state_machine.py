from enum import Enum


class CallState(str, Enum):
    NEW_CALL = "NEW_CALL"
    DISCLOSURE = "DISCLOSURE"
    AUTHENTICATION = "AUTHENTICATION"
    VERIFIED = "VERIFIED"
    INTENT_CAPTURE = "INTENT_CAPTURE"
    RESOLUTION = "RESOLUTION"
    ESCALATION = "ESCALATION"
    DISPOSITION = "DISPOSITION"
    ENDED = "ENDED"


class CallContext:
    def __init__(self):
        self.state = CallState.NEW_CALL

        # Security-sensitive flag
        self.customer_verified = False

        # Customer information
        self.customer_reference = None
        self.customer_name = None

        # Collection information
        self.overdue_amount = None
        self.loan_type = None
        self.days_past_due = None

        # Conversation information
        self.intent = None
        self.ptp_amount = None
        self.ptp_date = None

        # Final outcome
        self.disposition = None
        self.escalation_reason = None

        # Call metadata
        self.language = "EN"
        self.opted_out = False

    def transition(self, new_state):
        """
        Controlled state transition.
        """

        allowed_transitions = {
            CallState.NEW_CALL: [
                CallState.DISCLOSURE
            ],

            CallState.DISCLOSURE: [
                CallState.AUTHENTICATION,
                CallState.ENDED
            ],

            CallState.AUTHENTICATION: [
                CallState.VERIFIED,
                CallState.ENDED,
                CallState.ESCALATION
            ],

            CallState.VERIFIED: [
                CallState.INTENT_CAPTURE,
                CallState.ESCALATION,
                CallState.ENDED
            ],

            CallState.INTENT_CAPTURE: [
                CallState.RESOLUTION,
                CallState.ESCALATION,
                CallState.ENDED
            ],

            CallState.RESOLUTION: [
                CallState.DISPOSITION,
                CallState.ESCALATION,
                CallState.ENDED
            ],

            CallState.ESCALATION: [
                CallState.DISPOSITION,
                CallState.ENDED
            ],

            CallState.DISPOSITION: [
                CallState.ENDED
            ],

            CallState.ENDED: []
        }

        if new_state not in allowed_transitions[self.state]:
            raise ValueError(
                f"Invalid state transition: "
                f"{self.state} -> {new_state}"
            )

        self.state = new_state

    def can_disclose_debt(self):
        """
        Debt information may ONLY be disclosed after
        successful customer verification.
        """

        return (
            self.state == CallState.VERIFIED
            and self.customer_verified is True
        )

    def mark_verified(self, customer_data):
        """
        Mark customer as verified and store permitted
        account information.
        """

        if self.state != CallState.AUTHENTICATION:
            raise ValueError(
                "Customer verification can only happen "
                "during AUTHENTICATION state."
            )

        self.customer_verified = True

        self.customer_reference = customer_data.get(
            "customer_reference"
        )

        self.customer_name = customer_data.get(
            "customer_name"
        )

        self.overdue_amount = customer_data.get(
            "overdue_amount"
        )

        self.loan_type = customer_data.get(
            "loan_type"
        )

        self.days_past_due = customer_data.get(
            "days_past_due"
        )

        self.transition(CallState.VERIFIED)

    def set_intent(self, intent):
        """
        Store the detected customer intent.
        """

        if self.state != CallState.INTENT_CAPTURE:
            raise ValueError(
                "Intent can only be captured "
                "during INTENT_CAPTURE state."
            )

        self.intent = intent

    def end_call(self, disposition=None):
        """
        Safely terminate the conversation.
        """

        self.disposition = disposition
        self.state = CallState.ENDED