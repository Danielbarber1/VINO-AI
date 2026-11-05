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

# ניהול סשנים של שיחות
if "chats" not in st.session_state:
  st.session_state.chats = {}
if "current_chat_id" not in st.session_state:
  st.session_state.current_chat_id = None
if "user_email" not in st.session_state:
  st.session_state.user_email = ""
if "user_name" not in st.session_state:
  st.session_state.user_name = "אורח"


def create_new_chat():
  chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
  st.session_state.chats[chat_id] = {
      "title": f"שיחה {len(st.session_state.chats) + 1}",
      "messages": [],
  }
  st.session_state.current_chat_id = chat_id


if (
    not st.session_state.chats
    or st.session_state.current_chat_id not in st.session_state.chats
):
  create_new_chat()

st.markdown("<h1>AI VINO</h1>", unsafe_allow_html=True)

# סרגל צד
with st.sidebar:
  st.title("⚙️ תפריט")

  if not st.session_state.user_email:
    st.info("התחבר באמצעות Google:")
    login_email = st.text_input("הכנס כתובת מייל:", key="login_email_input")
    if st.button("התחבר 🔵", use_container_width=True):
      if login_email.strip():
        st.session_state.user_email = login_email.strip()
        st.session_state.user_name = login_email.split("@")[0]
        st.rerun()
  else:
    st.success(f"מחובר: **{st.session_state.user_name}**")
    if st.button("התנתק", use_container_width=True):
      st.session_state.user_email = ""
      st.session_state.user_name = "אורח"
      st.rerun()

  st.markdown("---")

  if st.button("➕ שיחה חדשה", use_container_width=True):
    create_new_chat()
    st.rerun()

  st.markdown("### 📜 השיחות שלי")
  for cid, cdata in list(st.session_state.chats.items()):
    label = f"💬 {cdata['title']}"
    if cid == st.session_state.current_chat_id:
      label = f"👉 {cdata['title']}"
    if st.button(label, key=f"chat_btn_{cid}", use_container_width=True):
      st.session_state.current_chat_id = cid
      st.rerun()

  if (
      st.session_state.user_email == ADMIN_EMAIL
      or "admin" in st.session_state.user_email
  ):
    st.markdown("---")
    st.subheader("🛡️ פאנל מנהל")
    st.write("מצב מנהל פעיל.")

# טעינת השיחה הנוכחית
current_chat = st.session_state.chats[st.session_state.current_chat_id]

# הצגת היסטוריית ההודעות בשיחה
for message in current_chat["messages"]:
  with st.chat_message(message["role"]):
    if isinstance(message["content"], list):
      for item in message["content"]:
        if isinstance(item, str):
          st.markdown(item)
        else:
          st.image(item, width=300)
    else:
      st.markdown(message["content"])

# אזור הוספת תמונה בצמוד למטה ליד כפתור השליחה
uploaded_file = st.file_uploader(
    "➕ הוסף תמונה (אופציונלי)", type=["png", "jpg", "jpeg"]
)

# שורת הקלט של הצ'אט
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
      {"role": "user", "content": user_entry if len(user_entry) > 1 else prompt}
  )

  with st.chat_message("user"):
    if prompt:
      st.markdown(prompt)
    if pil_img:
      st.image(pil_img, width=300)

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

        # שימוש במודל יציב ומהיר
        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=payload
        )
        response_text = response.text
      except Exception as e:
        # גיבוי למקרה שהמודל הקודם לא זמין
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
