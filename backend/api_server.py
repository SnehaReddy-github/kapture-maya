from flask import Flask, request, jsonify
from datetime import datetime, timezone

app = Flask(__name__)


# ============================================================
# MOCK CUSTOMER DATABASE
# ============================================================

CUSTOMERS = {
    "CUS-1001": {
        "customer_name": "Rahul Sharma",
        "phone": "+919999999999",
        "loan_type": "Personal Loan",
        "overdue_amount": 8499,
        "days_past_due": 12,
        "status": "OVERDUE",
        "already_paid": False,
        "do_not_call": False,
    },

    "CUS-PAID-001": {
        "customer_name": "Amit Kumar",
        "phone": "+918888888888",
        "loan_type": "Personal Loan",
        "overdue_amount": 6500,
        "days_past_due": 5,
        "status": "PAID",
        "already_paid": True,
        "do_not_call": False,
    },

    "CUS-DNC-001": {
        "customer_name": "Priya Reddy",
        "phone": "+917777777777",
        "loan_type": "Personal Loan",
        "overdue_amount": 9200,
        "days_past_due": 15,
        "status": "OVERDUE",
        "already_paid": False,
        "do_not_call": True,
    },
}


# ============================================================
# MOCK DATABASES
# ============================================================

PTP_RECORDS = []
PAYMENT_LINKS = []
DISPOSITIONS = []
ESCALATIONS = []


# ============================================================
# HELPER
# ============================================================

def utc_now():
    """
    Return timezone-aware UTC timestamp.
    Avoids deprecated datetime.utcnow().
    """
    return datetime.now(timezone.utc).isoformat()


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/", methods=["GET"])
def health_check():

    return jsonify({
        "service": "Kapture Finance - Maya Collections API",
        "status": "online",
        "version": "1.0",
        "timestamp": utc_now(),
    })


# ============================================================
# TOOL 1 — VERIFY CUSTOMER
# ============================================================

@app.route("/verify-customer", methods=["POST"])
def verify_customer():

    data = request.get_json(silent=True) or {}

    customer_reference = data.get("customer_reference")
    verification_value = data.get("verification_value")

    print("\n================ VERIFY CUSTOMER ================")
    print("Customer Reference:", customer_reference)
    print("Verification Value:", verification_value)

    # Validate input
    if not customer_reference:

        return jsonify({
            "success": False,
            "verified": False,
            "error": "customer_reference is required",
        }), 400

    # Find customer
    customer = CUSTOMERS.get(customer_reference)

    if not customer:

        return jsonify({
            "success": True,
            "verified": False,
            "reason": "CUSTOMER_NOT_FOUND",
        })

    # Do-not-call protection
    if customer["do_not_call"]:

        return jsonify({
            "success": True,
            "verified": False,
            "blocked": True,
            "reason": "DO_NOT_CALL",
        })

    # Mock verification
    expected_value = customer_reference.split("-")[-1]

    if str(verification_value) != str(expected_value):

        return jsonify({
            "success": True,
            "verified": False,
            "reason": "VERIFICATION_FAILED",
        })

    # Only after successful verification
    # return account information.

    return jsonify({
        "success": True,
        "verified": True,
        "customer_reference": customer_reference,
        "customer_name": customer["customer_name"],
        "loan_type": customer["loan_type"],
        "overdue_amount": customer["overdue_amount"],
        "days_past_due": customer["days_past_due"],
        "account_status": customer["status"],
    })


# ============================================================
# TOOL 2 — GET ACCOUNT DETAILS
# ============================================================

@app.route("/get-account-details", methods=["POST"])
def get_account_details():

    data = request.get_json(silent=True) or {}

    customer_reference = data.get("customer_reference")

    print("\n================ GET ACCOUNT DETAILS ================")
    print("Customer:", customer_reference)

    if not customer_reference:

        return jsonify({
            "success": False,
            "error": "customer_reference is required",
        }), 400

    customer = CUSTOMERS.get(customer_reference)

    if not customer:

        return jsonify({
            "success": False,
            "error": "CUSTOMER_NOT_FOUND",
        }), 404

    # Do not expose account details for DNC customers
    if customer["do_not_call"]:

        return jsonify({
            "success": False,
            "error": "CUSTOMER_BLOCKED",
            "reason": "DO_NOT_CALL",
        })

    return jsonify({
        "success": True,
        "customer_reference": customer_reference,
        "customer_name": customer["customer_name"],
        "loan_type": customer["loan_type"],
        "overdue_amount": customer["overdue_amount"],
        "days_past_due": customer["days_past_due"],
        "account_status": customer["status"],
    })


# ============================================================
# TOOL 3 — LOG PROMISE TO PAY
# ============================================================

@app.route("/log-promise-to-pay", methods=["POST"])
def log_promise_to_pay():

    data = request.get_json(silent=True) or {}

    customer_reference = data.get("customer_reference")
    amount = data.get("amount")
    payment_date = data.get("payment_date")

    print("\n================ LOG PTP ================")
    print("Customer:", customer_reference)
    print("Amount:", amount)
    print("Payment Date:", payment_date)

    # Required fields

    if not customer_reference:

        return jsonify({
            "success": False,
            "error": "customer_reference is required",
        }), 400

    if amount is None:

        return jsonify({
            "success": False,
            "error": "amount is required",
        }), 400

    if not payment_date:

        return jsonify({
            "success": False,
            "error": "payment_date is required",
        }), 400

    # Validate customer

    customer = CUSTOMERS.get(customer_reference)

    if not customer:

        return jsonify({
            "success": False,
            "error": "CUSTOMER_NOT_FOUND",
        }), 404

    # Validate amount

    try:
        amount = int(amount)

    except (ValueError, TypeError):

        return jsonify({
            "success": False,
            "error": "amount must be a number",
        }), 400

    if amount <= 0:

        return jsonify({
            "success": False,
            "error": "amount must be greater than zero",
        }), 400

    # Create record

    record = {
        "customer_reference": customer_reference,
        "customer_name": customer["customer_name"],
        "amount": amount,
        "payment_date": payment_date,
        "created_at": utc_now(),
        "status": "PROMISED",
    }

    PTP_RECORDS.append(record)

    print("PTP CREATED:", record)

    return jsonify({
        "success": True,
        "message": "Promise to pay recorded successfully",
        "ptp": record,
    })


# ============================================================
# TOOL 4 — SEND PAYMENT LINK
# ============================================================

@app.route("/send-payment-link", methods=["POST"])
def send_payment_link():

    data = request.get_json(silent=True) or {}

    customer_reference = data.get("customer_reference")
    channel = data.get("channel", "SMS")

    print("\n================ SEND PAYMENT LINK ================")
    print("Customer:", customer_reference)
    print("Channel:", channel)

    if not customer_reference:

        return jsonify({
            "success": False,
            "error": "customer_reference is required",
        }), 400

    customer = CUSTOMERS.get(customer_reference)

    if not customer:

        return jsonify({
            "success": False,
            "error": "CUSTOMER_NOT_FOUND",
        }), 404

    if customer["do_not_call"]:

        return jsonify({
            "success": False,
            "error": "CUSTOMER_BLOCKED",
            "reason": "DO_NOT_CALL",
        })

    # Mock payment link

    payment_link = (
        "https://pay.kapture-finance.demo/"
        + customer_reference.lower()
    )

    record = {
        "customer_reference": customer_reference,
        "channel": channel,
        "payment_link": payment_link,
        "created_at": utc_now(),
    }

    PAYMENT_LINKS.append(record)

    print("PAYMENT LINK GENERATED:", payment_link)

    return jsonify({
        "success": True,
        "message": f"Payment link prepared for {channel}",
        "channel": channel,
        "payment_link": payment_link,
    })


# ============================================================
# TOOL 5 — ESCALATE TO HUMAN
# ============================================================

@app.route("/escalate-to-agent", methods=["POST"])
def escalate_to_agent():

    data = request.get_json(silent=True) or {}

    customer_reference = data.get("customer_reference")
    reason = data.get("reason")

    print("\n================ ESCALATE ================")
    print("Customer:", customer_reference)
    print("Reason:", reason)

    record = {
        "customer_reference": customer_reference,
        "reason": reason,
        "queue": "COLLECTIONS_SPECIALIST",
        "created_at": utc_now(),
    }

    ESCALATIONS.append(record)

    return jsonify({
        "success": True,
        "escalated": True,
        "queue": "COLLECTIONS_SPECIALIST",
        "reason": reason,
        "message": (
            "Customer has been routed to a human "
            "collections specialist."
        ),
    })


# ============================================================
# TOOL 6 — MARK DISPOSITION
# ============================================================

@app.route("/mark-disposition", methods=["POST"])
def mark_disposition():

    data = request.get_json(silent=True) or {}

    customer_reference = data.get("customer_reference")
    disposition = data.get("disposition")
    notes = data.get("notes", "")

    if not customer_reference:

        return jsonify({
            "success": False,
            "error": "customer_reference is required",
        }), 400

    if not disposition:

        return jsonify({
            "success": False,
            "error": "disposition is required",
        }), 400

    record = {
        "customer_reference": customer_reference,
        "disposition": disposition,
        "notes": notes,
        "created_at": utc_now(),
    }

    DISPOSITIONS.append(record)

    print("\n================ DISPOSITION ================")
    print(record)

    return jsonify({
        "success": True,
        "message": "Call disposition recorded",
        "disposition": record,
    })


# ============================================================
# VAPI TOOL WEBHOOK — STEP 6A
# ============================================================

@app.route("/vapi/tools", methods=["POST"])
def vapi_tools():

    data = request.get_json(silent=True) or {}

    print("\n")
    print("=" * 70)
    print("VAPI TOOL REQUEST")
    print("=" * 70)
    print(data)

    message = data.get("message", {})

    # Vapi sends tool calls inside message.toolCallList
    tool_calls = message.get("toolCallList", [])

    # Some Vapi payloads may provide a single tool call.
    if not tool_calls and message.get("toolCall"):
        tool_calls = [message.get("toolCall")]

    results = []

    for tool_call in tool_calls:

        tool_call_id = (
            tool_call.get("id")
            or tool_call.get("toolCallId")
        )

        function_data = tool_call.get("function", {})

        function_name = function_data.get("name")

        parameters = function_data.get("arguments", {})

        # Sometimes arguments arrive as a JSON string.
        if isinstance(parameters, str):

            import json

            try:
                parameters = json.loads(parameters)

            except json.JSONDecodeError:

                parameters = {}

        if not isinstance(parameters, dict):
            parameters = {}

        print("\nTool:", function_name)
        print("Tool Call ID:", tool_call_id)
        print("Parameters:", parameters)

        # ====================================================
        # VERIFY CUSTOMER
        # ====================================================

        if function_name == "verify_customer":

            customer_reference = parameters.get(
                "customer_reference"
            )

            verification_value = parameters.get(
                "verification_value"
            )

            customer = CUSTOMERS.get(customer_reference)

            if not customer:

                result = {
                    "success": True,
                    "verified": False,
                    "reason": "CUSTOMER_NOT_FOUND",
                }

            elif customer["do_not_call"]:

                result = {
                    "success": True,
                    "verified": False,
                    "blocked": True,
                    "reason": "DO_NOT_CALL",
                }

            else:

                expected_value = customer_reference.split("-")[-1]

                if str(verification_value) != str(expected_value):

                    result = {
                        "success": True,
                        "verified": False,
                        "reason": "VERIFICATION_FAILED",
                    }

                else:

                    result = {
                        "success": True,
                        "verified": True,
                        "customer_reference": customer_reference,
                        "customer_name": customer["customer_name"],
                        "loan_type": customer["loan_type"],
                        "overdue_amount": customer["overdue_amount"],
                        "days_past_due": customer["days_past_due"],
                        "account_status": customer["status"],
                    }

            results.append({
                "toolCallId": tool_call_id,
                "result": result,
            })

        # ====================================================
        # GET ACCOUNT DETAILS
        # ====================================================

        elif function_name == "get_account_details":

            customer_reference = parameters.get(
                "customer_reference"
            )

            customer = CUSTOMERS.get(customer_reference)

            if not customer:

                result = {
                    "success": False,
                    "error": "CUSTOMER_NOT_FOUND",
                }

            elif customer["do_not_call"]:

                result = {
                    "success": False,
                    "error": "CUSTOMER_BLOCKED",
                    "reason": "DO_NOT_CALL",
                }

            else:

                result = {
                    "success": True,
                    "customer_reference": customer_reference,
                    "customer_name": customer["customer_name"],
                    "loan_type": customer["loan_type"],
                    "overdue_amount": customer["overdue_amount"],
                    "days_past_due": customer["days_past_due"],
                    "account_status": customer["status"],
                }

            results.append({
                "toolCallId": tool_call_id,
                "result": result,
            })

        # ====================================================
        # LOG PROMISE TO PAY
        # ====================================================

        elif function_name == "log_promise_to_pay":

            customer_reference = parameters.get(
                "customer_reference"
            )

            amount = parameters.get("amount")

            payment_date = parameters.get(
                "payment_date"
            )

            customer = CUSTOMERS.get(customer_reference)

            if not customer:

                result = {
                    "success": False,
                    "error": "CUSTOMER_NOT_FOUND",
                }

            elif amount is None:

                result = {
                    "success": False,
                    "error": "amount is required",
                }

            elif not payment_date:

                result = {
                    "success": False,
                    "error": "payment_date is required",
                }

            else:

                try:
                    amount = int(amount)

                    if amount <= 0:
                        raise ValueError

                    record = {
                        "customer_reference": customer_reference,
                        "customer_name": customer["customer_name"],
                        "amount": amount,
                        "payment_date": payment_date,
                        "created_at": utc_now(),
                        "status": "PROMISED",
                    }

                    PTP_RECORDS.append(record)

                    result = {
                        "success": True,
                        "message": "Promise to pay recorded successfully",
                        "ptp": record,
                    }

                except (ValueError, TypeError):

                    result = {
                        "success": False,
                        "error": "amount must be a positive number",
                    }

            results.append({
                "toolCallId": tool_call_id,
                "result": result,
            })

        # ====================================================
        # SEND PAYMENT LINK
        # ====================================================

        elif function_name == "send_payment_link":

            customer_reference = parameters.get(
                "customer_reference"
            )

            channel = parameters.get(
                "channel",
                "SMS"
            )

            customer = CUSTOMERS.get(customer_reference)

            if not customer:

                result = {
                    "success": False,
                    "error": "CUSTOMER_NOT_FOUND",
                }

            elif customer["do_not_call"]:

                result = {
                    "success": False,
                    "error": "CUSTOMER_BLOCKED",
                    "reason": "DO_NOT_CALL",
                }

            else:

                payment_link = (
                    "https://pay.kapture-finance.demo/"
                    + customer_reference.lower()
                )

                record = {
                    "customer_reference": customer_reference,
                    "channel": channel,
                    "payment_link": payment_link,
                    "created_at": utc_now(),
                }

                PAYMENT_LINKS.append(record)

                result = {
                    "success": True,
                    "message": (
                        f"Payment link prepared for {channel}"
                    ),
                    "channel": channel,
                    "payment_link": payment_link,
                }

            results.append({
                "toolCallId": tool_call_id,
                "result": result,
            })

        # ====================================================
        # ESCALATE TO AGENT
        # ====================================================

        elif function_name == "escalate_to_agent":

            customer_reference = parameters.get(
                "customer_reference"
            )

            reason = parameters.get(
                "reason",
                "Customer requested human assistance"
            )

            record = {
                "customer_reference": customer_reference,
                "reason": reason,
                "queue": "COLLECTIONS_SPECIALIST",
                "created_at": utc_now(),
            }

            ESCALATIONS.append(record)

            result = {
                "success": True,
                "escalated": True,
                "queue": "COLLECTIONS_SPECIALIST",
                "reason": reason,
                "message": (
                    "Customer has been routed to a human "
                    "collections specialist."
                ),
            }

            results.append({
                "toolCallId": tool_call_id,
                "result": result,
            })

        # ====================================================
        # MARK DISPOSITION
        # ====================================================

        elif function_name == "mark_disposition":

            customer_reference = parameters.get(
                "customer_reference"
            )

            disposition = parameters.get(
                "disposition"
            )

            notes = parameters.get(
                "notes",
                ""
            )

            if not customer_reference:

                result = {
                    "success": False,
                    "error": "customer_reference is required",
                }

            elif not disposition:

                result = {
                    "success": False,
                    "error": "disposition is required",
                }

            else:

                record = {
                    "customer_reference": customer_reference,
                    "disposition": disposition,
                    "notes": notes,
                    "created_at": utc_now(),
                }

                DISPOSITIONS.append(record)

                result = {
                    "success": True,
                    "message": "Call disposition recorded",
                    "disposition": record,
                }

            results.append({
                "toolCallId": tool_call_id,
                "result": result,
            })

        # ====================================================
        # UNKNOWN TOOL
        # ====================================================

        else:

            results.append({
                "toolCallId": tool_call_id,
                "result": {
                    "success": False,
                    "error": (
                        f"Unknown tool: {function_name}"
                    ),
                },
            })

    print("\nVAPI TOOL RESPONSE")
    print(results)

    return jsonify({
        "results": results
    })


# ============================================================
# DEBUG ENDPOINT
# ============================================================

@app.route("/debug/data", methods=["GET"])
def debug_data():

    return jsonify({
        "ptp_records": PTP_RECORDS,
        "payment_links": PAYMENT_LINKS,
        "dispositions": DISPOSITIONS,
        "escalations": ESCALATIONS,
    })


# ============================================================
# START SERVER
# IMPORTANT: THIS MUST BE AT THE VERY END
# ============================================================

if __name__ == "__main__":

    print("\n==============================================")
    print(" KAPTURE FINANCE - MAYA API SERVER")
    print("==============================================")
    print("Server starting...")
    print("Health:              http://127.0.0.1:5000/")
    print("Verify Customer:     POST /verify-customer")
    print("Account Details:     POST /get-account-details")
    print("Log PTP:             POST /log-promise-to-pay")
    print("Payment Link:        POST /send-payment-link")
    print("Escalation:          POST /escalate-to-agent")
    print("Disposition:         POST /mark-disposition")
    print("VAPI Tools:          POST /vapi/tools")
    print("Debug Data:          GET  /debug/data")
    print("==============================================\n")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )