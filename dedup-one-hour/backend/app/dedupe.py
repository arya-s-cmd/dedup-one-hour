from __future__ import annotations
from typing import List, Tuple, Dict
from collections import defaultdict
from rapidfuzz import fuzz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .models import Complaint, DuplicateGroup, GroupMember
from sqlalchemy.orm import Session

def compute_candidates(records: List[Complaint]) -> Dict[tuple, set]:
    from .utils import block_keys
    buckets: Dict[tuple, list] = defaultdict(list)
    for rec in records:
        for k in block_keys(rec.phone, rec.email, rec.timestamp):
            buckets[k].append(rec)
    candidates: Dict[tuple, set] = defaultdict(set)
    for _, rows in buckets.items():
        ids = [r.id for r in rows]
        for i in range(len(ids)):
            for j in range(i+1, len(ids)):
                a, b = sorted((ids[i], ids[j]))
                candidates[(a,b)].add("block")
    return candidates

def pair_score(a: Complaint, b: Complaint, tfidf_model=None, tfidf_vectors=None, idxmap=None) -> Dict:
    name = fuzz.token_sort_ratio(a.name or "", b.name or "") / 100.0
    email = 1.0 if (a.email and b.email and a.email == b.email) else 0.0
    phone = 1.0 if (a.phone and b.phone and a.phone == b.phone) else 0.0
    td = 0.0
    if a.timestamp and b.timestamp:
        da = a.timestamp.split("T")[0]
        db = b.timestamp.split("T")[0]
        td = 1.0 if da == db else 0.0
    text_sim = 0.0
    if tfidf_model is not None:
        ia, ib = idxmap[a.id], idxmap[b.id]
        text_sim = float(cosine_similarity(tfidf_vectors[ia], tfidf_vectors[ib])[0][0])
    score = 0.35*text_sim + 0.25*phone + 0.2*email + 0.15*name + 0.05*td
    return {"score": score, "breakdown": {"text": text_sim, "phone": phone, "email": email, "name": name, "time": td}}

def build_groups(db: Session, threshold: float = 0.72) -> None:
    recs = db.query(Complaint).all()
    if not recs: return
    idxmap = {r.id:i for i,r in enumerate(recs)}
    texts = [(r.text or "") for r in recs]
    tfidf = TfidfVectorizer(min_df=2, max_features=20000, ngram_range=(1,2))
    tfidf_vectors = tfidf.fit_transform(texts) if any(texts) else None
    candidates = compute_candidates(recs)
    edges = defaultdict(dict)
    for (a_id,b_id) in candidates.keys():
        a = next(r for r in recs if r.id==a_id)
        b = next(r for r in recs if r.id==b_id)
        sc = pair_score(a,b, tfidf, tfidf_vectors, idxmap if tfidf_vectors is not None else None)
        if sc["score"] >= threshold:
            edges[a_id][b_id] = sc
            edges[b_id][a_id] = sc
    visited=set()
    for start in list(edges.keys()):
        if start in visited: continue
        stack=[start]; comp=[]
        while stack:
            n=stack.pop()
            if n in visited: continue
            visited.add(n); comp.append(n)
            stack.extend([k for k in edges.get(n,{}).keys() if k not in visited])
        if len(comp) >= 2:
            group = DuplicateGroup(status="suggested", score_summary=f"{len(comp)} members")
            db.add(group); db.flush()
            for cid in comp:
                db.add(GroupMember(group_id=group.id, complaint_id=cid))
    db.commit()
