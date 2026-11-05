import os
from datetime import datetime
import streamlit as st
from google import genai
from PIL import Image

st.set_page_config(
    page_title="AI VINO",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# עיצוב מותאם: כחול-לבן עם כותרת סגולה מודרנית
st.markdown(
    """
    <style>
    .main { background-color: #0b1329; color: #ffffff; }
    .stTextInput textarea, .stChatInput input { background-color: #1e293b !important; color: #ffffff !important; }
    h1 { color: #a855f7 !important; text-align: center; font-weight: 800; font-size: 2.8rem; }
    .stButton button { border-radius: 8px; font-weight: bold; }
    </style>
""",
    unsafe_allow_html=True,
)

# טעינת מפתח API מכל המקורות האפשריים
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
  try:
    api_key = (
        st.secrets.get("GEMINI_API_KEY", "")
        or st.secrets.get("GEMINI_KEYS", "")
        or ""
    )
  except Exception:
    api_key = ""

ADMIN_EMAIL = "daniel@gmail.com"

# 1. מנגנון משתמשים בזיכרון המערכת
if "users_db" not in st.session_state:
  st.session_state.users_db = {ADMIN_EMAIL: "123456"}
if "logged_in_user" not in st.session_state:
  st.session_state.logged_in_user = None

# 2. מנגנון שיחות נפרדות לפי משתמש
if "user_chats" not in st.session_state:
  st.session_state.user_chats = {}
if "current_chat_id" not in st.session_state:
  st.session_state.current_chat_id = None

st.markdown("<h1>AI VINO</h1>", unsafe_allow_html=True)

# --- סרגל צד: ניהול משתמש ושיחות ---
with st.sidebar:
  st.title("⚙️ תפריט מערכת")

  if not st.session_state.logged_in_user:
    auth_mode = st.radio(
        "בחר פעולה:", ["התחברות", "הרשמה למערכת"], label_visibility="collapsed"
    )
    email_input = st.text_input("כתובת מייל:")
    pass_input = st.text_input("סיסמה:", type="password")

    if auth_mode == "התחברות":
      if st.button("התחבר 🔵", use_container_width=True):
        if (
            email_input in st.session_state.users_db
            and st.session_state.users_db[email_input] == pass_input
        ):
          st.session_state.logged_in_user = email_input
          if email_input not in st.session_state.user_chats:
            st.session_state.user_chats[email_input] = {}
          st.rerun()
        else:
          st.error("שגיאה במייל או בסיסמה.")
    else:
      if st.button("הירשם 🟢", use_container_width=True):
        if email_input.strip() and pass_input.strip():
          if email_input in st.session_state.users_db:
            st.warning("המשתמש כבר קיים במערכת.")
          else:
            st.session_state.users_db[email_input] = pass_input
            st.session_state.user_chats[email_input] = {}
            st.session_state.logged_in_user = email_input
            st.success("נרשמת בהצלחה!")
            st.rerun()
        else:
          st.warning("נא למלא מייל וסיסמה.")
  else:
    current_user = st.session_state.logged_in_user
    st.success(f"מחובר כ: **{current_user}**")
    if st.button("התנתק", use_container_width=True):
      st.session_state.logged_in_user = None
      st.session_state.current_chat_id = None
      st.rerun()

    st.markdown("---")

    user_chats = st.session_state.user_chats[current_user]


    def create_user_chat():
      cid = datetime.now().strftime("%Y%m%d_%H%M%S")
      user_chats[cid] = {
          "title": f"שיחה {len(user_chats) + 1}",
          "messages": [],
      }
      st.session_state.current_chat_id = cid


    if not user_chats or st.session_state.current_chat_id not in user_chats:
      create_user_chat()

    if st.button("➕ שיחה חדשה", use_container_width=True):
      create_user_chat()
      st.rerun()

    st.markdown("### 📜 השיחות שלי")
    for cid, cdata in list(user_chats.items()):
      label = f"💬 {cdata['title']}"
      if cid == st.session_state.current_chat_id:
        label = f"👉 {cdata['title']}"
      if st.button(label, key=f"chat_btn_{cid}", use_container_width=True):
        st.session_state.current_chat_id = cid
        st.rerun()

    if current_user == ADMIN_EMAIL:
      st.markdown("---")
      st.subheader("🛡️ פאנל מנהל (Admin)")
      st.write(f"👥 משתמשים רשומים: {len(st.session_state.users_db)}")
      st.write(f"💬 סך כל השיחות: {len(user_chats)}")

# --- אזור ת
