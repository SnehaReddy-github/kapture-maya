import streamlit as st
import requests

st.set_page_config(
    page_title="Kapture Finance - Maya",
    page_icon="💳",
    layout="wide"
)

BACKEND_URL = "http://127.0.0.1:5000"

st.title("💳 Kapture Finance - Maya")
st.subheader("AI Collections Assistant")

st.divider()

# --------------------------------------------------
# BACKEND STATUS
# --------------------------------------------------

st.header("Backend Status")

try:
    response = requests.get(
        f"{BACKEND_URL}/",
        timeout=5
    )

    if response.status_code == 200:
        data = response.json()
        st.success(
            f"Backend Online — Version {data.get('version', 'unknown')}"
        )
    else:
        st.error("Backend returned an error.")

except requests.exceptions.RequestException:
    st.error(
        "Backend is not reachable. "
        "Make sure Flask is running on port 5000."
    )

st.divider()

# --------------------------------------------------
# CUSTOMER VERIFICATION
# --------------------------------------------------

st.header("🔐 Customer Verification")

customer_reference = st.text_input(
    "Customer Reference",
    placeholder="Example: CUS-1001"
)

verification_value = st.text_input(
    "Verification Value",
    placeholder="Example: 1001"
)

if st.button("Verify Customer"):

    if not customer_reference:
        st.warning("Enter customer reference.")
    elif not verification_value:
        st.warning("Enter verification value.")
    else:

        try:
            response = requests.post(
                f"{BACKEND_URL}/verify-customer",
                json={
                    "customer_reference": customer_reference,
                    "verification_value": verification_value
                },
                timeout=10
            )

            result = response.json()

            if result.get("verified"):
                st.success("Customer successfully verified.")

                st.session_state["customer_reference"] = (
                    customer_reference
                )
                st.session_state["verified"] = True

                st.json(result)

            elif result.get("blocked"):
                st.error("Customer is blocked / Do Not Call.")

            else:
                st.error(
                    f"Verification failed: "
                    f"{result.get('reason', 'Unknown reason')}"
                )

        except requests.exceptions.RequestException as e:
            st.error(f"Backend connection error: {e}")


st.divider()

# --------------------------------------------------
# ACCOUNT DETAILS
# --------------------------------------------------

st.header("📋 Account Details")

if st.button("Get Account Details"):

    if not customer_reference:
        st.warning("Enter customer reference first.")

    else:

        try:
            response = requests.post(
                f"{BACKEND_URL}/get-account-details",
                json={
                    "customer_reference": customer_reference
                },
                timeout=10
            )

            result = response.json()

            if result.get("success"):
                st.success("Account details retrieved.")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "Customer",
                        result.get("customer_name", "-")
                    )

                with col2:
                    st.metric(
                        "Overdue Amount",
                        f"₹{result.get('overdue_amount', 0):,}"
                    )

                with col3:
                    st.metric(
                        "Days Past Due",
                        result.get("days_past_due", 0)
                    )

                st.json(result)

            else:
                st.error(
                    result.get(
                        "message",
                        result.get("error", "Request failed")
                    )
                )

        except requests.exceptions.RequestException as e:
            st.error(f"Backend connection error: {e}")


st.divider()

# --------------------------------------------------
# PROMISE TO PAY
# --------------------------------------------------

st.header("💰 Promise to Pay")

ptp_amount = st.number_input(
    "Promise Amount",
    min_value=0,
    step=100,
    value=0
)

payment_date = st.date_input(
    "Payment Date"
)

if st.button("Log Promise to Pay"):

    if not customer_reference:
        st.warning("Enter customer reference.")

    elif ptp_amount <= 0:
        st.warning("Enter a valid amount.")

    else:

        try:
            response = requests.post(
                f"{BACKEND_URL}/log-promise-to-pay",
                json={
                    "customer_reference": customer_reference,
                    "amount": ptp_amount,
                    "payment_date": str(payment_date)
                },
                timeout=10
            )

            result = response.json()

            if result.get("success"):
                st.success(
                    "Promise to Pay recorded successfully."
                )
                st.json(result)

            else:
                st.error(
                    result.get(
                        "error",
                        "Unable to record Promise to Pay."
                    )
                )

        except requests.exceptions.RequestException as e:
            st.error(f"Backend connection error: {e}")


st.divider()

# --------------------------------------------------
# PAYMENT LINK
# --------------------------------------------------

st.header("🔗 Send Payment Link")

channel = st.selectbox(
    "Payment Channel",
    ["SMS", "WHATSAPP"]
)

if st.button("Generate Payment Link"):

    if not customer_reference:
        st.warning("Enter customer reference.")

    else:

        try:
            response = requests.post(
                f"{BACKEND_URL}/send-payment-link",
                json={
                    "customer_reference": customer_reference,
                    "channel": channel
                },
                timeout=10
            )

            result = response.json()

            if result.get("success"):

                st.success(
                    f"Payment link prepared for {channel}"
                )

                st.code(
                    result.get("payment_link", ""),
                    language="text"
                )

            else:
                st.error(
                    result.get(
                        "error",
                        "Unable to generate payment link."
                    )
                )

        except requests.exceptions.RequestException as e:
            st.error(f"Backend connection error: {e}")


st.divider()

# --------------------------------------------------
# ESCALATION
# --------------------------------------------------

st.header("👤 Human Escalation")

reason = st.text_input(
    "Reason for escalation",
    value="Customer requested human assistance"
)

if st.button("Escalate to Agent"):

    if not customer_reference:
        st.warning("Enter customer reference.")

    else:

        try:
            response = requests.post(
                f"{BACKEND_URL}/escalate-to-agent",
                json={
                    "customer_reference": customer_reference,
                    "reason": reason
                },
                timeout=10
            )

            result = response.json()

            if result.get("success"):
                st.success(
                    "Customer successfully routed to "
                    "a collections specialist."
                )
                st.json(result)

            else:
                st.error(
                    result.get(
                        "error",
                        "Escalation failed."
                    )
                )

        except requests.exceptions.RequestException as e:
            st.error(f"Backend connection error: {e}")


st.divider()

# --------------------------------------------------
# DISPOSITION
# --------------------------------------------------

st.header("📝 Call Disposition")

disposition = st.selectbox(
    "Disposition",
    [
        "PROMISE_TO_PAY",
        "PAYMENT_MADE",
        "CALLBACK_REQUESTED",
        "CUSTOMER_REFUSED",
        "WRONG_NUMBER",
        "NO_RESPONSE",
        "ESCALATED"
    ]
)

notes = st.text_area(
    "Notes"
)

if st.button("Save Disposition"):

    if not customer_reference:
        st.warning("Enter customer reference.")

    else:

        try:
            response = requests.post(
                f"{BACKEND_URL}/mark-disposition",
                json={
                    "customer_reference": customer_reference,
                    "disposition": disposition,
                    "notes": notes
                },
                timeout=10
            )

            result = response.json()

            if result.get("success"):
                st.success(
                    "Call disposition recorded."
                )
                st.json(result)

            else:
                st.error(
                    result.get(
                        "error",
                        "Unable to save disposition."
                    )
                )

        except requests.exceptions.RequestException as e:
            st.error(f"Backend connection error: {e}")


st.divider()

st.caption(
    "Kapture Finance — Maya Collections API Demo"
)