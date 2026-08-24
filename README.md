# RecoverAI — Autonomous Revenue Recovery Agent for Merchants

RecoverAI is an autonomous, explainable revenue recovery backend engine built for the **Razorpay AI Buildathon** (Track: *AI Revenue Recovery*).

## Project Overview

RecoverAI detects revenue at risk from payment failures (e.g., card declines, gateway errors, subscription halts), determines the right recovery intervention using **Google Gemini AI** and **RAG-based merchant business policies**, and executes bounded recovery actions via **Razorpay Test APIs** (Payment Links) with complete auditability and safety guardrails.

---

## Technical Stack

- **Framework**: Python 3.11+, FastAPI, Uvicorn
- **Database**: PostgreSQL, SQLAlchemy 2.0 ORM, Alembic Migrations
- **AI Layer**: Google Gemini API (`google-genai`), FAISS Vector Search, Embeddings
- **Payment Integration**: Razorpay Python SDK (Orders & Payment Links API), Webhooks
- **Authentication**: JWT authentication with passlib/bcrypt password hashing
- **Testing**: Pytest, HTTPX Async Client

---

## Directory Structure

```
recoverai/
├── app/
│   ├── api/            # API routers and endpoints
│   ├── core/           # Security, config, database connection
│   ├── models/         # SQLAlchemy ORM models
│   ├── schemas/        # Pydantic schemas (Requests/Responses/AI Structured Output)
│   ├── services/       # Core business logic (Ingestion, Risk, AI, RAG, Action Executor, Audit)
│   ├── tasks/          # Background worker tasks & retry schedulers
│   ├── utils/          # Helper utilities
│   └── config.py       # Pydantic settings loading from .env
├── migrations/         # Alembic database migration scripts
├── tests/              # Pytest test suite
├── .env.example        # Environment variables template
├── .gitignore          # Git ignore rules
├── pyproject.toml      # Dependency & project configuration
├── requirements.txt    # Dependency requirements
└── README.md           # Documentation
```

---

## Quick Start Setup

1. **Clone & Virtual Environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Environment Variables**:
   Copy `.env.example` to `.env` and fill in your credentials:
   ```bash
   cp .env.example .env
   ```

3. **Database Setup**:
   Ensure PostgreSQL is running and update `DATABASE_URL` in `.env`.
   ```bash
   alembic upgrade head
   ```

4. **Run Application**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
