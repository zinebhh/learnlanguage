from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.deps import get_db, get_current_user   # ✅ هنا الصحيح
from ..db.models import Message, Correction, User  # حسب الموديلات ديالك

router = APIRouter(tags=["stats"])

LEVEL_ORDER = ["A1","A2","B1","B2","C1","C2"]


@router.get("/stats/me")
def stats_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # ✅ Top 5 errors (ديال هاد user فقط)
    errors = (
        db.query(
            Correction.error,
            Correction.suggestion,
            func.count(Correction.id).label("count")
        )
        .filter(Correction.user_id == user.id)   # ✅ بدل session_id
        .group_by(Correction.error, Correction.suggestion)
        .order_by(func.count(Correction.id).desc())
        .limit(5)
        .all()
    )

    top_errors = [
        {"error": e.error, "suggestion": e.suggestion, "count": e.count}
        for e in errors
    ]

    # ✅ Messages per day (ديال user فقط)
    messages_per_day = (
        db.query(
            func.date(Message.created_at).label("day"),
            func.count(Message.id).label("count")
        )
        .filter(Message.user_id == user.id)     # ✅ بدل session_id
        .group_by("day")
        .order_by("day")
        .all()
    )
    msgs = [{"day": str(m.day), "count": m.count} for m in messages_per_day]

    # ✅ CEFR progression (ديال user فقط)
    levels = (
        db.query(Message.created_at, Message.level)
        .filter(Message.user_id == user.id)     # ✅ بدل session_id
        .filter(Message.level.isnot(None))
        .filter(Message.level != "")
        .order_by(Message.created_at)
        .all()
    )

    level_map = {lvl: i for i, lvl in enumerate(LEVEL_ORDER)}
    progression = [
        {"time": str(l.created_at), "level": l.level, "value": level_map.get(l.level, 0)}
        for l in levels
    ]

    total_messages = (
        db.query(func.count(Message.id))
        .filter(Message.user_id == user.id)     # ✅ بدل session_id
        .scalar()
    )

    return {
        "top_errors": top_errors,
        "messages_per_day": msgs,
        "progression": progression,
        "total_messages": total_messages
    }