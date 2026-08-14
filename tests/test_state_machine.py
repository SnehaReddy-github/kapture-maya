from backend.state_machine import CallContext, CallState


def test_new_call_starts_correctly():
    context = CallContext()

    assert context.state == CallState.NEW_CALL
    assert context.customer_verified is False


def test_debt_cannot_be_disclosed_before_verification():
    context = CallContext()

    assert context.can_disclose_debt() is False


def test_valid_authentication_flow():
    context = CallContext()

    context.transition(CallState.DISCLOSURE)
    context.transition(CallState.AUTHENTICATION)

    context.mark_verified({
        "customer_reference": "CUS-1001",
        "customer_name": "Rahul Sharma",
        "overdue_amount": 8499,
        "loan_type": "Personal Loan",
        "days_past_due": 12
    })

    assert context.state == CallState.VERIFIED
    assert context.customer_verified is True
    assert context.can_disclose_debt() is True


def test_invalid_state_transition_is_blocked():
    context = CallContext()

    try:
        context.transition(CallState.VERIFIED)
        assert False, "Invalid transition was allowed"
    except ValueError:
        assert True


def test_unverified_customer_cannot_be_marked_verified_from_wrong_state():
    context = CallContext()

    try:
        context.mark_verified({
            "customer_reference": "CUS-1001",
            "customer_name": "Rahul Sharma"
        })

        assert False, "Verification bypass was allowed"

    except ValueError:
        assert True