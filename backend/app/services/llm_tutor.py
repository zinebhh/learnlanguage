import json
import requests
from typing import List, Dict, Any

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "llama3.2:3b"   # بدلها لـ llama3.1:8b إذا بغيتي

SYSTEM_TUTOR = """
You are a professional English tutor.

You MUST:
1. Correct the user's sentence.
2. Explain the corrections briefly.
3. Answer the user's question directly.
4. Ask ONE follow-up question related to the user's message.
5. Provide ONE short exercise related to the same topic.

VERY IMPORTANT:
- Output MUST be ONLY valid JSON.
- No markdown.
- No code fences.
- No extra text.
- Always fill all fields.

Return exactly this structure:

{
  "reply": "...",
  "corrected_text": "...",
  "corrections": [
      {"error": "...", "suggestion": "...", "explanation": "..."}
  ],
  "followup_question": "...",
  "exercise": {"type": "...", "prompt": "...", "answer": "..."}
}
"""

def _history_to_messages(history: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    msgs = [{"role": "system", "content": SYSTEM_TUTOR.strip()}]

    # keep last 10 turns
    for h in history[-10:]:
        role = (h.get("role") or "").lower()
        content = (h.get("content") or "").strip()
        if not content:
            continue

        if role == "you":
            msgs.append({"role": "user", "content": content})
        elif role == "bot":
            msgs.append({"role": "assistant", "content": content})

    return msgs

def call_llm(message: str, cefr_level: str, topic: str, profile: dict, history: List[Dict[str, Any]]):
    msgs = _history_to_messages(history)

    user_prompt = f"""
CEFR level: {cefr_level}
Detected topic: {topic}
Known profile facts: {profile}

User message:
{message}

Return JSON only.
""".strip()

    msgs.append({"role": "user", "content": user_prompt})

    payload = {
        "model": OLLAMA_MODEL,
        "messages": msgs,
        "stream": False,
             "options": {
  "temperature": 0.4,
  "num_predict": 300
}
    }

    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=180)
   
        r.raise_for_status()
        data = r.json()
        # Ollama returns: {"message": {"role":"assistant","content":"..."} , ...}
        return data["message"]["content"]
    except Exception:
        # fallback JSON if Ollama is not running
        return """{
  "reply":"⚠️ Local LLM (Ollama) not reachable. Make sure Ollama is running and the model is pulled.",
  "corrected_text":"",
  "corrections":[],
  "followup_question":"What do you want to practice today (home, study, food, travel)?",
  "exercise":{"type":"fill_blank","prompt":"I ___ English every day. (study/studies)","answer":"study"}
}"""