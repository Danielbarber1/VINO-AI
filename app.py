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

st.markdown(
    """
    <style>
    .main { background-color: #0b1329; color: #ffffff; }
    .stTextInput textarea, .stChatInput input { background-color: #1e293b !important; color: #ffffff !important; }
    h1 { color: #a855f7 !important; text-align: center; font-weight: 800; }
    </style>
""",
    unsafe_allow_html=True,
)

# טעינת מפתח API
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

# ניהול משתמשים וסיסמאות
if "users_db" not in st.session_state:
  st.session_state.users_db = {ADMIN_EMAIL: "123456"}
if "logged_in_user" not in st.session_state:
  st.session_state.logged_in_user = None

# ניהול שיחות
if "user_chats" not in st.session_state:
  st.session_state.user_chats = {}
if "current_chat_id" not in st.session_state:
  st.session_state.current_chat_id = None

st.markdown("<h1>AI VINO</h1>", unsafe_allow_html=True)

with st.sidebar:
  st.title("⚙️ תפריט משתמש")

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
            and
