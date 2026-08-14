# Capture Finance – Maya Outbound Collections Voicebot

Maya is an outbound collections voice assistant developed for Capture Finance.

The assistant is designed to contact customers regarding overdue loan EMIs, verify customer identity, understand payment situations, obtain payment commitments, and support payment-link delivery.

## Project Overview

- **Assistant:** Maya
- **Use Case:** Outbound loan collections
- **Platform:** Vapi
- **Backend:** Python / Flask
- **Communication:** Voice
- **Status:** Implemented and tested

## Key Features

- Outbound customer calling
- Customer identity verification
- Overdue loan account handling
- Structured collections conversation
- Promise-to-pay recording
- Payment-link delivery support
- SMS / WhatsApp communication support
- Backend API integration
- Tool-call validation
- Automated testing
- Call and tool execution logging

## System Architecture

```text
Customer
   |
   v
Vapi Platform
   |
   v
Maya Voice Assistant
   |
   | Tool Calls
   v
Backend API
   |
   +-------------------+
   |                   |
   v                   v
Customer          Promise-to-Pay
Verification         Logging
   |                   |
   +---------+---------+
             |
             v
       Payment Link
          Service
```
##Project Structure
kapture-maya/
│
├── backend/
│   ├── api_server.py
│   ├── main.py
│   ├── maya_orchestrator.py
│   ├── server.py
│   ├── state_machine.py
│   └── tools.py
│
├── tests/
│   ├── test_api.py
│   ├── test_orchestrator.py
│   ├── test_security.py
│   └── test_state_machine.py
│
├── docs/
│   ├── HLD_Document.md
│   └── System_Architecture.png
│
└── README.md
```
````
Backend

The backend provides APIs and business logic required by the Maya assistant.

Major backend responsibilities include:

Customer verification
Account information retrieval
Promise-to-pay handling
Payment-link processing
Conversation state management
Tool-call processing
Customer Verification

Sensitive account information is protected through customer verification.

The verification flow checks the customer reference and verification value before returning account information.
````
Conversation Flow
Call Customer
      |
      v
Introduce Maya
      |
      v
Verify Customer
      |
      +---- Failed ----> Do Not Reveal Account Information
      |
      v
Understand Payment Situation
      |
      v
Discuss Payment Commitment
      |
      v
Record Promise-to-Pay
      |
      v
Send Payment Link
      |
      v
Close Conversation
````
Testing

The project includes automated tests covering:

API functionality
State-machine behavior
Orchestrator behavior
Security and verification logic

The backend API was also tested using tool-call requests and successful HTTP responses.

Vapi Integration

Maya is configured as a Vapi voice assistant with tools connected to the backend API.

The assistant handles the conversational layer while the backend handles business logic and customer/account operations.

Documentation

The detailed High-Level Design is available in:

docs/HLD_Document.md

The system architecture diagram is available in:

docs/System_Architecture.png
Security Considerations

The system follows basic security principles for collections conversations:

Verify customer identity before exposing account information.
Do not disclose sensitive account details to unverified callers.
Keep business logic in backend tools.
Validate tool inputs.
Log important tool executions and results.
