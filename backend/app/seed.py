from __future__ import annotations
import random
from sqlalchemy.orm import Session
from .db import SessionLocal, engine, Base, init_triggers
from .models import Complaint
from .utils import norm_phone, norm_email, norm_text, iso_datetime

N=600
N_DUP_SETS=100

names = ["Rahul","Priya","Anil","Sunita","Vikram","Aisha","Rohit","Neha"]
domains=["mail.com","example.com","inbox.in","gov.in"]
texts = [
 "I was duped by a caller asking OTP for KYC.",
 "UPI transfer went to wrong account after a fraud link.",
 "Job scam demanded registration fee, then blocked me.",
 "Call from bank, asked CVV, card charged without consent.",
 "Phishing sms with link, my account debited.",
]
phones = ["+91 98{:08d}".format(i) for i in range(10000000,10005000)]

def seed():
    Base.metadata.create_all(bind=engine)
    init_triggers()
    db: Session = SessionLocal()
    if db.query(Complaint).count() > 0:
        db.close(); return
    rnd = random.Random(42)
    for i in range(N):
        name = rnd.choice(names)+" "+str(rnd.randint(1,99))
        email = f"{name.split()[0].lower()}{rnd.randint(1,999)}@{rnd.choice(domains)}"
        phone = rnd.choice(phones)
        ts = f"2025-09-{rnd.randint(1,28):02d}T{rnd.randint(0,23):02d}:{rnd.randint(0,59):02d}:00"
        text = rnd.choice(texts)
        c = Complaint(
            external_id=f"EXT-{i}",
            name=name, phone=norm_phone(phone), email=norm_email(email), timestamp=iso_datetime(ts), text=norm_text(text)
        )
        db.add(c)
    db.commit()
    ids = [c.id for c in db.query(Complaint).all()]
    for k in range(N_DUP_SETS):
        base_id = rnd.choice(ids)
        base = db.get(Complaint, base_id)
        for _ in range(rnd.randint(1,2)):
            c = Complaint(
                external_id=f"DUP-{k}-{rnd.randint(1000,9999)}",
                name=base.name,
                phone=base.phone,
                email=base.email if rnd.random()<0.7 else None,
                timestamp=base.timestamp,
                text=base.text,
            )
            db.add(c)
    db.commit(); db.close()

if __name__ == "__main__":
    seed()
