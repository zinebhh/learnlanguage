from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..core.deps import get_db, get_current_user
from ..db.models import User
from ..services import tutor_engine

router = APIRouter()

# -------- REQUEST MODEL --------
class ChatRequest(BaseModel):
    message: str
    mode: str = "conversation"


# -------- CHAT ENDPOINT --------
@router.post("/chat")
def chat_endpoint(
    payload: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    result = tutor_engine.chat(
        user_text=payload.message,
        user=user,
        history=[],
        mode=payload.mode,
        db=db
    )
    return result