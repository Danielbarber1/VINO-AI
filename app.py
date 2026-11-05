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
    .stButton button { border-radius: 8px; font-weight: bold; }
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

# --- סרגל צד ---
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
    st.success(f"מחובר: **{current_user}**")
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
      st.subheader("🛡️ פאנל מנהל")
      st.write(f"משתמשים רשומים: {len(st.session_state.users_db)}")

# --- תוכן ראשי ---
if not st.session_state.logged_in_user:
  st.info("👈 נא להתחבר או להירשם דרך תפריט צד ימין כדי להתחיל.")
else:
  current_user = st.session_state.logged_in_user
  user_chats = st.session_state.user_chats[current_user]
  current_chat = user_chats[st.session_state.current_chat_id]

  # הצגת היסטוריית השיחה
  for message in current_chat["messages"]:
    with st.chat_message(message["role"]):
      if isinstance(message["content"], list):
        for item in message["content"]:
          if isinstance(item, str):
            st.markdown(item)
          else:
            st.image(item, width=280)
      else:
        st.markdown(message["content"])

  # שורת הקלט והעלאת התמונה בצמוד אליה
  col_up, col_chat = st.columns([1, 4])
  with col_up:
    uploaded_file = st.file_uploader(
        "➕ תמונה", type=["png", "jpg", "jpeg"], key="img_input"
    )
  with col_chat:
    prompt = st.chat_input("שאל משהו את AI VINO...")

  if prompt or uploaded_file:
    pil_img = None
    if uploaded_file:
      pil_img = Image.open(uploaded_file)

    if not current_chat["messages"] and prompt:
      current_chat["title"] = prompt[:18] + "..."

    user_entry = []
    if prompt:
      user_entry.append(prompt)
    if pil_img:
      user_entry.append(pil_img)

    current_chat["messages"].append(
        {
            "role": "user",
            "content": user_entry if len(user_entry) > 1 else prompt,
        }
    )

    with st.chat_message("user"):
      if prompt:
        st.markdown(prompt)
      if pil_img:
        st.image(pil_img, width=280)

    with st.chat_message("assistant"):
      placeholder = st.empty()
      placeholder.markdown("חושב...")

      response_text = ""
      if not api_key:
        response_text = "⚠️ לא הוגדר מפתח API ב-Secrets."
      else:
        try:
          client = genai.Client(api_key=api_key)
          payload = []
          if prompt:
            payload.append(prompt)
          if pil_img:
            payload.append(pil_img)

          # ניסיון שימוש במודל יציב דרך ה-SDK החדש עם מנגנון הגנה
          response = client.models.generate_content(
              model="gemini-2.5-flash", contents=payload
          )
          response_text = response.text
        except Exception as e:
          try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-1.5-flash", contents=payload
            )
            response_text = response.text
          except Exception as e2:
            response_text = f"⚠️ שגיאה: {e2}"

      placeholder.markdown(response_text)
      current_chat["messages"].append(
          {"role": "assistant", "content": response_text}
      )
      st.rerun()
