# Secure Complaint De-duplication (Entity Resolution)
> **De-duplicate multi-source cyber-crime complaints at scale with reviewer oversight and a tamper-evident audit trail.**  
> _~92% precision · ~88% recall on a 10k synthetic corpus · Append-only hash-chained audit_

[![Docker](https://img.shields.io/badge/Docker-ready-0db7ed)](#quickstart)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688)](#api)
[![React](https://img.shields.io/badge/UI-React-61dafb)](#frontend)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](#license)

---

## Why This Matters
Cyber-crime complaints often arrive multiple times across portals (NCRP/NCFL) and channels (helplines, web forms, walk-ins). Investigators waste time triaging the same incidents, evidence gets scattered, and related cases aren’t linked.

This project:
- **Automatically surfaces likely duplicates**
- Enables reviewers to **approve / keep separate / merge**
- Preserves **chain-of-custody** via an immutable, hash-chained audit trail

---

## What’s in This Repo
- **Dedupe pipeline**: blocking → similarity scoring (TF-IDF, fuzzy, exacts) → graph clustering into duplicate groups  
- **Reviewer UI (React)**: side-by-side context; Approve / Keep Separate / Merge; export audit  
- **Triage API (FastAPI)**: endpoints for dedupe runs, group listing, decisions  
- **Audit trail**: append-only **hash-chained** event log; DB triggers prevent mutation  
- **Docker Compose**: one-command bring-up with synthetic seed data for instant demo

> **Results:** On a 10,000-record synthetic dataset, the pipeline achieved **~92% precision** and **~88% recall** (threshold-tunable). See [Benchmarks](#benchmarks).

---

## Dedupe Core
**Blocking keys:** phone / email / time-bucket to reduce candidate pairs  
**Similarity:** TF-IDF cosine on text; RapidFuzz for names; exact matches on phone/email; time proximity  
**Clustering:** thresholded edges → connected components ⇒ **duplicate groups**

---

## Audit System
- Every decision creates an **append-only** record with `prev_hash → hash` linkage
- SQLite triggers block `UPDATE`/`DELETE` on the `audit_log` table
- Exported JSON is **tamper-evident** and independently verifiable

---

## Quickstart

### 1) Docker (recommended)
    git clone https://github.com/<your-handle>/secure-dedup.git
    cd secure-dedup
    docker compose up --build

    UI:        http://localhost:5173
    API docs:  http://localhost:8000/docs

    In the UI: Run Deduplication → Review Groups → Approve / Keep Separate / Merge → Export Audit

---

### 2) Local Development
Backend:
    cd backend
    python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    export DB_URL=sqlite:///./app.db
    python -m app.seed
    uvicorn app.main:app --reload --port 8000

Frontend:
    cd ../frontend
    npm install
    npm run dev   # opens on :5173

Note:
    Ensure `VITE_API_BASE=http://localhost:8000` is set (Docker not required for local dev)

---

## Configuration
Environment variables:
- `DB_URL` — SQLAlchemy database URL (default: `sqlite:///./app.db`)
- `VITE_API_BASE` — frontend to API base URL (default: `http://localhost:8000`)

---

## API
- **POST** `/dedupe/run` — execute a dedupe run over current corpus  
- **GET** `/groups` — list grouped duplicates with similarity stats  
- **POST** `/decision` — record reviewer decision (approve / keep separate / merge)  
- **GET** `/audit/export` — export append-only audit log (JSON)

Swagger UI available at **/docs** when the server is running.

---

## Frontend
- React + Vite app for reviewer workflows
- Side-by-side record comparison, similarity highlights, decision queue
- Export audit button for chain-of-custody packaging

---

## Benchmarks
- Corpus: 10k synthetic complaints mixing portals/channels and varied noise
- Metrics at default threshold:
  - **Precision:** ~92%
  - **Recall:** ~88%
- Thresholds and blocking keys are configurable to trade precision/recall

---

## Roadmap (Optional)
- Pluggable embedding models for semantic similarity on narratives
- Active-learning loop from reviewer feedback
- Multi-DB support (PostgreSQL) with cryptographic anchoring (Merkle root) per export

---

## License
[MIT License](LICENSE)

---

**Made for investigators who care about truth, efficiency, and integrity.**
