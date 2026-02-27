from sqlalchemy.orm import Session
from .models import Message, Correction

def save_message(db: Session, session_id: str, role: str, content: str, level: str = "", topic: str = ""):
    m = Message(session_id=session_id, role=role, content=content, level=level, topic=topic)
    db.add(m)
    db.commit()

def save_corrections(db: Session, session_id: str, corrections: list):
    for c in corrections or []:
        db.add(Correction(
            session_id=session_id,
            error=c.get("error",""),
            suggestion=c.get("suggestion",""),
            explanation=c.get("explanation","")
        ))
    db.commit()

def get_last_messages(db: Session, session_id: str, limit: int = 12):
    rows = (db.query(Message)
              .filter(Message.session_id == session_id)
              .order_by(Message.id.desc())
              .limit(limit)
              .all())
    rows.reverse()
    return [{"role": r.role, "content": r.content, "level": r.level, "topic": r.topic} for r in rows]

def top_errors(db: Session, session_id: str, limit: int = 5):
    # simple frequency count in python (fast enough)
    rows = (db.query(Correction)
              .filter(Correction.session_id == session_id)
              .all())
    freq = {}
    for r in rows:
        key = (r.error.strip().lower(), r.suggestion.strip())
        freq[key] = freq.get(key, 0) + 1
    ranked = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:limit]
    return [{"error": k[0], "suggestion": k[1], "count": v} for k, v in ranked]