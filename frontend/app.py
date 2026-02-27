import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime

API_URL = "http://127.0.0.1:8001"

st.set_page_config(
    page_title="LearnLanguage 2026 • Tutor",
    page_icon="🧠",
    layout="wide",
)

# ---------------- SESSION ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "last" not in st.session_state:
    st.session_state.last = None

if "mode" not in st.session_state:
    st.session_state.mode = "conversation"

if "token" not in st.session_state:
    st.session_state.token = None


# ---------------- STREAM FUNCTION ----------------
def stream_chat(message: str):

    payload = {
        "message": message,
        "mode": st.session_state.mode
    }

    headers = {
        "Authorization": f"Bearer {st.session_state.token}"
    }

    r = requests.post(
        f"{API_URL}/chat",
        json=payload,
        headers=headers,
        timeout=180
    )

    r.raise_for_status()

    data = r.json()

    yield ("final", data)
# ---------------- SIDEBAR AUTH ----------------
with st.sidebar:
    st.markdown("## 🔐 Account")

    tabL, tabR = st.tabs(["Login", "Register"])

    with tabL:
        email = st.text_input("Email", key="login_email")
        pwd = st.text_input("Password", type="password", key="login_pwd")

        if st.button("Login", use_container_width=True):
            r = requests.post(
                f"{API_URL}/auth/login",
                json={"email": email, "password": pwd}
            )

            if r.status_code == 200:
                st.session_state.token = r.json()["token"]
                st.success("Logged in ✅")
                st.rerun()
            else:
                st.error(r.text)

    with tabR:
        email2 = st.text_input("Email", key="reg_email")
        username2 = st.text_input("Username", key="reg_username")
        pwd2 = st.text_input("Password", type="password", key="reg_pwd")

        if st.button("Create account", use_container_width=True):
            r = requests.post(
                f"{API_URL}/auth/register",
                json={"email": email2, "username": username2, "password": pwd2}
            )

            if r.status_code == 200:
                st.session_state.token = r.json()["token"]
                st.success("Account created ✅")
                st.rerun()
            else:
                st.error(r.text)

    if st.session_state.token:
        me = requests.get(
            f"{API_URL}/auth/me",
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )

        if me.status_code == 200:
            st.success(f"Connected as: {me.json()['username']}")

        if st.button("Logout", use_container_width=True):
            st.session_state.token = None
            st.session_state.messages = []
            st.rerun()


# ---------------- MAIN HEADER ----------------
st.title("🧠 LearnLanguage • Streaming Tutor")
st.caption("Streaming replies • Corrections • Exercises • Progress-ready")


# ---------------- INPUT ----------------
if not st.session_state.token:
    st.warning("Please login first to start chatting.")
    st.stop()

colA, colB = st.columns([5, 1])

with colA:
    user_msg = st.text_input(
        "Type your message (English)",
        placeholder="e.g., I like my city because it is calm..."
    )

with colB:
    send = st.button("Send 🚀", use_container_width=True)


# ---------------- SEND LOGIC ----------------
if send and user_msg.strip():

    ts = datetime.now().strftime("%H:%M")

    st.session_state.messages.append({
        "role": "user",
        "text": user_msg,
        "ts": ts
    })

    streamed_text = ""
    placeholder = st.empty()

    try:
        for kind, data in stream_chat(user_msg):

            if kind == "text":
                streamed_text += data
                placeholder.markdown(f"**Tutor (streaming…)**\n\n{streamed_text}")

            else:
                res = data
                st.session_state.last = res
                st.session_state.messages.append({
                    "role": "bot",
                    "text": res.get("reply", ""),
                    "ts": datetime.now().strftime("%H:%M")
                })
                break

        st.rerun()

    except Exception as e:
        st.error(f"Streaming error: {e}")


# ---------------- CHAT HISTORY ----------------
st.markdown("## 💬 Conversation")

for m in st.session_state.messages[-30:]:
    who = "You" if m["role"] == "user" else "Tutor"
    st.markdown(f"**{who} • {m['ts']}**")
    st.write(m["text"])


# ---------------- TUTOR PANEL ----------------
st.markdown("## 🧾 Tutor Panel")

res = st.session_state.last or {}

tabs = st.tabs(["Feedback", "Exercises", "Raw JSON"])

with tabs[0]:
    st.markdown("**Corrected text**")
    st.write(res.get("corrected_text", "—"))

    st.markdown("**Corrections**")
    corrections = res.get("corrections", [])
    if corrections:
        st.dataframe(pd.DataFrame(corrections))
    else:
        st.success("No corrections 🎉")

    st.markdown("**Follow-up question**")
    st.write(res.get("followup_question", "—"))

with tabs[1]:
    st.json(res.get("exercise", {}))
    st.json(res.get("exercise_from_progress", {}))

with tabs[2]:
    st.json(res)