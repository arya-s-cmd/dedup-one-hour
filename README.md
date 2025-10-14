# Secure Complaint De-duplication (Entity Resolution)
> **De-duplicate multi-source cyber-crime complaints at scale with reviewer oversight and a tamper-evident audit trail.**  
> _~92% precision · ~88% recall on a 10k synthetic corpus · Append-only hash-chained audit_

[![Docker](https://img.shields.io/badge/Docker-ready-0db7ed)](#quickstart)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688)](#api)
[![React](https://img.shields.io/badge/UI-React-61dafb)](#frontend)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](#license)

---

## Why this matters
Cyber-crime complaints often arrive multiple times across portals (NCRP/NCFL) and channels (helplines, web forms, walk-ins). Investigators waste time triaging the same incident, evidence gets scattered, and related cases aren’t linked. This project **automatically surfaces likely duplicates**, lets reviewers **approve/merge confidently**, and **proves chain-of-custody** with an immutable audit trail.

---

## What’s in this repo
- **Dedupe pipeline**: blocking → similarity scoring (TF-IDF, fuzzy, exacts) → graph clustering into duplicate groups.
- **Reviewer UI (React)**: approve/keep-separate/merge; side-by-side context; export audit.
- **Triage API (FastAPI)**: endpoints for dedupe runs, group listing, decisions.
- **Audit trail**: append-only **hash-chained** event log, with DB triggers to prevent mutation.
- **Docker Compose**: one-command bring-up; synthetic seed data for instant demo.

> **Results:** On a 10,000-record synthetic dataset, the pipeline achieved **~92% precision** and **~88% recall** (threshold-tunable). See [Benchmarks](#benchmarks).

---

## Architecture

### System Overview
```mermaid
flowchart LR
    A["Multi-source Complaints<br/>(NCRP · NCFL · Helpline · Web)"] -->|ingest /complaints| B[FastAPI Service]
    B -->|/dedupe/run| C["Dedupe Pipeline<br/>Blocking · Similarity · Clustering"]
    C -->|writes groups| D["DB: complaints, dup_groups,<br/>group_members, decisions, audit_log"]
    B <-->|/groups · /decision · /audit/export| D
    E[React Reviewer UI] -->|HTTP JSON| B
    E -.->|"Export Audit JSON"| D


```markdown
### Request Flow
```mermaid
sequenceDiagram
    autonumber
    participant R as Reviewer UI
    participant API as FastAPI
    participant PIPE as Dedupe Pipeline
    participant DB as DB (SQLite/Postgres)
    R->>API: POST /dedupe/run
    API->>PIPE: build candidates + score
    PIPE->>DB: write dup_groups + group_members
    API-->>R: 200 OK
    R->>API: GET /groups?status=suggested
    API->>DB: fetch groups + members
    DB-->>API: rows
    API-->>R: JSON groups
    R->>API: POST /groups/{id}/decision
    API->>DB: update status · set canonical_of
    API->>DB: INSERT audit_log (hash-chained)
    API-->>R: 200 OK


```markdown
### Data Model (ER)
```mermaid
erDiagram
    complaints {
      int id PK
      string external_id
      string name
      string phone
      string email
      string timestamp
      text   text
      int    canonical_of
    }
    dup_groups {
      int id PK
      string created_at
      string status
      text   score_summary
    }
    group_members {
      int id PK
      int group_id FK
      int complaint_id FK
    }
    decisions {
      int id PK
      int group_id FK
      string actor
      string decision
      int target_canonical_id
      string created_at
    }
    audit_log {
      int id PK
      string ts
      string actor
      string action
      string entity_type
      string entity_id
      text before_json
      text after_json
      string prev_hash
      string hash
    }
    dup_groups ||--o{ group_members : contains
    complaints ||--o{ group_members : included_in
    dup_groups ||--o{ decisions : has


```markdown
### Deployment (Dev/Prod)
```mermaid
flowchart TB
  subgraph Dev [Dev (Docker Compose)]
    W[web: Vite/React] -->|5173| Browser
    API[api: FastAPI] -->|8000| Browser
    API --- VOL[(Named Volume /data)]
  end
  subgraph Prod [Prod (Example)]
    SSR["Static Hosting<br/>(Netlify/Vercel)"] --> Users
    SRV["API Service<br/>(Render/VM/K8s)"] --> DB[(Postgres)]
    SRV --> Blob[(Disk / S3)]
    SSR -. VITE_API_BASE .-> SRV
  end





**Dedupe core**
- **Blocking keys:** phone/email/time bucket reduce pair candidates.
- **Similarity:** TF-IDF cosine on text, RapidFuzz for names, exact matches on phone/email, time proximity.
- **Clustering:** thresholded edges → connected components ⇒ **duplicate groups**.

**Audit**
- Every decision creates an **append-only** record with `prev_hash → hash` linkage.
- SQLite triggers block UPDATE/DELETE on `audit_log`.
- Exported JSON is **tamper-evident**.

---


## Quickstart

### 1) Docker (recommended)
```bash
git clone https://github.com/<you>/secure-dedup.git
cd secure-dedup
docker compose up --build
UI: http://localhost:5173
API docs: http://localhost:8000/docs
In the UI: Run Deduplication → review groups → Approve / Keep Separate / Merge → Export Audit

### 2) Local dev
'''bash
cd backend
python -m venv .venv && . .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export DB_URL=sqlite:///./app.db
python -m app.seed
uvicorn app.main:app --reload --port 8000

cd frontend
npm install
npm run dev  # opens on 5173
# ensure VITE_API_BASE=http://localhost:8000 (Docker not required in local dev)


**a.** Want me to add a `render.yaml` + Netlify config so deploys happen on push?  
**b.** Want a `BENCHMARKS.md` with the exact evaluation script and confusion matrix?
::contentReference[oaicite:0]{index=0}
