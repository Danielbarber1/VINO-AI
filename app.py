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

# עיצוב מותאם: כחול-לבן עם כותרת סגולה וממשק נקי
st.markdown(
    """
    <style>
    .main { background-color: #0b1329; color: #ffffff; }
    .stTextInput textarea, .stChatInput input { background-color: #1e293b !important; color: #ffffff !important; }
    h1 { color: #a855f7 !important; text-align: center; font-weight: 800; }
    .sidebar .sidebar-content { background-color: #0f172a; }
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

# הגדרת מנהל המערכת (הכנס כאן את המייל שלך או השאר ברירת מחדל)
ADMIN_EMAIL = "daniel@gmail.com"

# ניהול מצב משתמש והיסטוריה בסשן
if "messages" not in st.session_state:
  st.session_state.messages = []
if "user_email" not in st.session_state:
  st.session_state.user_email = ""
if "user_name" not in st.session_state:
  st.session_state.user_name = "אורח"

st.markdown("<h1>AI VINO</h1>", unsafe_allow_html=True)

# סרגל צד מתקדם
with st.sidebar:
  st.title("⚙️ תפריט מערכת")

  # אזור התחברות מדמה למשתמשי גוגל
  if not st.session_state.user_email:
    st.info("התחבר באמצעות חשבון Google שלך:")
    login_email_input = st.text_input("הכנס כתובת מייל:")
    if st.button("התחבר 🔵", use_container_width=True):
      if login_email_input.strip():
        st.session_state.user_email = login_email_input.strip()
        st.session_state.user_name = login_email_input.split("@")[0]
        st.rerun()
  else:
    st.success(f"מחובר בשם: **{st.session_state.user_name}**")
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
    st.write("אין היסטוריה פעילה בשיחה זו.")
  else:
    for idx, msg in enumerate(st.session_state.messages):
      prefix = "👤" if msg["role"] == "user" else "🤖"
      # הצגת תקציר ההודעה בהיסטוריה
      content_preview = (
          msg["content"]
          if isinstance(msg["content"], str)
          else "[הודעת תמונה]"
      )
      st.text(f"{prefix} {content_preview[:20]}...")

  # פאנל ניהול מיוחד למנהל בלבד
  if (
      st.session_state.user_email == ADMIN_EMAIL
      or "admin" in st.session_state.user_email
  ):
    st.markdown("---")
    st.subheader("🛡️ פאנל מנהל (Admin)")
    st.markdown("ברוך הבא, מנהל המערכת!")
    admin_action = st.selectbox(
        "בחר פעולת ניהול:",
        ["צפה בסטטיסטיקות", "נקה מטמון מערכת", "הגדרות סקילים מתקדמות"],
    )
    if st.button("בצע פעולת מנהל", use_container_width=True):
      st.success(f"הפעולה '{admin_action}' בוצעה בהצלחה!")

# הצגת היסטוריית הצ'אט במסך הראשי
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

# אזור קלט הכולל טקסט ואפשרות הוספת תמונה
st.markdown("---")
uploaded_file = st.file_uploader(
    "העלה תמונה (אופציונלי):", type=["png", "jpg", "jpeg"]
)
prompt = st.text_area(
    "כתוב את ההודעה שלך כאן:", placeholder="שאל משהו את AI VINO..."
)

col1, col2 = st.columns([6, 1])
with col2:
  send_btn = st.button("שלח 🚀", use_container_width=True)

if send_btn and (prompt.strip() or uploaded_file):
  user_content = []
  if prompt.strip():
    user_content.append(prompt)

  pil_img = None
  if uploaded_file:
    pil_img = Image.open(uploaded_file)
    user_content.append(pil_img)

  # הוספה להיסטוריה
  st.session_state.messages.append({"role": "user", "content": user_content})

  with st.chat_message("user"):
    if prompt.strip():
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

        # בניית מבנה התוכן לשליחה למודל (תמיכה בתמונה + טקסט)
        contents_payload = []
        if prompt.strip():
          contents_payload.append(prompt)
        if pil_img:
          contents_payload.append(pil_img)

        response = client.models.generate_content(
            model="gemini-2.0-flash", contents=contents_payload
        )
        response_text = response.text
      except Exception as e:
        response_text = f"⚠️ שגיאה בתקשורת מול ה-AI: {e}"

    placeholder.markdown(response_text)
    st.session_state.messages.append(
        {"role": "assistant", "content": response_text}
    )
    st.rerun()
