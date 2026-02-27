import streamlit as st
import requests
import pandas as pd

API_URL = "http://127.0.0.1:8001"

st.set_page_config(
    page_title="LearnLanguage • Dashboard",
    page_icon="📊",
    layout="wide"
)

# ---------------- SESSION ----------------
if "token" not in st.session_state:
    st.session_state.token = None

# ---------------- CSS ----------------
st.markdown("""
<style>
.stApp{ background:#f6f7fb; }
.card{
  background:#ffffff;
  border:1px solid #e9ecf3;
  border-radius:16px;
  padding:16px 18px;
  box-shadow:0 10px 24px rgba(17,24,39,0.06);
}
.kpi-title{ color:#6b7280; font-size:12px; font-weight:700; }
.kpi-value{ color:#111827; font-size:26px; font-weight:900; }
.empty-state{
  padding:14px;
  border:1px dashed #d8dde8;
  border-radius:14px;
  background:#fbfcff;
  color:#6b7280;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HELPERS ----------------
def api_get(path: str, token: str, timeout=10):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{API_URL}{path}", headers=headers, timeout=timeout)
    r.raise_for_status()
    return r.json()

def api_post(path: str, payload: dict, timeout=10):
    r = requests.post(f"{API_URL}{path}", json=payload, timeout=timeout)
    return r

# ---------------- SIDEBAR: LOGIN ----------------
with st.sidebar:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("### 🔐 Account")

    if not st.session_state.token:
        email = st.text_input("Email", key="dash_email")
        pwd = st.text_input("Password", type="password", key="dash_pwd")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Login", use_container_width=True):
                resp = api_post("/auth/login", {"email": email, "password": pwd})
                if resp.status_code == 200:
                    st.session_state.token = resp.json()["token"]
                    st.success("Logged in ✅")
                    st.rerun()
                else:
                    st.error(resp.text)

        with c2:
            if st.button("Register", use_container_width=True):
                st.info("Register from main app (or add register form here).")

    else:
        # show user
        try:
            me = api_get("/auth/me", st.session_state.token, timeout=6)
            st.caption(f"Connected as: **{me.get('username','')}**")
        except Exception:
            st.caption("Connected (token)")

        if st.button("Logout", use_container_width=True):
            st.session_state.token = None
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- LOGIN CHECK ----------------
if not st.session_state.token:
    st.warning("Please login to view your dashboard.")
    st.stop()

# ---------------- LOAD DATA ----------------
try:
    data = api_get("/stats/me", st.session_state.token, timeout=10)
except Exception as e:
    st.error(f"Cannot load stats: {e}")
    st.stop()

# ---------------- KPIs ----------------
total_messages = data.get("total_messages", 0)
progression = data.get("progression", [])
messages_per_day = data.get("messages_per_day", [])
top_errors = data.get("top_errors", [])

current_level = progression[-1]["level"] if progression else "—"
active_days = len(messages_per_day) if messages_per_day else 0
top_error_text = top_errors[0]["error"] if top_errors else "—"

st.title("📊 Progress Dashboard")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='kpi-title'>Total Messages</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='kpi-value'>{total_messages}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='kpi-title'>Current Level</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='kpi-value'>{current_level}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with c3:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='kpi-title'>Active Days</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='kpi-value'>{active_days}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with c4:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='kpi-title'>Top Mistake</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='kpi-value'>{top_error_text}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# ---------------- CHARTS ----------------
left, right = st.columns(2)

with left:
    st.markdown("### 📈 CEFR Progression")

    if progression:
        dfp = pd.DataFrame(progression)

        mapping = {"A1":0,"A2":1,"B1":2,"B2":3,"C1":4,"C2":5}
        if "value" not in dfp.columns:
            dfp["value"] = dfp["level"].map(mapping).fillna(0)

        dfp["time"] = pd.to_datetime(dfp["time"], errors="coerce")
        dfp = dfp.dropna(subset=["time"]).sort_values("time").set_index("time")

        st.line_chart(dfp["value"])
        st.caption("0=A1, 1=A2, 2=B1, 3=B2, 4=C1, 5=C2")
    else:
        st.markdown("<div class='empty-state'>No progression yet.</div>", unsafe_allow_html=True)

with right:
    st.markdown("### 💬 Messages Per Day")

    if messages_per_day:
        dfm = pd.DataFrame(messages_per_day)
        dfm["day"] = pd.to_datetime(dfm["day"], errors="coerce")
        dfm = dfm.dropna(subset=["day"]).sort_values("day").set_index("day")

        st.bar_chart(dfm["count"])
    else:
        st.markdown("<div class='empty-state'>No activity yet.</div>", unsafe_allow_html=True)

st.divider()

# ---------------- TOP ERRORS ----------------
st.markdown("### ❌ Top Frequent Mistakes")

if top_errors:
    st.dataframe(pd.DataFrame(top_errors), use_container_width=True, hide_index=True)
else:
    st.markdown("<div class='empty-state'>🎉 No repeated errors yet.</div>", unsafe_allow_html=True)