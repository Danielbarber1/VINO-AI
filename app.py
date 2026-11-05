import os
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

# אתחול היסטוריה ומשתמש
if "messages" not in st.session_state:
  st.session_state.messages = []
if "user_email" not in st.session_state:
  st.session_state.user_email = ""
if "user_name" not in st.session_state:
  st.session_state.user_name = "אורח"

st.markdown("<h1>AI VINO</h1>", unsafe_allow_html=True)

# סרגל צד
with st.sidebar:
  st.title("⚙️ תפריט מערכת")

  if not st.session_state.user_email:
    st.info("התחבר באמצעות חשבון Google:")
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

  if st.button("🔄 שיחה חדשה", use_container_width=True):
    st.session_state.messages = []
    st.rerun()

  st.markdown("### 📜 היסטוריית שיחות")
  if not st.session_state.messages:
    st.write("אין הודעות בהיסטוריה.")
  else:
    for msg in st.session_state.messages:
      icon = "👤" if msg["role"] == "user" else "🤖"
      txt = (
          msg["content"]
          if isinstance(msg["content"], str)
          else "[הודעת תמונה]"
      )
      st.text(f"{icon} {txt[:22]}...")

  # פאנל מנהל
  if (
      st.session_state.user_email == ADMIN_EMAIL
      or "admin" in st.session_state.user_email
  ):
    st.markdown("---")
    st.subheader("🛡️ פאנל מנהל")
    st.write("מצב מנהל פעיל בהצלחה.")

# הצגת כל ההיסטוריה מתוך st.session_state בכל טעינה מחדש
for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    if isinstance(message["content"], list):
      for item in message["content"]:
        if isinstance(item, str):
          st.markdown(item)
        else:
          st.image(item, width=300)
    else:
      st.markdown(message["content"])

# קלט מהמשתמש באמצעות st.chat_input (הדרך הטבעית והיציבה ביותר בשטרימלייט לשמירת שיחות)
prompt = st.chat_input("שאל משהו את AI VINO...")
uploaded_file = st.file_uploader(
    "העלה תמונה (אופציונלי):", type=["png", "jpg", "jpeg"]
)

if prompt or uploaded_file:
  user_content = []
  if prompt:
    user_content.append(prompt)

  pil_img = None
  if uploaded_file:
    pil_img = Image.open(uploaded_file)
    user_content.append(pil_img)

  # שמירת הודעת המשתמש בסשן
  st.session_state.messages.append(
      {
          "role": "user",
          "content": prompt if not uploaded_file else user_content,
      }
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
        contents_payload = [prompt] if prompt else []
        if pil_img:
          contents_payload.append(pil_img)

        response = client.models.generate_content(
            model="gemini-2.0-flash", contents=contents_payload
        )
        response_text = response.text
      except Exception as e:
        response_text = f"⚠️ שגיאה: {e}"

    placeholder.markdown(response_text)

    # שמירת תשובת הבוט בסשן כדי שתופיע בהיסטוריה תמיד
    st.session_state.messages.append(
        {"role": "assistant", "content": response_text}
    )
    st.rerun()
