from backend.maya_orchestrator import MayaOrchestrator
from backend.state_machine import CallState


def test_call_starts_with_disclosure():
    maya = MayaOrchestrator()

    result = maya.start_call()

    assert result["state"] == CallState.DISCLOSURE.value
    assert result["action"] == "DISCLOSE_IDENTITY_AND_PURPOSE"


def test_authentication_is_required_before_debt_disclosure():
    maya = MayaOrchestrator()

    maya.start_call()
    maya.begin_authentication()

    assert maya.debt_disclosure_allowed() is False


def test_verified_customer_can_proceed():
    maya = MayaOrchestrator()

    maya.start_call()
    maya.begin_authentication()

    result = maya.verification_success({
        "customer_reference": "CUS-1001",
        "customer_name": "Rahul Sharma",
        "overdue_amount": 8499,
        "loan_type": "Personal Loan",
        "days_past_due": 12
    })

    assert result["verified"] is True
    assert result["can_disclose_debt"] is True


def test_failed_authentication_ends_without_disclosure():
    maya = MayaOrchestrator()

    maya.start_call()
    maya.begin_authentication()

    result = maya.verification_failed()

    assert result["verified"] is False
    assert result["can_disclose_debt"] is False
    assert result["action"] == "END_WITHOUT_DEBT_DISCLOSURE"


def test_unverified_customer_cannot_enter_intent_capture():
    maya = MayaOrchestrator()

    maya.start_call()
    maya.begin_authentication()

    try:
        maya.begin_intent_capture()
        assert False, "Unverified customer reached intent capture"
    except PermissionError:
        assert True


def test_verified_customer_can_enter_intent_capture():
    maya = MayaOrchestrator()

    maya.start_call()
    maya.begin_authentication()

    maya.verification_success({
        "customer_reference": "CUS-1001",
        "customer_name": "Rahul Sharma",
        "overdue_amount": 8499,
        "loan_type": "Personal Loan",
        "days_past_due": 12
    })

    result = maya.begin_intent_capture()

    assert result["state"] == CallState.INTENT_CAPTURE.value


def test_dispute_can_be_escalated():
    maya = MayaOrchestrator()

    maya.start_call()
    maya.begin_authentication()

    maya.verification_success({
        "customer_reference": "CUS-1001",
        "customer_name": "Rahul Sharma",
        "overdue_amount": 8499,
        "loan_type": "Personal Loan",
        "days_past_due": 12
    })

    maya.begin_intent_capture()
    maya.capture_intent("DISPUTE")
    maya.begin_resolution()

    result = maya.escalate("Customer disputes overdue amount")

    assert result["state"] == CallState.ESCALATION.value
    assert result["reason"] == "Customer disputes overdue amount"


def test_ptp_flow_can_reach_disposition():
    maya = MayaOrchestrator()

    maya.start_call()
    maya.begin_authentication()

    maya.verification_success({
        "customer_reference": "CUS-1001",
        "customer_name": "Rahul Sharma",
        "overdue_amount": 8499,
        "loan_type": "Personal Loan",
        "days_past_due": 12
    })

    maya.begin_intent_capture()
    maya.capture_intent("WILL_PAY")
    maya.begin_resolution()

    result = maya.record_disposition("PTP")

    assert result["state"] == CallState.DISPOSITION.value
    assert result["disposition"] == "PTP"