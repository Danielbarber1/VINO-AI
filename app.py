import streamlit as st
import google.generativeai as genai
import time
import os

# הגדרת דף עם סרגל פתוח
st.set_page_config(
    page_title="AI VINO",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# עיצוב כהה ומודרני
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    </style>
""", unsafe_allow_html=True)

# הגדרת מפתח ה-API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        api_key = ""

if api_key:
    genai.configure(api_key=api_key)

# כותרת ראשית
st.markdown("<h1 style='text-align: center; color: #f0f2f6;'>AI VINO</h1>", unsafe_allow_html=True)

# אתחול היסטוריה
if "messages" not in st.session_state:
    st.session_state.messages = []

# סרגל צד עם מפתח ייחודי לכפתור
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

# הצגת השיחה מההיסטוריה פעם אחת בלבד
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# תיבת טקסט גדולה לכתיבת כמה שורות שתרצה
with st.form(key="chat_form", clear_on_submit=True):
    prompt = st.text_area(
        "כתוב את ההודעה שלך כאן (אפשר כמה שורות שתרצה):",
        placeholder="שאל משהו...",
        height=100,
        key="unique_user_prompt_textarea"
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
        
        # מנגנון ניסיונות למקרה שהשרת עמוס
        for attempt in range(3):
            try:
                if not api_key:
                    response_text = "⚠️ מפתח API אינו מוגדר ב-Secrets."
                    break
                
                model = genai.GenerativeModel('gemini-2.5-flash')
                chat_history = [{"role": m["role"], "parts": [m["content"]]} for m in st.session_state.messages[:-1]]
                chat = model.start_chat(history=chat_history)
                
                res = chat.send_message(prompt)
                response_text = res.text
                success = True
                break
            except Exception as e:
                if "503" in str(e) or "High Demand" in str(e) or "UNAVAILABLE" in str(e):
                    time.sleep(1)
                    continue
                response_text = f"⚠️ שגיאה זמנית בשרת, נסה שוב בעוד רגע."
                break
                
        placeholder.markdown(response_text)
        if success:
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            st.rerun()
