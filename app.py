import random
import time
import uuid

import requests
import streamlit as st

# ---------- הגדרות ----------
APP_NAME = "AI VINO"
GEMINI_MODEL = "gemini-3.8-flash"  # מודל חינמי ב-Google AI Studio
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
NUM_SEARCH_RESULTS = 5

SYSTEM_PROMPT = f"""אתה העוזר של האפליקציה "{APP_NAME}".
ענה בעברית, אלא אם המשתמש כותב בשפה אחרת. היה ברור, מדויק וידידותי.
כשמסופקות תוצאות חיפוש, התבסס עליהן, ציין מידע עדכני, והפנה למקורות בסימון [מספר].
אם התוצאות לא מספיקות או סותרות, כתוב זאת במפורש. אל תמציא עובדות."""

BUSY_MESSAGE = "השרתים של הבינה המלאכותית עמוסים כרגע. נסה שוב בעוד רגע."

st.set_page_config(page_title=APP_NAME, page_icon="🤖", layout="centered")

# ---------- עיצוב ----------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@400;500;700;800&display=swap');

    html, body, [class*="css"], .stApp {
        font-family: 'Heebo', system-ui, -apple-system, 'Segoe UI', Arial, sans-serif;
    }
    .stApp {
        background:
            radial-gradient(1000px 500px at 85% -10%, rgba(124,58,237,.20), transparent 60%),
            radial-gradient(800px 500px at -10% 110%, rgba(6,182,212,.14), transparent 60%),
            #0b0b14;
    }
    .block-container { max-width: 860px; padding-top: 2.2rem; padding-bottom: 6rem; }
    #MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }

    .brand {
        font-size: 2.6rem; font-weight: 800; text-align: center; letter-spacing: -0.5px;
        background: linear-gradient(90deg, #a78bfa, #7c3aed 40%, #06b6d4);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .subtitle { text-align: center; color: #94a3b8; margin-bottom: 1.8rem; font-size: 1.02rem; }

    [data-testid="stChatMessage"] {
        border-radius: 18px; padding: 0.9rem 1.1rem; margin-bottom: 0.8rem;
        background: rgba(22, 22, 38, 0.78);
        border: 1px solid rgba(124, 58, 237, 0.18);
        box-shadow: 0 8px 24px rgba(0,0,0,.25);
        line-height: 1.75; color: #e8eaf3;
    }
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
        background: linear-gradient(135deg, rgba(124,58,237,.35), rgba(6,182,212,.18));
        border: 1px solid rgba(167, 139, 250, .35);
    }
    [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li { font-size: 1rem; }
    [data-testid="stChatMessage"] a { color: #67e8f9; text-decoration: none; }
    [data-testid="stChatMessage"] a:hover { text-decoration: underline; }

    [data-testid="stChatInput"] {
        background: rgba(19, 19, 31, .92);
        border: 1px solid rgba(124, 58, 237, .35);
        border-radius: 16px;
        box-shadow: 0 0 0 4px rgba(124,58,237,.08);
    }
    [data-testid="stChatInput"]:focus-within {
        border-color: #7c3aed;
        box-shadow: 0 0 0 4px rgba(124,58,237,.22);
    }
    [data-testid="stChatInput"] textarea { color: #eef0f7 !important; }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #13131f 0%, #0d0d18 100%);
        border-left: 1px solid rgba(124,58,237,.2);
    }
    [data-testid="stSidebar"] h2 { font-weight: 800; }

    .stButton > button {
        border-radius: 12px; border: 1px solid rgba(124,58,237,.45);
        background: rgba(124,58,237,.12); color: #eef0f7; font-weight: 600;
        padding: 0.45rem 0.9rem; transition: all .2s ease;
    }
    .stButton > button:hover {
        border-color: #a78bfa; background: linear-gradient(90deg, #7c3aed, #06b6d4);
        color: #fff; transform: translateY(-1px); box-shadow: 0 6px 18px rgba(124,58,237,.35);
    }
    .stButton > button:active { transform: translateY(0); }

    [data-testid="stAlert"] { border-radius: 14px; }
    [data-testid="stSpinner"] { color: #a78bfa; }
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-thumb { background: rgba(124,58,237,.35); border-radius: 8px; }
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


# ---------- ניהול שיחות (st.session_state) ----------
def new_chat() -> None:
    chat_id = uuid.uuid4().hex[:8]
    st.session_state.chats[chat_id] = {"title": "שיחה חדשה", "messages": []}
    st.session_state.current_id = chat_id


if "chats" not in st.session_state:
    st.session_state.chats = {}
    st.session_state.current_id = None
if st.session_state.current_id not in st.session_state.chats:
    new_chat()


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


class GeminiError(RuntimeError):
    """שגיאה מ-Gemini, עם קוד הסטטוס של התשובה."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


RETRYABLE_STATUS = {429, 500, 502, 503, 504}  # עומס, תקלה זמנית ומגבלת קצב


def ask_gemini(history: list[dict], max_attempts: int = 8, base_delay: float = 2.0, max_delay: float = 20.0) -> str:
    """
    קריאה ל-Gemini עם ניסיון חוזר אוטומטי.
    בשגיאות עומס (503 / 429) או בעיות רשת, ממתינים ומנסים שוב בלי להציג שגיאה למשתמש.
    שגיאות אחרות (כמו מפתח שגוי) נזרקות מיד.
    """
    for attempt in range(1, max_attempts + 1):
        try:
            return _ask_gemini_once(history)
        except GeminiError as e:
            if e.status not in RETRYABLE_STATUS or attempt == max_attempts:
                raise
        except requests.RequestException:
            if attempt == max_attempts:
                raise
        wait = min(base_delay * (2 ** (attempt - 1)), max_delay)
        time.sleep(wait + random.uniform(0, 1))
    raise RuntimeError("נכשל אחרי מספר ניסיונות")


def _ask_gemini_once(history: list[dict]) -> str:
    """ניסיון יחיד מול Gemini. Gemini משתמש בתפקידים 'user' ו-'model'."""
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
        raise GeminiError(resp.status_code, f"Gemini {resp.status_code}: {resp.text[:300]}")

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
    if st.button("➕ שיחה חדשה", use_container_width=True, type="primary"):
        new_chat()
        st.rerun()

    use_search = st.toggle("חיפוש ברשת", value=bool(TAVILY_KEY), disabled=not TAVILY_KEY)

    st.divider()
    st.markdown("**היסטוריית שיחות**")
    for cid in reversed(list(st.session_state.chats.keys())):
        chat = st.session_state.chats[cid]
        marker = "● " if cid == st.session_state.current_id else ""
        col_open, col_del = st.columns([5, 1])
        if col_open.button(marker + chat["title"], key=f"open_{cid}", use_container_width=True):
            st.session_state.current_id = cid
            st.rerun()
        if col_del.button("🗑", key=f"del_{cid}"):
            del st.session_state.chats[cid]
            if cid == st.session_state.current_id:
                st.session_state.current_id = None
            st.rerun()

# ---------- כותרת ----------
st.markdown(f'<div class="brand">{APP_NAME}</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">שאל כל שאלה, ואענה לך בזמן אמת</div>', unsafe_allow_html=True)

current = st.session_state.chats[st.session_state.current_id]

# ---------- הצגת השיחה ----------
for msg in current["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            st.markdown(msg["sources"])

# ---------- קלט משתמש ----------
if prompt := st.chat_input("כתוב שאלה..."):
    if not current["messages"]:
        current["title"] = prompt[:30] + ("…" if len(prompt) > 30 else "")
    current["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    results = []
    if use_search and TAVILY_KEY:
        with st.spinner("מחפש ברשת..."):
            try:
                results = search_web(prompt, NUM_SEARCH_RESULTS)
            except Exception:
                results = []  # אם החיפוש נכשל, ממשיכים בלי מקורות

    api_content = prompt
    if results:
        api_content += f"\n\nתוצאות חיפוש עדכניות:\n{build_context(results)}"

    # היסטוריה למודל: הודעות קודמות שלא נכשלו, ואז ההודעה הנוכחית עם תוצאות החיפוש
    api_history = [
        {"role": m["role"], "api_content": m["content"]}
        for m in current["messages"][:-1]
        if not m.get("error")
    ]
    api_history.append({"role": "user", "api_content": api_content})

    sources = format_sources(results)
    with st.chat_message("assistant"):
        is_error = False
        with st.spinner("כותב תשובה..."):
            try:
                answer = ask_gemini(api_history)
            except GeminiError as e:
                is_error = True
                if e.status in RETRYABLE_STATUS:
                    answer = BUSY_MESSAGE
                else:
                    answer = f"הייתה שגיאה בקבלת התשובה: {e}"
            except Exception as e:
                is_error = True
                answer = BUSY_MESSAGE if isinstance(e, requests.RequestException) else f"הייתה שגיאה: {e}"
        st.markdown(answer)
        if sources and not is_error:
            st.markdown(sources)

    current["messages"].append(
        {
            "role": "assistant",
            "content": answer,
            "sources": "" if is_error else sources,
            "error": is_error,
        }
    )
