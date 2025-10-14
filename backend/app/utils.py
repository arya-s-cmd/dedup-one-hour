from __future__ import annotations
import re, json, hashlib, datetime
import phonenumbers
from email_validator import validate_email, EmailNotValidError
from dateutil import parser as dateparser

def norm_phone(s: str | None) -> str | None:
    if not s: return None
    try:
        num = phonenumbers.parse(s, "IN")
        if not phonenumbers.is_valid_number(num): return None
        return phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164)
    except Exception:
        return None

def norm_email(s: str | None) -> str | None:
    if not s: return None
    s = s.strip().lower()
    try:
        return validate_email(s, check_deliverability=False).normalized
    except EmailNotValidError:
        return None

def norm_text(s: str | None) -> str | None:
    if not s: return None
    s = re.sub(r"\s+", " ", s.strip().lower())
    return s[:5000]

def iso_datetime(s: str | None) -> str | None:
    if not s: return None
    try:
        dt = dateparser.parse(s)
        return dt.replace(microsecond=0).isoformat()
    except Exception:
        return None

def block_keys(phone: str | None, email: str | None, ts: str | None):
    keys = []
    if phone: keys.append(("p", phone))
    if email:
        user, _, domain = email.partition("@")
        keys.append(("e", f"{user[:4]}@{domain}"))
    if ts:
        day = ts.split("T")[0]
        keys.append(("d", day))
    return keys

def hash_chain(prev_hash: str | None, payload: dict) -> str:
    msg = (prev_hash or "") + json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(msg.encode("utf-8")).hexdigest()

def utcnow_iso() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat()+"Z"
