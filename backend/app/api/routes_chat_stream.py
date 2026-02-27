import json
import requests
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any

from ..services.tutor_engine import build_prompt_context, safe_json_parse, make_exercise_from_top_errors
from ..db.database import SessionLocal
from ..db.repo import save_message, save_corrections, get_last_messages, top_errors

router = APIRouter()

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "llama3.2:3b"

class StreamChatRequest(BaseModel):
    session_id: str
    message: str

@router.post("/chat_stream")
def chat_stream(payload: StreamChatRequest):
    db = SessionLocal()

    # load memory (last messages) from DB
    history = get_last_messages(db, payload.session_id, limit=12)
    # build prompt context (level/topic/profile + JSON-only instructions)
    ctx = build_prompt_context(payload.message, history, db, payload.session_id)

    # save user message first
    save_message(db, payload.session_id, "You", payload.message, level=ctx["level"], topic=ctx["topic"])

    messages = ctx["ollama_messages"]

    body = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": True,
        "options": {"temperature": 0.4, "num_predict": 260}
    }

    def gen():
        full = ""
        try:
            with requests.post(OLLAMA_URL, json=body, stream=True, timeout=180) as r:
                r.raise_for_status()
                for line in r.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    data = json.loads(line)
                    if "message" in data and "content" in data["message"]:
                        chunk = data["message"]["content"]
                        full += chunk
                        # send chunk to streamlit
                        yield chunk

            # after stream ends: parse JSON and persist bot output + corrections
            parsed = safe_json_parse(full)
            bot_reply = parsed.get("reply","")
            corrections = parsed.get("corrections", [])

            # generate extra exercise from top errors
            errs = top_errors(db, payload.session_id, limit=3)
            parsed["exercise_from_progress"] = make_exercise_from_top_errors(ctx["level"], errs)

            # persist bot message + corrections
            save_message(db, payload.session_id, "Bot", bot_reply, level=ctx["level"], topic=ctx["topic"])
            save_corrections(db, payload.session_id, corrections)

            # send final JSON marker
            yield "\n\n[[FINAL_JSON]]\n" + json.dumps(parsed, ensure_ascii=False)

        finally:
            db.close()

    return StreamingResponse(gen(), media_type="text/plain")