import sys
from pathlib import Path

import pytest

# Make sure Python can find the backend folder
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from backend.api_server import app


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


# ============================================================
# 1. HEALTH CHECK
# ============================================================

def test_health_check(client):
    response = client.get("/")

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "online"


# ============================================================
# 2. SUCCESSFUL CUSTOMER VERIFICATION
# ============================================================

def test_verify_customer_success(client):
    response = client.post(
        "/verify-customer",
        json={
            "customer_reference": "CUS-1001",
            "verification_value": "1001"
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert data["verified"] is True


# ============================================================
# 3. FAILED CUSTOMER VERIFICATION
# ============================================================

def test_verify_customer_failure(client):
    response = client.post(
        "/verify-customer",
        json={
            "customer_reference": "CUS-1001",
            "verification_value": "9999"
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert data["verified"] is False
    assert data["reason"] == "VERIFICATION_FAILED"


# ============================================================
# 4. UNKNOWN CUSTOMER
# ============================================================

def test_unknown_customer(client):
    response = client.post(
        "/verify-customer",
        json={
            "customer_reference": "CUS-9999",
            "verification_value": "9999"
        }
    )

    data = response.get_json()

    # Unknown customers must never be verified
    assert data.get("verified") is False


# ============================================================
# 5. PROMISE TO PAY
# ============================================================

def test_promise_to_pay(client):
    response = client.post(
        "/log-promise-to-pay",
        json={
            "customer_reference": "CUS-1001",
            "amount": 8499,
            "payment_date": "2026-08-15"
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["ptp"] is not None
    assert data["ptp"]["amount"] == 8499
    assert data["ptp"]["customer_reference"] == "CUS-1001"
    assert data["ptp"]["payment_date"] == "2026-08-15"
    assert data["ptp"]["status"] == "PROMISED"


# ============================================================
# 6. PAYMENT LINK
# ============================================================

def test_payment_link(client):
    response = client.post(
        "/send-payment-link",
        json={
            "customer_reference": "CUS-1001",
            "amount": 8499
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert data["channel"] == "SMS"
    assert data["payment_link"] is not None


# ============================================================
# 7. ESCALATION
# ============================================================

def test_escalation(client):
    response = client.post(
        "/escalate-to-agent",
        json={
            "customer_reference": "CUS-1001",
            "reason": "Customer requested to speak with an agent"
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert data["escalated"] is True


# ============================================================
# 8. DISPOSITION
# ============================================================

def test_disposition(client):
    response = client.post(
        "/mark-disposition",
        json={
            "customer_reference": "CUS-1001",
            "disposition": "PTP",
            "notes": "Customer committed to pay overdue amount"
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["disposition"] is not None