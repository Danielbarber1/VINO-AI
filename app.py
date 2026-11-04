import requests
import streamlit as st

# ---------- הגדרות ----------
APP_NAME = "דניאל / וינו AI"
GEMINI_MODEL = "gemini-3.8-flash"  # מודל חינמי ב-Google AI Studio
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

SYSTEM_PROMPT = f"""אתה העוזר של האפליקציה "{APP_NAME}".
ענה בעברית, אלא אם המשתמש כותב בשפה אחרת. היה ברור, מדויק וידידותי.
כשמסופקות תוצאות חיפוש, התבסס עליהן, ציין מידע עדכני, והפנה למקורות בסימון [מספר].
אם התוצאות לא מספיקות או סותרות, כתוב זאת במפורש. אל תמציא עובדות."""

st.set_page_config(page_title=APP_NAME, page_icon="🤖", layout="centered")

# ---------- עיצוב ----------
st.markdown("""
<style>
    .block-container { max-width: 820px; padding-top: 2rem; }
    .brand {
        font-size: 2.4rem; font-weight: 800; text-align: center;
        background: linear-gradient(90deg, #7c3aed, #06b6d4);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0.1rem;
    }
    .subtitle { text-align: center; color: #94a3b8; margin-bottom: 1.5rem; }
    [data-testid="stChatMessage"] {
        border-radius: 16px; padding: 0.8rem 1rem; margin-bottom: 0.6rem;
        border: 1px solid rgba(124, 58, 237, 0.15);
    }
</style>
""", unsafe_allow_html=True)


# ---------- מפתחות ----------
def get_secret(name: str) -> str:
    try:
        return st.secrets.get(name, "") or ""
    except Exception:
        return ""


GEMINI_KEY = get_secret("GEMINI_API_KEY")
TAVILY_KEY = get_secret("TAVILY_API_KEY")

if not GEMINI_KEY:
    st.error("חסר מפתח GEMINI_API_KEY. הוסף אותו ל-Secrets (או ל-.streamlit/secrets.toml בהרצה מקומית).")
    st.stop()


# ---------- פונקציות עזר ----------
def search_web(query: str, max_results: int) -> list[dict]:
    """חיפוש ברשת דרך Tavily. מחזיר רשימה ריקה אם אין מפתח."""
    if not TAVILY_KEY:
        return []
    resp = requests.post(
        "https://api.tavily.com/search",
        headers={"Authorization": f"Bearer {TAVILY_KEY}"},
        json={"query": query, "max_results": max_results, "search_depth": "basic"},
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json().get("results", [])


def build_context(results: list[dict]) -> str:
    return "\n\n".join(
        f"[{i}] {r.get('title', '')}\nURL: {r.get('url', '')}\n{r.get('content', '')}"
        for i, r in enumerate(results, 1)
    )


def format_sources(results: list[dict]) -> str:
    if not results:
        return ""
    links = " | ".join(f"[{i}]({r['url']})" for i, r in enumerate(results, 1))
    return f"**מקורות:** {links}"


def ask_gemini(history: list[dict]) -> str:
    """שליחת השיחה ל-Gemini. Gemini משתמש בתפקידים 'user' ו-'model'."""
    contents = [
        {
            "role": "model" if m["role"] == "assistant" else "user",
            "parts": [{"text": m["api_content"]}],
        }
        for m in history
    ]
    resp = requests.post(
        GEMINI_URL,
        headers={"Content-Type": "application/json", "x-goog-api-key": GEMINI_KEY},
        json={
            "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": contents,
            "generationConfig": {"maxOutputTokens": 2000, "temperature": 0.7},
        },
        timeout=60,
    )
    if not resp.ok:
        raise RuntimeError(f"Gemini {resp.status_code}: {resp.text[:300]}")

    data = resp.json()
    candidate = (data.get("candidates") or [{}])[0]
    text = "".join(p.get("text", "") for p in candidate.get("content", {}).get("parts", []))
    if not text:
        reason = candidate.get("finishReason") or data.get("promptFeedback", {}).get("blockReason", "לא ידועה")
        raise RuntimeError(f"התשובה ריקה או נחסמה (סיבה: {reason})")
    return text


# ---------- סרגל צד ----------
with st.sidebar:
    st.markdown(f"## 🤖 {APP_NAME}")
    st.caption("עוזר AI חינמי (Google Gemini) עם חיפוש ברשת")
    st.divider()
    use_search = st.toggle("חיפוש ברשת (Tavily)", value=bool(TAVILY_KEY), disabled=not TAVILY_KEY)
    num_results = st.slider("מספר תוצאות חיפוש", 3, 8, 5)
    st.divider()
    if st.button("🗑️ נקה שיחה", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    if st.button("🔌 בדיקת חיבור ל-Gemini", use_container_width=True):
        try:
            test_reply = ask_gemini(
                [{"role": "user", "api_content": "ענה במילה אחת בעברית: עובד?"}]
            )
            st.success(f"החיבור תקין. תשובה: {test_reply.strip()[:100]}")
        except requests.RequestException as e:
            st.error(f"החיבור נכשל (בעיית רשת): {e}")
        except Exception as e:
            st.error(f"החיבור נכשל: {e}")

# ---------- כותרת ----------
st.markdown(f'<div class="brand">{APP_NAME}</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">שאל כל שאלה, ואענה לך בזמן אמת</div>',
    unsafe_allow_html=True,
)

# ---------- היסטוריית צ'אט ----------
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            st.markdown(msg["sources"])

# ---------- קלט משתמש ----------
if prompt := st.chat_input("כתוב שאלה..."):
    with st.chat_message("user"):
        st.markdown(prompt)

    results = []
    if use_search and TAVILY_KEY:
        with st.spinner("מחפש ברשת..."):
            try:
                results = search_web(prompt, num_results)
            except Exception as e:
                st.warning(f"החיפוש נכשל, אענה בלי מקורות חיצוניים. ({e})")

    api_content = prompt
    if results:
        api_content += f"\n\nתוצאות חיפוש עדכניות:\n{build_context(results)}"

    # ההיסטוריה שנשלחת למודל: הודעות קודמות, ואז ההודעה הנוכחית עם תוצאות החיפוש
    history_for_api = [
        {"role": m["role"], "api_content": m["content"]}
        for m in st.session_state.messages
    ]
    history_for_api.append({"role": "user", "api_content": api_content})

    sources = format_sources(results)
    with st.chat_message("assistant"):
        with st.spinner("כותב תשובה..."):
            try:
                answer = ask_gemini(history_for_api)
            except requests.RequestException as e:
                answer = f"לא הצלחתי להתחבר ל-Gemini: {e}"
            except Exception as e:
                answer = f"הייתה שגיאה בקבלת התשובה: {e}"
        st.markdown(answer)
        if sources and not answer.startswith(("לא הצלחתי", "הייתה שגיאה")):
            st.markdown(sources)

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "sources": sources}
    )
