import os
import time
import streamlit as st
from google import genai
from google.genai import types

# הגדרת דף עם סרגל פתוח
st.set_page_config(
    page_title="AI VINO",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# עיצוב כהה ומודרני
st.markdown(
    """
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    </style>
""",
    unsafe_allow_html=True,
)

# טעינת רשימת המפתחות מתוך ה-Secrets או הסביבה
keys_raw = os.getenv("GEMINI_KEYS")
if not keys_raw:
  try:
    keys_raw = st.secrets["GEMINI_KEYS"]
  except Exception:
    keys_raw = ""

# פיצול המפתחות לרשימה וניקוי רווחים מיותרים
api_keys = [k.strip() for k in keys_raw.split(",") if k.strip()]

# מעקב אחר אינדקס המפתח הנוכחי בזיכרון של הסשן
if "key_index" not in st.session_state:
  st.session_state.key_index = 0

# כותרת ראשית
st.markdown(
    "<h1 style='text-align: center; color: #f0f2f6;'>AI VINO</h1>",
    unsafe_allow_html=True,
)

# אתחול היסטוריה
if "messages" not in st.session_state:
  st.session_state.messages = []

# סרגל צד
with st.sidebar:
  st.title("⚙️ תפריט")
  if st.button("🔄 שיחה חדשה", use_container_width=True, key="unique_new_chat_btn"):
    st.session_state.messages = []
    st.rerun()

  st.markdown("---")
  st.subheader("📜 היסטוריית הודעות")
  if not st.session_state.messages:
    st.write("אין הודעות עדיין.")
  else:
    for i, msg in enumerate(st.session_state.messages):
      role_icon = "👤" if msg["role"] == "user" else "🤖"
      st.text(f"{role_icon} {msg['content'][:25]}...")

# הצגת ההיסטוריה
for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.markdown(message["content"])

# תיבת טקסט גדולה לכתיבה
with st.form(key="chat_form", clear_on_submit=True):
  prompt = st.text_area(
      "כתוב את ההודעה שלך כאן (אפשר כמה שורות שתרצה):",
      placeholder="שאל משהו...",
      height=100,
      key="unique_user_prompt_textarea",
  )
  submit_button = st.form_submit_button("שלח הודעה 🚀", use_container_width=True)

if submit_button and prompt.strip():
  st.session_state.messages.append({"role": "user", "content": prompt})

  with st.chat_message("user"):
    st.markdown(prompt)

  with st.chat_message("assistant"):
    placeholder = st.empty()
    placeholder.markdown("חושב...")

    response_text = ""
    success = False

    if not api_keys:
      response_text = "⚠️ לא הוגדרו מפתחות API ב-Secrets (תחת GEMINI_KEYS)."
      placeholder.markdown(response_text)
    else:
      # ננסה לעבור על המפתחות ברשימה אם מפתח מסוים נגמר
      tried_keys = 0
      total_keys = len(api_keys)

      while tried_keys < total_keys and not success:
        current_key = api_keys[st.session_state.key_index]

        try:
          client = genai.Client(api_key=current_key)

          recent_messages = st.session_state.messages[-7:-1]
          history = []
          for m in recent_messages:
            r = "user" if m["role"] == "user" else "model"
            history.append(
                types.Content(
                    role=r, parts=[types.Part.from_text(text=m["content"])]
                )
            )

          chat = client.chats.create(model="gemini-3.8-flash", history=history)
          res = chat.send_message(prompt)
          response_text = res.text
          success = True

        except Exception as e:
          err_str = str(e)
          # אם הגענו למגבלת מכסה (429 / RESOURCE_EXHAUSTED)
          if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
            tried_keys += 1
            # עוברים מיד למפתח הבא ברשימה (בלופ עגול)
            st.session_state.key_index = (
                st.session_state.key_index + 1
            ) % total_keys
            continue
          elif (
              "503" in err_str or "High Demand" in err_str or "UNAVAILABLE" in err_str
          ):
            time.sleep(1)
            continue
          else:
            response_text = f"⚠️ שגיאה: {err_str}"
            break

      if not success and not response_text:
        response_text = (
            "⚠️ כל 5 המפתחות שהוגדרו הגיעו למכסת הבקשות היומית שלהם."
        )

    placeholder.markdown(response_text)
    if success:
      st.session_state.messages.append(
          {"role": "assistant", "content": response_text}
      )
      st.rerun()
