# Kapture Finance — Maya Collections Voicebot

## 1. Project Overview

Maya is an outbound collections voice assistant designed for Kapture Finance.

The assistant contacts customers regarding overdue loan EMIs and follows a secure, state-driven conversation flow. Before discussing any protected account information, Maya verifies the customer's identity using a backend verification tool.

The system supports:

- Customer identity verification
- Secure account disclosure
- Payment intent detection
- Promise-to-pay (PTP) collection
- Payment-link requests
- Already-paid handling
- Payment disputes
- Financial hardship handling
- Human-agent escalation
- Do-not-call requests
- Callback requests
- Call disposition recording

---

## 2. System Architecture

The high-level voice pipeline is:

Customer
→ Vapi Telephony
→ Speech-to-Text
→ Maya Orchestrator / LLM
→ Text-to-Speech
→ Customer

The LLM can call backend tools through the Vapi tool webhook.

Backend flow:

Vapi
→ HTTPS ngrok endpoint
→ Flask API
→ Mock customer/account data
→ Tool result
→ Vapi / Maya

The backend currently uses mock in-memory data for the assignment prototype.

---

## 3. Technology Stack

### Voice Platform

Vapi

### Speech-to-Text

Soniox STT RT v5

### Language Model

OpenAI GPT-4.1

### Text-to-Speech

Vapi Elliot v2

### Backend

Python + Flask

### Testing

Pytest

### Development

PowerShell, VS Code and ngrok

---

## 4. Vapi Configuration

The assistant was configured with:

- Model: GPT-4.1
- Voice: Vapi Elliot v2
- Transcriber: Soniox STT RT v5
- Backend tool server: Flask API exposed through ngrok

The model was selected for reliable instruction following and tool-use behaviour.

Soniox STT was selected for real-time speech recognition.

Elliot was selected as the voice layer for a natural and concise collections conversation.

---

## 5. Conversation State Machine

Maya follows a state-driven conversation model.

### State 1 — OPENING

Maya identifies herself and asks whether she is speaking with the intended customer.

No loan or overdue information is disclosed.

### State 2 — AUTHENTICATION

After the customer confirms their identity, Maya requests the customer reference number and calls:

`verify_customer`

Protected account information remains unavailable while verification is pending.

### State 3 — VERIFIED

The conversation can proceed to account discussion only when:

`verified = true`

### State 4 — ACCOUNT DISCUSSION

After successful authentication, Maya can disclose the permitted account information and determine the customer's intent.

### State 5 — INTENT HANDLING

Supported intents include:

- WILL_PAY
- CANNOT_PAY / HARDSHIP
- DISPUTE
- ALREADY_PAID
- WRONG_PERSON
- DO_NOT_CALL
- CALLBACK_REQUEST
- HOSTILE / ABUSIVE

### State 6 — PAYMENT COMMITMENT

A Promise-to-Pay is valid only after:

1. Customer identity is verified.
2. Customer agrees to pay.
3. Payment amount is known.
4. Payment date is known.
5. Customer confirms the commitment.

Maya then calls:

`log_promise_to_pay`

### State 7 — PAYMENT LINK

A payment link can only be generated for an authenticated customer.

Maya calls:

`send_payment_link`

when appropriate.

### State 8 — ESCALATION

Human escalation is used for cases such as:

- Disputes
- Financial hardship
- Explicit request for a human representative
- Complex cases that Maya should not resolve

### State 9 — CLOSING

Maya records the appropriate disposition and ends the call politely.

---

## 6. Security and Authentication

The main security principle is:

> No account information should be disclosed until customer identity has been successfully verified.

Protected information includes:

- Loan type
- Overdue amount
- Payment status
- Days past due
- Collection reason

The `verify_customer` tool is used to authenticate the customer.

A successful response must contain:

`verified = true`

Only then can Maya discuss protected account information.

If verification fails, Maya allows one retry. If verification fails again, Maya does not disclose account information and ends the account discussion.

The backend also contains authorization checks for sensitive operations so that security does not depend only on the LLM prompt.

---

## 7. Tools / API

The backend exposes the following endpoints:

```text
GET  /
POST /verify-customer
POST /get-account-details
POST /log-promise-to-pay
POST /send-payment-link
POST /escalate-to-agent
POST /mark-disposition
POST /vapi/tools
GET  /debug/data