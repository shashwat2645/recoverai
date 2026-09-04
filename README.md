# RecoverAI — Autonomous Revenue Recovery Agent for Merchants

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python)](https://python.org)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-2.5--Flash-4285F4?style=flat&logo=google)](https://ai.google.dev)
[![Razorpay](https://img.shields.io/badge/Razorpay-Payment%20Links%20API-0C2340?style=flat&logo=razorpay)](https://razorpay.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=flat&logo=sqlalchemy)](https://www.sqlalchemy.org)

> **Razorpay AI Buildathon Submission**  
> **Track**: *AI Revenue Recovery*  
> **Mission**: Build an autonomous AI agent that detects revenue at risk from payment failures, diagnoses root causes with merchant business policy context, and executes bounded recovery workflows with explainability, stopping rules, and immutable audit trails.

---

## Key Capabilities & Problem Solved

| Feature | How RecoverAI Solves It |
| :--- | :--- |
| **Revenue Leak Detection** | Ingests real-time Razorpay webhooks (`payment.failed`) with HMAC-SHA256 signature verification & deduplication. Prioritizes cases by revenue value and failure code. |
| **AI Root Cause Analysis** | Utilizes **Google Gemini 2.5 Flash** with low-temperature structured outputs to diagnose technical glitches, customer limits, or invalid instruments. |
| **RAG Policy Grounding** | Indexes merchant refund, retry, and discount terms via **Vector Embeddings (`text-embedding-004`)**, dynamically retrieving relevant rules before AI decision-making. |
| **Bounded Action Execution** | Hard whitelist guardrails: executes **only** safe actions (`GENERATE_PAYMENT_LINK`, `SEND_REMINDER`, `SCHEDULE_RETRY`). Code-level block on dangerous operations like refunds. |
| **Explainable Audit Trail** | Captures input events, prompt context, retrieved RAG policies, confidence scores, and timestamps in an immutable PostgreSQL/SQLite audit table. |
| **Live Evaluation Metrics** | Real-time analytics dashboard tracking Failed Payments, Revenue at Risk, Recovery Conversion %, and False Actions Avoided. |

---

## System Architecture Flow

```
                      INCOMING PAYMENT FAILURE
                                 │
                                 ▼
             [ Razorpay Webhook Ingestion & Deduplication ]
                                 │
                                 ▼
              [ Revenue Risk Scoring & Case Detection ]
                                 │
                                 ▼
                [ RAG Merchant Policy Retrieval ]
                (Vector Search: text-embedding-004)
                                 │
                                 ▼
                 [ Gemini AI Reasoning Engine ]
             (Structured Output: AIReasoningResult)
                                 │
                                 ▼
              [ Bounded Action Execution Sandbox ]
        ┌────────────────────────┴────────────────────────┐
        ▼                                                 ▼
[ Allowed Bounded Action ]                      [ Forbidden Action ]
- Generate Razorpay Link                        (e.g., Refund, Alter Amount)
- Dispatch Notification                                   │
- Schedule 24h Retry                                      ▼
        │                                     [ 🚫 Guardrail Blocked ]
        └────────────────────────┬────────────────────────┘
                                 │
                                 ▼
                  [ Immutable Audit Trail Logged ]
                                 │
                                 ▼
             [ Real-Time Glassmorphic Merchant Dashboard ]
```

---

## Technical Stack

- **Backend**: Python 3.11+, FastAPI, Uvicorn, Pydantic v2
- **Database & ORM**: SQLAlchemy 2.0 (PostgreSQL & SQLite compatible), Alembic Migrations
- **AI & RAG**: Google GenAI SDK (`google-genai`), Gemini 2.5 Flash, Text Embeddings
- **Payments Gateway**: Razorpay Python SDK (Payment Links API, Orders API, HMAC Webhooks)
- **Security**: JWT Authentication, Bcrypt Password Hashing, HMAC-SHA256 Timing Attack Defense
- **Frontend**: Single-Page Responsive Glassmorphic Dashboard (HTML5, Vanilla CSS, JS)

---

## Quick Start & Installation

### 1. Setup Virtual Environment
```bash
# Clone repository
git clone https://github.com/shashwat2645/recoverai.git
cd recoverai

# Create & activate venv
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and configure your keys:
```bash
cp .env.example .env
```
*(Default settings run seamlessly with mock mode even without active external API keys).*

### 3. Run Database Migrations
```bash
alembic upgrade head
```

### 4. Start the Application
```bash
uvicorn app.main:app --reload --port 8000
```
- **Web Dashboard**: Open [http://localhost:8000](http://localhost:8000)
- **Interactive API Docs**: Open [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Running the Evaluation Benchmark

Run the automated end-to-end evaluation simulator to process multi-category payment failures and measure recovery performance:

```bash
python scripts/benchmark_runner.py
```

### Sample Evaluation Output:
```text
======================================================================
 📊 EVALUATION SCORECARD & METRICS SUMMARY
======================================================================
 Total Failed Payments Analyzed:  6
 Total Revenue at Risk Detected:  ₹19,996.00
 Recovery Interventions Executed: 5
 False / Unsafe Actions Avoided:  1 (100% Guardrail Compliance)
 Total Pipeline Execution Time:   0.96 seconds
 Average Latency per Case:        0.16s
======================================================================
 ✅ All benchmarks & safety guardrails validated successfully!
```

---

## Core API Endpoints

### Authentication & Merchant
- `POST /api/v1/auth/register` — Register merchant account
- `POST /api/v1/auth/login` — Authenticate and receive JWT Bearer token
- `GET /api/v1/auth/me` — Current authenticated merchant profile

### Event Ingestion & Webhooks
- `POST /api/v1/webhooks/razorpay` — Razorpay webhook receiver with HMAC signature verification
- `POST /api/v1/events/simulate` — Ingest simulated payment failures for testing

### Revenue Recovery Cases & Agent Orchestrator
- `GET /api/v1/cases` — List merchant recovery cases (with status & risk filters)
- `GET /api/v1/cases/{case_id}` — Get single recovery case details
- `POST /api/v1/cases/{case_id}/analyze` — Trigger Gemini AI root-cause analysis
- `POST /api/v1/cases/{case_id}/execute` — Execute bounded recovery action via Razorpay
- `GET /api/v1/cases/{case_id}/audit-logs` — Fetch case explainability audit timeline

### RAG Policies & Knowledge Base
- `POST /api/v1/policies` — Create & vector-index a merchant policy document
- `GET /api/v1/policies` — List active merchant business rules

### Evaluation & Analytics
- `GET /api/v1/dashboard/metrics` — Aggregate recovery metrics and conversion statistics
- `GET /api/v1/audit-logs` — Global merchant audit log explorer
