from flask import Flask, request, jsonify
from datetime import datetime, timezone
import json

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
        "verified": False,
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
        "verified": False,
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
        "verified": False,
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
# HELPER FUNCTIONS
# ============================================================

def utc_now():
    """Return timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def is_verified(customer):
    """Check whether the customer has been successfully verified."""
    return customer.get("verified", False)


def authentication_required():
    """Standard response when verification has not occurred."""
    return jsonify({
        "success": False,
        "error": "AUTHENTICATION_REQUIRED",
        "reason": "CUSTOMER_NOT_VERIFIED",
        "message": (
            "Customer identity must be successfully verified "
            "before account information or payment actions "
            "can be accessed."
        ),
    }), 403


def normalize_amount(value):
    """
    Convert common spoken/string money formats into an integer.

    Examples:
        8499             -> 8499
        "8499"           -> 8499
        "8,499"          -> 8499
        "₹8,499"         -> 8499
        "$8,499"         -> 8499
        "8499 rupees"    -> 8499
        "8499.00"        -> 8499
    """

    if value is None:
        return None

    if isinstance(value, bool):
        return None

    try:
        if isinstance(value, (int, float)):
            return int(value)

        value = str(value).strip()

        value = (
            value
            .replace(",", "")
            .replace("₹", "")
            .replace("$", "")
            .replace("INR", "")
            .replace("inr", "")
            .replace("rupees", "")
            .replace("Rupees", "")
            .replace("RUPEES", "")
            .strip()
        )

        return int(float(value))

    except (ValueError, TypeError):
        return None


def extract_parameter(parameters, *names):
    """
    Return the first available parameter from a list
    of possible parameter names.
    """

    for name in names:
        if name in parameters and parameters[name] is not None:
            return parameters[name]

    return None


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/", methods=["GET"])
def health_check():

    return jsonify({
        "service": "Kapture Finance - Maya Collections API",
        "status": "online",
        "version": "1.1",
        "timestamp": utc_now(),
    })


# ============================================================
# TOOL 1 - VERIFY CUSTOMER
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
    #
    # CUS-1001 -> expected verification value = 1001
    # CUS-PAID-001 -> expected verification value = 001
    expected_value = customer_reference.split("-")[-1]

    if str(verification_value).strip() != str(expected_value).strip():

        customer["verified"] = False

        print("VERIFICATION FAILED:", customer_reference)

        return jsonify({
            "success": True,
            "verified": False,
            "reason": "VERIFICATION_FAILED",
        })

    # Successful verification
    customer["verified"] = True

    print("CUSTOMER VERIFIED:", customer_reference)

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
# TOOL 2 - GET ACCOUNT DETAILS
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

    # DNC protection
    if customer["do_not_call"]:

        return jsonify({
            "success": False,
            "error": "CUSTOMER_BLOCKED",
            "reason": "DO_NOT_CALL",
        }), 403

    # Verification guardrail
    if not is_verified(customer):

        print(
            "SECURITY BLOCK: Account details requested "
            "before customer verification."
        )

        return authentication_required()

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
# TOOL 3 - LOG PROMISE TO PAY
# ============================================================

@app.route("/log-promise-to-pay", methods=["POST"])
def log_promise_to_pay():

    data = request.get_json(silent=True) or {}

    customer_reference = data.get("customer_reference")

    # Accept both NEW and OLD schema names.
    #
    # Preferred:
    #   amount
    #   payment_date
    #
    # Fallback:
    #   ptp_amount
    #   ptp_date

    amount = extract_parameter(
        data,
        "amount",
        "ptp_amount"
    )

    payment_date = extract_parameter(
        data,
        "payment_date",
        "ptp_date"
    )

    print("\n================ LOG PTP ================")
    print("Customer:", customer_reference)
    print("Raw Amount:", amount)
    print("Payment Date:", payment_date)

    # Required customer reference
    if not customer_reference:

        return jsonify({
            "success": False,
            "error": "customer_reference is required",
        }), 400

    # Validate customer
    customer = CUSTOMERS.get(customer_reference)

    if not customer:

        return jsonify({
            "success": False,
            "error": "CUSTOMER_NOT_FOUND",
        }), 404

    # DNC protection
    if customer["do_not_call"]:

        return jsonify({
            "success": False,
            "error": "CUSTOMER_BLOCKED",
            "reason": "DO_NOT_CALL",
        }), 403

    # Verification guardrail
    if not is_verified(customer):

        print(
            "SECURITY BLOCK: PTP requested "
            "before customer verification."
        )

        return authentication_required()

    # Amount required
    if amount is None:

        print("PTP ERROR: amount is missing")

        return jsonify({
            "success": False,
            "error": "amount is required",
            "expected_fields": [
                "customer_reference",
                "amount",
                "payment_date"
            ],
        }), 400

    # Payment date required
    if not payment_date:

        print("PTP ERROR: payment_date is missing")

        return jsonify({
            "success": False,
            "error": "payment_date is required",
            "expected_fields": [
                "customer_reference",
                "amount",
                "payment_date"
            ],
        }), 400

    # Normalize amount
    normalized_amount = normalize_amount(amount)

    if normalized_amount is None:

        return jsonify({
            "success": False,
            "error": "amount must be a positive number",
        }), 400

    if normalized_amount <= 0:

        return jsonify({
            "success": False,
            "error": "amount must be greater than zero",
        }), 400

    # Prevent commitment above overdue amount
    if normalized_amount > customer["overdue_amount"]:

        return jsonify({
            "success": False,
            "error": "amount exceeds current overdue amount",
            "overdue_amount": customer["overdue_amount"],
        }), 400

    # Create PTP record
    record = {
        "customer_reference": customer_reference,
        "customer_name": customer["customer_name"],
        "amount": normalized_amount,
        "payment_date": str(payment_date),
        "created_at": utc_now(),
        "status": "PROMISED",
    }

    PTP_RECORDS.append(record)

    print("PTP CREATED SUCCESSFULLY:")
    print(record)

    return jsonify({
        "success": True,
        "message": "Promise to pay recorded successfully",
        "ptp": record,
    })


# ============================================================
# TOOL 4 - SEND PAYMENT LINK
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

    # DNC protection
    if customer["do_not_call"]:

        return jsonify({
            "success": False,
            "error": "CUSTOMER_BLOCKED",
            "reason": "DO_NOT_CALL",
        }), 403

    # Verification guardrail
    if not is_verified(customer):

        print(
            "SECURITY BLOCK: Payment link requested "
            "before customer verification."
        )

        return authentication_required()

    # Validate channel
    channel = str(channel).upper().strip()

    if channel not in ["SMS", "WHATSAPP"]:

        return jsonify({
            "success": False,
            "error": "INVALID_CHANNEL",
            "message": "Channel must be SMS or WHATSAPP.",
        }), 400

    # Generate mock payment link
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
# TOOL 5 - ESCALATE TO HUMAN
# ============================================================

@app.route("/escalate-to-agent", methods=["POST"])
def escalate_to_agent():

    data = request.get_json(silent=True) or {}

    customer_reference = data.get("customer_reference")

    reason = data.get(
        "reason",
        "Customer requested human assistance"
    )

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
# TOOL 6 - MARK DISPOSITION
# ============================================================

@app.route("/mark-disposition", methods=["POST"])
def mark_disposition():

    data = request.get_json(silent=True) or {}

    customer_reference = data.get("customer_reference")
    disposition = data.get("disposition")
    notes = data.get("notes", "")

    print("\n================ DISPOSITION ================")
    print("Customer:", customer_reference)
    print("Disposition:", disposition)
    print("Notes:", notes)

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

    print(record)

    return jsonify({
        "success": True,
        "message": "Call disposition recorded",
        "disposition": record,
    })


# ============================================================
# VAPI TOOL WEBHOOK
# ============================================================

@app.route("/vapi/tools", methods=["POST"])
def vapi_tools():

    data = request.get_json(silent=True) or {}

    print("\n")
    print("=" * 70)
    print("VAPI TOOL REQUEST")
    print("=" * 70)
    print(json.dumps(data, indent=2, default=str))

    message = data.get("message", {})

    # Vapi normally sends multiple tool calls here.
    tool_calls = message.get("toolCallList", [])

    # Some payloads can contain one tool call.
    if not tool_calls and message.get("toolCall"):

        tool_calls = [
            message.get("toolCall")
        ]

    results = []

    # ========================================================
    # PROCESS EACH TOOL CALL
    # ========================================================

    for tool_call in tool_calls:

        tool_call_id = (
            tool_call.get("id")
            or tool_call.get("toolCallId")
        )

        function_data = tool_call.get("function", {})

        function_name = function_data.get("name")

        parameters = function_data.get(
            "arguments",
            {}
        )

        # Arguments can arrive as JSON string.
        if isinstance(parameters, str):

            try:
                parameters = json.loads(parameters)

            except json.JSONDecodeError:

                print(
                    "WARNING: Could not parse tool arguments:"
                )

                print(parameters)

                parameters = {}

        if not isinstance(parameters, dict):

            parameters = {}

        print("\n------------------------------------------")
        print("Tool:", function_name)
        print("Tool Call ID:", tool_call_id)
        print("Parameters:", parameters)
        print("------------------------------------------")

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

            customer = CUSTOMERS.get(
                customer_reference
            )

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

                expected_value = (
                    customer_reference.split("-")[-1]
                )

                if (
                    str(verification_value).strip()
                    != str(expected_value).strip()
                ):

                    customer["verified"] = False

                    result = {
                        "success": True,
                        "verified": False,
                        "reason": "VERIFICATION_FAILED",
                    }

                else:

                    customer["verified"] = True

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

            customer = CUSTOMERS.get(
                customer_reference
            )

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

            elif not is_verified(customer):

                result = {
                    "success": False,
                    "error": "AUTHENTICATION_REQUIRED",
                    "reason": "CUSTOMER_NOT_VERIFIED",
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

            amount = extract_parameter(
                parameters,
                "amount",
                "ptp_amount"
            )

            payment_date = extract_parameter(
                parameters,
                "payment_date",
                "ptp_date"
            )

            print("\nPTP TOOL PARAMETERS:")
            print("customer_reference =", customer_reference)
            print("amount =", amount)
            print("payment_date =", payment_date)

            customer = CUSTOMERS.get(
                customer_reference
            )

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

            elif not is_verified(customer):

                result = {
                    "success": False,
                    "error": "AUTHENTICATION_REQUIRED",
                    "reason": "CUSTOMER_NOT_VERIFIED",
                }

            elif amount is None:

                result = {
                    "success": False,
                    "error": "amount is required",
                    "expected_fields": [
                        "customer_reference",
                        "amount",
                        "payment_date"
                    ],
                }

            elif not payment_date:

                result = {
                    "success": False,
                    "error": "payment_date is required",
                    "expected_fields": [
                        "customer_reference",
                        "amount",
                        "payment_date"
                    ],
                }

            else:

                normalized_amount = normalize_amount(
                    amount
                )

                if normalized_amount is None:

                    result = {
                        "success": False,
                        "error": (
                            "amount must be a "
                            "positive number"
                        ),
                    }

                elif normalized_amount <= 0:

                    result = {
                        "success": False,
                        "error": (
                            "amount must be greater "
                            "than zero"
                        ),
                    }

                elif normalized_amount > customer["overdue_amount"]:

                    result = {
                        "success": False,
                        "error": (
                            "amount exceeds current "
                            "overdue amount"
                        ),
                        "overdue_amount": (
                            customer["overdue_amount"]
                        ),
                    }

                else:

                    record = {
                        "customer_reference": customer_reference,
                        "customer_name": customer["customer_name"],
                        "amount": normalized_amount,
                        "payment_date": str(payment_date),
                        "created_at": utc_now(),
                        "status": "PROMISED",
                    }

                    PTP_RECORDS.append(record)

                    print(
                        "PTP CREATED THROUGH VAPI:"
                    )
                    print(record)

                    result = {
                        "success": True,
                        "message": (
                            "Promise to pay recorded "
                            "successfully"
                        ),
                        "ptp": record,
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

            customer = CUSTOMERS.get(
                customer_reference
            )

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

            elif not is_verified(customer):

                result = {
                    "success": False,
                    "error": "AUTHENTICATION_REQUIRED",
                    "reason": "CUSTOMER_NOT_VERIFIED",
                }

            else:

                channel = str(
                    channel
                ).upper().strip()

                if channel not in [
                    "SMS",
                    "WHATSAPP"
                ]:

                    result = {
                        "success": False,
                        "error": "INVALID_CHANNEL",
                        "message": (
                            "Channel must be "
                            "SMS or WHATSAPP."
                        ),
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
                            f"Payment link prepared "
                            f"for {channel}"
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
                    "Customer has been routed to a "
                    "human collections specialist."
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
                    "error": (
                        "customer_reference "
                        "is required"
                    ),
                }

            elif not disposition:

                result = {
                    "success": False,
                    "error": (
                        "disposition "
                        "is required"
                    ),
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
                    "message": (
                        "Call disposition recorded"
                    ),
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

            print(
                "UNKNOWN TOOL:",
                function_name
            )

            results.append({
                "toolCallId": tool_call_id,
                "result": {
                    "success": False,
                    "error": (
                        f"Unknown tool: "
                        f"{function_name}"
                    ),
                },
            })

    # ========================================================
    # VAPI RESPONSE
    # ========================================================

    print("\n================ VAPI TOOL RESPONSE ================")

    print(
        json.dumps(
            results,
            indent=2,
            default=str
        )
    )

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
# RESET DEMO DATA
# ============================================================

@app.route("/debug/reset", methods=["POST"])
def reset_demo_data():

    PTP_RECORDS.clear()
    PAYMENT_LINKS.clear()
    DISPOSITIONS.clear()
    ESCALATIONS.clear()

    # Reset verification status
    for customer in CUSTOMERS.values():
        customer["verified"] = False

    return jsonify({
        "success": True,
        "message": "Demo data and verification state reset.",
    })


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    print("\n==============================================")
    print(" KAPTURE FINANCE - MAYA API SERVER")
    print("==============================================")
    print("Server starting...")
    print()

    print("Health:")
    print("http://127.0.0.1:5000/")
    print()

    print("Verify Customer:")
    print("POST /verify-customer")
    print()

    print("Account Details:")
    print("POST /get-account-details")
    print()

    print("Log PTP:")
    print("POST /log-promise-to-pay")
    print()

    print("Payment Link:")
    print("POST /send-payment-link")
    print()

    print("Escalation:")
    print("POST /escalate-to-agent")
    print()

    print("Disposition:")
    print("POST /mark-disposition")
    print()

    print("VAPI Tools:")
    print("POST /vapi/tools")
    print()

    print("Debug Data:")
    print("GET /debug/data")
    print()

    print("Reset Demo:")
    print("POST /debug/reset")

    print("==============================================\n")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )