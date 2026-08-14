KAPTURE FINANCE – MAYA VOICE AI ARCHITECTURE

                         CUSTOMER
                            │
                            │ Voice Call
                            ▼
                  ┌─────────────────────┐
                  │      TELEPHONY      │
                  │  Outbound Call/SIP  │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │        VAPI         │
                  │   Voice Platform    │
                  │      Maya Agent     │
                  └──────────┬──────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
        ┌──────────┐   ┌────────────┐  ┌──────────┐
        │   STT    │   │    LLM     │  │   TTS    │
        │ Speech → │   │ GPT-4.1    │  │ Text →   │
        │  Text    │   │Orchestrator│  │  Speech  │
        └────┬─────┘   └─────┬──────┘  └────▲─────┘
             │               │              │
             │               │ Tool Calls   │
             │               ▼              │
             │       ┌─────────────────┐    │
             │       │   BACKEND API   │    │
             │       │  Flask/Webhook  │    │
             │       └────────┬────────┘    │
             │                │             │
             │        ┌───────┼────────┐    │
             │        │       │        │    │
             │        ▼       ▼        ▼    │
             │   ┌────────┐ ┌──────┐ ┌────────────┐
             │   │Verify  │ │ Log  │ │   Send     │
             │   │Customer│ │ PTP  │ │ Payment    │
             │   └────────┘ └──────┘ │   Link     │
             │                       └────────────┘
             │
             │
             ▼
       ┌────────────────────────────────────┐
       │       STATE / CONVERSATION         │
       │                                    │
       │ Greeting                           │
       │      ↓                             │
       │ Authentication                     │
       │      ↓                             │
       │ Authenticated                      │
       │      ↓                             │
       │ Payment Negotiation                │
       │      ↓                             │
       │ PTP / Hardship / Dispute           │
       │      ↓                             │
       │ Closing / Disposition              │
       └────────────────────────────────────┘


SECURITY GATE

        Customer Information
                 │
                 ▼
        ┌─────────────────┐
        │ verify_customer │
        └────────┬────────┘
                 │
          ┌──────┴──────┐
          │             │
       VERIFIED       FAILED
          │             │
          ▼             ▼
  Account details    No debt
    permitted       disclosure