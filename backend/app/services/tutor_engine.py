import json, re
from collections import Counter
from .cefr_predictor import CEFRPredictor
from ..db.repo import top_errors

predictor = CEFRPredictor()
LEVEL_ORDER = ["A1","A2","B1","B2","C1","C2"]

SYSTEM_JSON = """
You are a professional English tutor.

You MUST:
- Answer the user's question directly.
- Correct the user's sentence (capitalization, punctuation, grammar).
- Provide corrections with short explanations.
- Ask ONE follow-up question related to the same topic.
- Provide ONE short micro-exercise related to the same topic.
- Keep reply under 2 sentences.

Return ONLY valid JSON (no markdown, no code fences), exactly keys:
reply, corrected_text, corrections, followup_question, exercise

corrections: array of {error, suggestion, explanation} max 5
exercise: {type, prompt, answer}
"""

def smooth_level(levels, current):
    levels = [x for x in (levels or []) if x in LEVEL_ORDER]
    if current in LEVEL_ORDER: levels.append(current)
    if not levels: return current or "A2"
    return Counter(levels).most_common(1)[0][0]

def detect_topic(text: str) -> str:
    t = (text or "").lower()
    if "irregular" in t: return "irregular_verbs"
    if any(k in t for k in ["tense","past","present","future"]): return "tenses"
    if any(k in t for k in ["food","eat"]): return "food"
    if any(k in t for k in ["study","school","exam"]): return "study"
    if any(k in t for k in ["live","city","country","from","morocco"]): return "home"
    return "general"

def extract_profile(history):
    profile = {}
    for h in history[-12:]:
        if (h.get("role") or "") == "You":
            msg = (h.get("content") or "").lower()
            m = re.search(r"\bmy name is\s+([a-z]+)", msg)
            if m: profile["name"] = m.group(1).title()
            m = re.search(r"\bi live in\s+([a-z\s]+)", msg)
            if m: profile["lives_in"] = m.group(1).strip().title()
    return profile

def safe_json_parse(text: str):
    cleaned = (text or "").strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    m = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if m: cleaned = m.group(0)

    try:
        data = json.loads(cleaned)
        data.setdefault("reply","")
        data.setdefault("corrected_text","")
        data.setdefault("corrections",[])
        data.setdefault("followup_question","")
        data.setdefault("exercise", {"type":"","prompt":"","answer":""})
        return data
    except Exception:
        return {
            "reply": cleaned[:700],
            "corrected_text": "",
            "corrections": [],
            "followup_question": "Can you tell me more?",
            "exercise": {"type":"rewrite","prompt":"Rewrite your sentence correctly.","answer":""}
        }

def make_exercise_from_top_errors(level: str, errors: list):
    # errors = [{"error":"at morocco","suggestion":"in Morocco","count":3},...]
    if not errors:
        return {"type":"", "prompt":"", "answer":""}

    e0 = errors[0]
    if level in ["A1","A2"]:
        return {
            "type":"fix_mistake",
            "prompt": f"Fix this: 'I live {e0['error']}'.",
            "answer": f"I live {e0['suggestion']}."
        }
    return {
        "type":"rewrite",
        "prompt": f"Rewrite correctly and add a reason: 'I live {e0['error']}'.",
        "answer": f"I live {e0['suggestion']} because ..."
    }

def build_prompt_context(user_text: str, history: list, db, session_id: str):
    recent_levels = [h.get("level") for h in history if h.get("level")]
    pred = predictor.predict(user_text)
    level = smooth_level(recent_levels, pred)
    topic = detect_topic(user_text)
    profile = extract_profile(history)

    # progress: top errors from db
    errs = top_errors(db, session_id, limit=3)

    # build messages for ollama
    # We include system + short conversation + user instruction
    msgs = [{"role":"system","content":SYSTEM_JSON.strip()}]

    for h in history[-10:]:
        role = (h.get("role") or "")
        content = (h.get("content") or "")
        if not content: continue
        if role == "You":
            msgs.append({"role":"user","content":content})
        elif role == "Bot":
            msgs.append({"role":"assistant","content":content})

    user_instruction = f"""
CEFR: {level}
Topic: {topic}
Profile: {profile}
Common mistakes to focus on: {errs}

User message:
{user_text}

Return JSON only.
""".strip()

    msgs.append({"role":"user","content":user_instruction})

    return {"level": level, "topic": topic, "profile": profile, "ollama_messages": msgs}
from ..db.models import Message, Correction
from .llm_tutor import call_llm
def chat(user_text: str, user, history=None, mode="conversation", db=None):
    history = history or []

    pred = predictor.predict(user_text)
    recent_levels = [h.get("level") for h in history if h.get("level")]
    level = smooth_level(recent_levels, pred)
    topic = detect_topic(user_text)
    profile = extract_profile(history)

    # Call LLM
    raw = call_llm(user_text, level, topic, profile, history)
    parsed = safe_json_parse(raw)

    # ---------------- SAVE USER MESSAGE ----------------
    user_msg = Message(
        user_id=user.id,
        role="user",
        text=user_text,
        level=level,
        topic=topic
    )
    db.add(user_msg)

    # ---------------- SAVE BOT MESSAGE ----------------
    bot_msg = Message(
        user_id=user.id,
        role="bot",
        text=parsed.get("reply",""),
        level=level,
        topic=topic
    )
    db.add(bot_msg)

    db.flush()  # باش ناخدو id

    # ---------------- SAVE CORRECTIONS ----------------
    corrections = parsed.get("corrections", [])
    for c in corrections:
        corr = Correction(
            user_id=user.id,
            error=c.get("error",""),
            suggestion=c.get("suggestion",""),
            explanation=c.get("explanation","")
        )
        db.add(corr)

    db.commit()

    return {
        "level": level,
        "topic": topic,
        **parsed
    }