import pytest

from backend.maya_orchestrator import MayaOrchestrator


# ============================================================
# SECURITY TEST 1
# UNVERIFIED CALLER CANNOT ACCESS ACCOUNT DETAILS
# ============================================================

def test_unverified_customer_cannot_access_debt():

    maya = MayaOrchestrator()

    maya.start_call()
    maya.begin_authentication()

    with pytest.raises(PermissionError):
        maya.get_verified_account_details()


# ============================================================
# SECURITY TEST 2
# FAILED AUTHENTICATION CANNOT ACCESS DEBT
# ============================================================

def test_failed_authentication_cannot_access_debt():

    maya = MayaOrchestrator()

    maya.start_call()
    maya.begin_authentication()

    result = maya.verification_failed()

    assert result["verified"] is False
    assert result["can_disclose_debt"] is False

    with pytest.raises(PermissionError):
        maya.get_verified_account_details()


# ============================================================
# SECURITY TEST 3
# PAYMENT LINK CANNOT BE GENERATED BEFORE AUTH
# ============================================================

def test_unverified_customer_cannot_generate_payment_link():

    maya = MayaOrchestrator()

    maya.start_call()
    maya.begin_authentication()

    with pytest.raises(PermissionError):
        maya.create_payment_link(8499)


# ============================================================
# SECURITY TEST 4
# PTP CANNOT BE CREATED BEFORE AUTH
# ============================================================

def test_unverified_customer_cannot_create_ptp():

    maya = MayaOrchestrator()

    maya.start_call()
    maya.begin_authentication()

    with pytest.raises(PermissionError):
        maya.create_promise_to_pay(
            amount=8499,
            payment_date="2026-08-15",
        )


# ============================================================
# SECURITY TEST 5
# VERIFIED CUSTOMER CAN ACCESS ACCOUNT DETAILS
# ============================================================

def test_verified_customer_can_access_account():

    maya = MayaOrchestrator()

    maya.start_call()
    maya.begin_authentication()

    maya.verification_success({
        "customer_reference": "CUS-1001",
        "customer_name": "Rahul Sharma",
    })

    result = maya.get_verified_account_details()

    assert result["success"] is True
    assert result["overdue_amount"] == 8499
    assert result["days_past_due"] == 12


# ============================================================
# SECURITY TEST 6
# VERIFICATION FAILURE NEVER ENABLES DISCLOSURE
# ============================================================

def test_failed_verification_never_enables_disclosure():

    maya = MayaOrchestrator()

    maya.start_call()
    maya.begin_authentication()

    result = maya.verification_failed()

    assert result["can_disclose_debt"] is False
    assert maya.debt_disclosure_allowed() is False