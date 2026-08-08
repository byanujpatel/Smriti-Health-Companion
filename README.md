# Smriti — Dadi Ka Health Saathi

> *"Mummy ko chakkar aa raha tha aaj — yaad rakhna"*
> "Mummy had dizziness today — remember this."

Smriti is a family health memory app built for ageing parents in India and the children who care for them from a distance.

**Dadi** speaks a quick note in Hindi — on WhatsApp/Telegram or the web app. **Beti in Mumbai** checks the family dashboard and asks *"Has she mentioned dizziness before?"* — Smriti answers with exact dates and quotes.

- 🔗 **Live app:** `PASTE_RENDER_URL_HERE`
- 📹 **Build screencast:** `PASTE_LOOM_URL_HERE`
- 💬 **Telegram bot:** `PASTE_BOT_USERNAME_HERE`

---

## The problem it solves

India has 140 million people over 60. Most of them live apart from their adult children. Every family has some version of this:

- Papa had a fall last month — no one remembered until the next visit
- Dadi's BP has been high for three weeks — no one connected the dots
- "Did the doctor say anything about her knee?" — no one wrote it down

Smriti is a memory for health moments — saved automatically when you speak, recalled instantly when you ask.

---

## Who it's for

**Elder (Dadi / Papa)** — speaks or types a health note in Hindi or English. No login, no forms. Just say what happened.

**Caregiver (Beti / Beta)** — opens the family dashboard from any city. Sees recent flags, urgency level, and a full timeline of remembered moments. Asks questions in plain language.

---

## Key features

| Feature | What it does |
|---|---|
| 🎙️ Voice check-in | Speak in Hindi/English → Groq Whisper transcribes → structured memory saved |
| 📋 Prescription scan | Upload a prescription photo or PDF → AI extracts medicine names and doses |
| 💬 Ask anything | "Has she mentioned dizziness?" → answers from saved memories with dates and quotes |
| 👨‍👩‍👧 Family dashboard | Caregiver view: urgency level, flags, recent timeline, pattern summary |
| 🤖 Telegram bot | `/start`, voice note, text note, `/ask` — works on any phone |
| 🆘 Emergency alert | One-tap emergency → logged memory + email alert to family |
| 📅 Weekly patterns | "Noticed changes this week?" — AI summarises recurring symptoms |
| 🔒 Per-person memory | Separate memories per person — Mummy and Papa never mix |

---

## How the AI pipeline works

```
Elder speaks (voice or text)
       │
       ▼
Groq Whisper (STT)        ← whisper-large-v3-turbo
       │
       ▼
Groq Llama (structure)    ← llama-3.3-70b-versatile
  turns free text into:
    type / date / entities / tags
       │
       ▼
Preview card shown         ← caregiver/elder confirms before saving
       │
       ▼
Supermemory Cloud          ← semantic + hybrid search index
       │
       ▼
Ask a question
       │
       ▼
Supermemory search  →  Groq Llama answer  →  reply with sources + dates
```

---

## Try it in 60 seconds

1. Open the live URL above.
2. Skip login — type a name like `Asha Devi` or `Papa` and tap **Shuru karein**.
3. On the home screen tap **BOLIYE** and say *"Aaj BP 150 tha, thoda chakkar aaya"*.
4. Review the preview card → tap **SAHI HAI — Save Karein**.
5. Switch to the **Ask** tab → ask *"Has she mentioned dizziness?"*
6. Tap **👨‍👩‍👧 Family** in the bottom nav → see the caregiver dashboard.

Or load the built-in demo:

```bash
curl -X POST https://YOUR-RENDER-URL/demo/load
```

This loads 9 memories for **Asha Devi** (68, Varanasi, BP patient). Use subject ID `asha-devi` in all requests.

---

## Telegram bot

1. Search for `@SmritiDadiBot` on Telegram.
2. Send `/start` → enter your parent's name.
3. Send a voice note in Hindi.
4. Smriti replies with a structured preview → tap ✅ to save.
5. Send `/ask Has she had dizziness before?`

---

## Local setup

**Requirements:** Python 3.11+, [uv](https://docs.astral.sh/uv/)

### 1. Clone and install

```bash
git clone https://github.com/YOUR-USERNAME/smriti
cd smriti
uv sync
```

### 2. Create `.env`

```env
# Memory
SMRITI_MEMORY_MODE=cloud
SUPERMEMORY_API_KEY=your-supermemory-key

# AI
GROQ_API_KEY=your-groq-key
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_STT_MODEL=whisper-large-v3-turbo
GROQ_VISION_MODEL=meta-llama/llama-4-scout-17b-16e-instruct

# Optional: Telegram bot
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
WEBHOOK_URL=https://your-app.onrender.com

# Optional: Emergency email via Gmail
ALERT_EMAIL=family@example.com
SMTP_USER=sender@gmail.com
SMTP_PASS=your-app-password
```

For **local-only testing** (no cloud):

```env
SMRITI_MEMORY_MODE=local
SUPERMEMORY_BASE_URL=http://localhost:6767
SUPERMEMORY_API_KEY=any-local-key
```

Start Supermemory Local first: `supermemory-server`

### 3. Start the app

```bash
UV_CACHE_DIR=/private/tmp/uv-cache uv run uvicorn main:app --reload --port 8000
```

Open: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## Deploy to Render

1. Push this repo to GitHub (public).
2. Create a new **Web Service** in Render → connect the repo.
3. Render auto-detects `render.yaml` — no extra config needed.
4. Set all environment variables in Render dashboard (see `.env` above).
5. Deploy → copy the live URL → update `WEBHOOK_URL` in env vars.
6. (Optional) Set Telegram webhook: `curl -F "url=https://YOUR-URL/telegram" https://api.telegram.org/botTOKEN/setWebhook`

---

## API reference (quick)

| Method | Path | What it does |
|---|---|---|
| `GET` | `/` | Web app |
| `GET` | `/health` | `{"status":"ok"}` |
| `POST` | `/ingest/preview` | Text → structured memory preview |
| `POST` | `/memories` | Save confirmed memories |
| `POST` | `/ask` | Ask a question, get answer + sources |
| `POST` | `/checkin` | Voice check-in → summary + auto-save |
| `POST` | `/summary` | Weekly/monthly visit summary |
| `POST` | `/patterns` | Recurring symptom patterns |
| `POST` | `/documents/preview` | PDF/photo prescription → memory cards |
| `POST` | `/voice/transcribe` | Audio file → transcribed text |
| `GET` | `/api/dashboard/{id}` | Caregiver dashboard data |
| `POST` | `/api/emergency` | Log emergency + send alert email |
| `POST` | `/telegram` | Telegram webhook (auto-set on startup) |
| `POST` | `/demo/load` | Load Asha Devi demo data |

Full interactive docs: `/docs`

---

## Run tests

```bash
UV_CACHE_DIR=/private/tmp/uv-cache uv run pytest -q
```

---

## Code layout

```
main.py                     FastAPI routes, dashboard helpers, emergency email
telegram_bot.py             Telegram bot: /start, voice, text, /ask
smriti/
  config.py                 Settings (pydantic-settings, all env vars)
  models.py                 API schemas and memory models
  clients/llm.py            Groq: Whisper STT, Llama structurer, answerer, summarizer
  clients/memory.py         Supermemory cloud/local client
  services/
    demo_data.py            Asha Devi demo memories + eval questions
    retrieval_service.py    Semantic search with scoring guardrails
    memory_quality.py       Duplicate detection before save
    document_ingestion.py   PDF/photo → text extraction
frontend/
  index.html                Browser entry point
  src/app.js                React UI (vanilla, no build step)
  src/voice.js              Microphone recording
  src/styles.css            Mobile-first styling
  src/api.js                API client functions
docs/hackathon/             Build plan, changes log, testing guide
```

---

## Safety

Smriti recalls facts you have recorded. It does not diagnose conditions, recommend medication doses, interpret lab values, or make medical urgency decisions. Always consult a doctor for medical advice. The safety notice is displayed on every screen.

---

## Built with

- [FastAPI](https://fastapi.tiangolo.com) — backend
- [Groq](https://groq.com) — Whisper STT + Llama 3.3 70B
- [Supermemory](https://supermemory.ai) — semantic memory layer
- [python-telegram-bot](https://python-telegram-bot.org) — Telegram integration
- React (vanilla, no bundler) — frontend
- [Render](https://render.com) — deployment

---

*Built for the [BestPossible.AI Hackathon](https://bestpossible.ai/hackathon) — Aug 2026*
