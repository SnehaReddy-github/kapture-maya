# High-Level Design (HLD)
## Capture Finance – Maya Outbound Collections Voicebot

**Project:** Capture Finance Voicebot  
**Assistant:** Maya  
**Platform:** Vapi  
**Document:** High-Level Design  
**Version:** 1.0  
**Status:** Implemented / Tested

---

# 1. Overview

Maya is an outbound voice assistant designed for Capture Finance to contact customers regarding overdue loan payments.

The assistant is designed to conduct a polite, respectful and structured conversation with customers, understand their payment situation, verify customer identity before exposing account information, record payment commitments, and send a payment link through the customer's preferred communication channel.

The system combines a Vapi voice assistant with a local backend API and dedicated tools for customer verification, promise-to-pay logging, and payment-link delivery.

---

# 2. Goals

The primary goals of the system are:

1. Contact customers regarding overdue loan EMIs.
2. Maintain a polite, calm and non-threatening conversation.
3. Verify the customer's identity before revealing sensitive account information.
4. Understand the customer's payment situation.
5. Obtain a payment commitment when appropriate.
6. Record a promise-to-pay commitment.
7. Send a payment link through SMS or WhatsApp.
8. Maintain clear separation between conversation logic and backend business logic.
9. Validate important operations through automated tests.
10. Provide observable call and tool execution logs.

---

# 3. High-Level Architecture

The system consists of the following major components:

```text
                    +----------------------+
                    |      Customer        |
                    |      Phone Call      |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |      Vapi Platform   |
                    |      Maya Assistant   |
                    +----------+-----------+
                               |
                               |
                         Tool Calls
                               |
                               v
                    +----------------------+
                    |   Backend API Server  |
                    |       Flask API       |
                    +----------+-----------+
                               |
              +----------------+----------------+
              |                |                |
              v                v                v
      +---------------+ +---------------+ +---------------+
      | Verify        | | Promise to    | | Payment Link |
      | Customer      | | Pay Logging   | | Service      |
      +---------------+ +---------------+ +---------------+
              |                |                |
              +----------------+----------------+
                               |
                               v
                    +----------------------+
                    | Customer / Account   |
                    | Data & Tool Results  |
                    +----------------------+