# דניאל / וינו AI (Streamlit + Google Gemini)

עוזר AI חינמי עם חיפוש ברשת. הקריאה ל-Gemini נעשית מהשרת, ולכן אין שגיאות Failed to fetch של הדפדפן.

## קבצים בפרויקט

```
my-ai-app-gemini/
├── app.py
├── requirements.txt
├── .gitignore
├── README.md
└── .streamlit/
    └── secrets.toml.example
```

## 1. קבלת מפתחות

**Gemini (חובה, חינם):**
1. היכנס ל-https://aistudio.google.com/app/apikey עם חשבון Google.
2. לחץ על **Create API key** והעתק את המפתח (מתחיל ב-`AIza`).

**Tavily (אופציונלי, לחיפוש ברשת):**
1. היכנס ל-https://tavily.com והירשם.
2. העתק את המפתח (מתחיל ב-`tvly-`). יש תוכנית חינמית עם מכסה חודשית.

## 2. הרצה מקומית

צור את הקובץ `.streamlit/secrets.toml` והעתק אליו את התוכן מ-`secrets.toml.example`, עם המפתחות שלך:

```toml
GEMINI_API_KEY = "AIza..."
TAVILY_API_KEY = "tvly-..."
```

אם אין לך מפתח Tavily, השאר רק את `GEMINI_API_KEY`. החיפוש ייכבה אוטומטית.

ואז בטרמינל, בתיקיית הפרויקט:

```bash
pip install -r requirements.txt
streamlit run app.py
```

האתר ייפתח בכתובת http://localhost:8501.

## 3. העלאה לאוויר בחינם (Streamlit Community Cloud)

1. העלה ל-GitHub את `app.py`, `requirements.txt`, `.gitignore` ו-`README.md`. **אל תעלה את `secrets.toml`.**
2. היכנס ל-https://share.streamlit.io והתחבר עם GitHub.
3. לחץ על **Create app** ואז על **Deploy a public app from GitHub**.
4. מלא:
   - **Repository:** שם ה-repository שלך
   - **Branch:** `main`
   - **Main file path:** `app.py`
5. לחץ על **Advanced settings** ובסעיף **Secrets** הדבק:
   ```toml
   GEMINI_API_KEY = "AIza..."
   TAVILY_API_KEY = "tvly-..."
   ```
6. לחץ על **Deploy**. אחרי דקה-שתיים תקבל קישור בסגנון `https://your-app.streamlit.app`.

## הערות

- **מכסות חינמיות:** לג'מיני יש מכסה יומית ולדקה. אם תגיע אליה, תופיע הודעת שגיאה בצ'אט, ונסה שוב מאוחר יותר.
- **פרטיות:** בתוכנית החינמית של Google, השימוש עשוי לשמש לשיפור המוצרים. אל תכניס מידע אישי או רגיש.
- **שינוי מודל:** אם `gemini-2.5-flash` לא זמין, החלף את `GEMINI_MODEL` בראש `app.py` לשם מודל אחר מתוך AI Studio.
- **שינוי בקוד:** דחוף את השינוי ל-GitHub, והאפליקציה תתעדכן אוטומטית.
