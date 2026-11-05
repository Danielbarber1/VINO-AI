import os
import streamlit as st
from google import genai

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

# טעינת המפתח היחיד
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
  try:
    api_key = st.secrets.get("GEMINI_API_KEY", "")
    if not api_key:
      api_key = st.secrets.get("GEMINI_KEYS", "")
  except Exception:
    api_key = ""

st.markdown(
    "<h1 style='text-align: center; color: #f0f2f6;'>AI VINO</h1>",
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
  st.session_state.messages = []

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

for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.markdown(message["content"])

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

    if not api_key:
      response_text = "⚠️ לא הוגדר מפתח API ב-Secrets."
    else:
      try:
        client = genai.Client(api_key=api_key)
        # שימוש במודל העדכני והנתמך בספרייה החדשה
        response = client.models.generate_content(
            model="gemini-2.0-flash", contents=prompt
        )
        response_text = response.text
      except Exception as e:
        response_text = f"⚠️ שגיאה: {e}"

    placeholder.markdown(response_text)
    if not response_text.startswith("⚠️"):
      st.session_state.messages.append(
          {"role": "assistant", "content": response_text}
      )
      st.rerun()
