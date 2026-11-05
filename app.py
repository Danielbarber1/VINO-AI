import os
import time
import streamlit as st
from google import genai
from google.genai import types

# הגדרת דף
st.set_page_config(
    page_title="AI VINO",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    </style>
""",
    unsafe_allow_html=True,
)

# טעינת המפתחות
keys_raw = os.getenv("GEMINI_KEYS")
if not keys_raw:
  try:
    keys_raw = st.secrets["GEMINI_KEYS"]
  except Exception:
    keys_raw = ""

api_keys = [k.strip() for k in keys_raw.split(",") if k.strip()]

if "key_index" not in st.session_state:
  st.session_state.key_index = 0

st.markdown(
    "<h1 style='text-align: center; color: #f0f2f6;'>AI VINO</h1>",
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
  st.session_state.messages = []

# סרגל צד
with st.sidebar:
  st.title("⚙️ תפריט")
  if st.button("🔄 שיחה חדשה", use_container_width=True, key="new_chat_btn"):
    st.session_state.messages = []
    st.rerun()

  st.markdown("---")
  st.subheader("📜 היסטוריה")
  if not st.session_state.messages:
    st.write("אין הודעות עדיין.")
  else:
    for msg in st.session_state.messages:
      icon = "👤" if msg["role"] == "user" else "🤖"
      st.text(f"{icon} {msg['content'][:25]}...")

# הצגת היסטוריה
for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.markdown(message["content"])

# טופס שליחה
with st.form(key="chat_form", clear_on_submit=True):
  prompt = st.text_area(
      "כתוב את ההודעה שלך כאן:",
      placeholder="שאל משהו...",
      height=100,
      key="user_prompt_input",
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
      response_text = "⚠️ לא הוגדרו מפתחות ב-GEMINI_KEYS."
      placeholder.markdown(response_text)
    else:
      tried_keys = 0
      total_keys = len(api_keys)

      while tried_keys < total_keys and not success:
        current_key = api_keys[st.session_state.key_index]

        try:
          # אתחול הלקוח מחדש עבור המפתח הנוכחי
          client = genai.Client(api_key=current_key)

          # שליחה ישירה
          response = client.models.generate_content(
              model="gemini-2.5-flash", contents=prompt
          )

          response_text = response.text
          success = True

        except Exception as e:
          err_str = str(e)
          # מעבר למפתח הבא במקרה של שגיאת מכסה או הרשאה
          if (
              "429" in err_str
              or "RESOURCE_EXHAUSTED" in err_str
              or "401" in err_str
              or "UNAUTHENTICATED" in err_str
          ):
            tried_keys += 1
            st.session_state.key_index = (
                st.session_state.key_index + 1
            ) % total_keys
          elif "503" in err_str or "UNAVAILABLE" in err_str:
            time.sleep(1)
            tried_keys += 1
          else:
            response_text = f"⚠️ שגיאה: {err_str}"
            break

      if not success and not response_text:
        response_text = "⚠️ כל המפתחות הגיעו למגבלה או שאינם תקינים."

    placeholder.markdown(response_text)
    if success:
      st.session_state.messages.append(
          {"role": "assistant", "content": response_text}
      )
      st.rerun()
