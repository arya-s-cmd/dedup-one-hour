from __future__ import annotations
import json
from sqlalchemy.orm import Session
from .utils import utcnow_iso, hash_chain

def append_audit(db: Session, actor: str, action: str, entity_type: str, entity_id: str, before: dict | None, after: dict | None):
    prev_hash = db.execute("SELECT hash FROM audit_log ORDER BY id DESC LIMIT 1").scalar()
    payload = {
        "ts": utcnow_iso(),
        "actor": actor,
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "before": before or {},
        "after": after or {},
        "prev_hash": prev_hash or ""
    }
    h = hash_chain(prev_hash, payload)
    db.execute(
        "INSERT INTO audit_log(ts,actor,action,entity_type,entity_id,before_json,after_json,prev_hash,hash) VALUES (:ts,:actor,:action,:etype,:eid,:b,:a,:prev,:hash)",
        {
            "ts": payload["ts"], "actor": actor, "action": action,
            "etype": entity_type, "eid": entity_id,
            "b": json.dumps(before or {}, separators=(',', ':'), sort_keys=True),
            "a": json.dumps(after or {}, separators=(',', ':'), sort_keys=True),
            "prev": prev_hash, "hash": h
        }
    )
