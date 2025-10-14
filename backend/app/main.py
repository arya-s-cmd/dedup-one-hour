from __future__ import annotations
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import update
from .db import Base, engine, SessionLocal, init_triggers
from .models import Complaint, DuplicateGroup, GroupMember, Decision
from .schemas import ComplaintIn, ComplaintOut, GroupOut, DecisionIn
from .utils import norm_phone, norm_email, norm_text, iso_datetime
from .dedupe import build_groups
from .audit import append_audit

app = FastAPI(title="Dedup API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    init_triggers()

@app.post("/complaints", response_model=ComplaintOut)
def create_complaint(payload: ComplaintIn, db: Session = Depends(get_db)):
    c = Complaint(
        external_id = payload.external_id,
        name = (payload.name or "").strip() or None,
        phone = norm_phone(payload.phone),
        email = norm_email(payload.email),
        timestamp = iso_datetime(payload.timestamp),
        text = norm_text(payload.text),
    )
    db.add(c); db.commit(); db.refresh(c)
    append_audit(db, actor="system", action="ingest", entity_type="complaint", entity_id=str(c.id), before=None, after={"complaint": c.id})
    db.commit()
    return ComplaintOut(id=c.id, **payload.model_dump())

@app.post("/dedupe/run")
def run_dedupe(db: Session = Depends(get_db)):
    build_groups(db)
    append_audit(db, actor="system", action="dedupe_run", entity_type="dedupe", entity_id="*", before=None, after={})
    db.commit()
    return {"ok": True}

@app.get("/groups", response_model=list[GroupOut])
def list_groups(status: str = "suggested", db: Session = Depends(get_db)):
    groups = db.query(DuplicateGroup).filter(DuplicateGroup.status==status).all()
    out=[]
    for g in groups:
        member_ids = [m.complaint_id for m in db.query(GroupMember).filter_by(group_id=g.id)]
        members = db.query(Complaint).filter(Complaint.id.in_(member_ids)).all()
        phones = {m.phone for m in members if m.phone}
        emails = {m.email for m in members if m.email}
        out.append(GroupOut(
            id=g.id, status=g.status, score_summary=g.score_summary,
            members=[ComplaintOut(id=m.id, external_id=m.external_id, name=m.name, phone=m.phone, email=m.email, timestamp=m.timestamp, text=m.text) for m in members],
            top_evidence={"same_phone": len(phones)==1 and len(phones)>0, "same_email": len(emails)==1 and len(emails)>0}
        ))
    return out

@app.post("/groups/{group_id}/decision")
def decide_group(group_id: int, payload: DecisionIn, db: Session = Depends(get_db)):
    g = db.get(DuplicateGroup, group_id)
    if not g: raise HTTPException(404, "group not found")
    if payload.decision not in {"approve","keep_separate","merge_into"}:
        raise HTTPException(400, "invalid decision")
    dec = Decision(group_id=g.id, actor=payload.actor, decision=payload.decision, target_canonical_id=payload.target_canonical_id)
    db.add(dec)
    before = {"status": g.status}
    if payload.decision=="approve":
        g.status="approved"
        members = [m.complaint_id for m in db.query(GroupMember).filter_by(group_id=g.id)]
        if not members: raise HTTPException(400, "empty group")
        canonical = min(members) if payload.target_canonical_id is None else payload.target_canonical_id
        for cid in members:
            db.execute(update(Complaint).where(Complaint.id==cid).values(canonical_of=canonical))
    elif payload.decision=="keep_separate":
        g.status="rejected"
    elif payload.decision=="merge_into":
        if not payload.target_canonical_id:
            raise HTTPException(400, "target_canonical_id required")
        members = [m.complaint_id for m in db.query(GroupMember).filter_by(group_id=g.id)]
        for cid in members:
            db.execute(update(Complaint).where(Complaint.id==cid).values(canonical_of=payload.target_canonical_id))
        g.status="merged"
    append_audit(db, actor=payload.actor, action="decision", entity_type="dup_group", entity_id=str(g.id), before=before, after={"status": g.status, "decision": payload.decision})
    db.commit()
    return {"ok": True}

@app.get("/audit/export")
def audit_export(db: Session = Depends(get_db)):
    rows = db.execute("SELECT id,ts,actor,action,entity_type,entity_id,before_json,after_json,prev_hash,hash FROM audit_log ORDER BY id ASC").all()
    return {"records":[dict(r._mapping) for r in rows]}
