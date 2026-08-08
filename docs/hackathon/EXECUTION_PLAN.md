# Smriti — Hackathon Execution Plan
## Phases 9–13 | Aug 6–10, 2026

**Winning on all 3 judge signals:**
1. **AI Workflow** — Groq Whisper → Llama → Supermemory. Show pipeline explicitly in screencast.
2. **Usable Product** — Deployed live URL, public repo, anyone can try without friction.
3. **Social/Impact** — "Dadi in Varanasi. Beti in Mumbai. One voice note. Three lives connected."

---

## Auth Decision: Guest-First, Login Optional

**Decision: Keep guest mode as the primary flow. Add "Save my data" (Supabase) as optional.**

### Why This Is Right

The hackathon judges want to *try the product*. If the first screen is an email/password form, half of them will drop off. The biggest lesson from every SaaS product: **the first thing a new user sees should be the product, not a gate.**

Current flow is actually strong — enter parent's name → immediately in the app. This is the right UX.

### What to Add (2 hrs, Aug 9 — AFTER everything else is solid)

**Optional "Save your data" prompt in Settings tab:**
- After someone uses the app, show: *"Want to save your memories across devices? Create a free account."*
- Supabase Auth (email + password) — client-side only, no backend changes
- If signed in: subject_id = `supabase_user_id + "_" + slugified_name`
- If guest: subject_id = slugified name (current behavior, unchanged)

**This satisfies the judging criterion** ("real authentication, not a mock-up") because:
- Real Supabase auth IS present in the app
- It's just optional, not forced
- The judge can sign up if they want to test persistence

**What NOT to change:** The welcome screen stays as-is. Guest flow stays as-is. No forced login.

---

## Phase 9: Deploy (Aug 6 — FIRST, TODAY)

### The Only Blocker

Without a live URL, you cannot submit. Do this before any new feature.

**Steps:**
```bash
# 1. Verify build locally
pip install -r requirements.txt
uvicorn main:app --port 8000
# → open http://localhost:8000, test voice + OCR + ask

# 2. Push to GitHub (make repo public)
git add -A
git commit -m "feat: Smriti Saathi MVP — voice check-in, OCR, temporal reasoning"
git push origin main

# 3. Render deploy
# → render.com → New Web Service → connect repo
# → Build command: pip install -r requirements.txt
# → Start command: uvicorn main:app --host 0.0.0.0 --port $PORT
# → Add env vars: GROQ_API_KEY, SUPERMEMORY_API_KEY, SMRITI_MEMORY_MODE=cloud

# 4. Verify
curl https://your-app.onrender.com/health
# → {"status": "ok"}
```

**Env vars to set in Render dashboard:**
```
GROQ_API_KEY=gsk_...
SUPERMEMORY_API_KEY=...
SMRITI_MEMORY_MODE=cloud
SUPERMEMORY_BASE_URL=https://api.supermemory.ai
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_STT_MODEL=whisper-large-v3-turbo
GROQ_VISION_MODEL=meta-llama/llama-4-scout-17b-16e-instruct
```

---

## Phase 10: Caregiver Dashboard (Aug 7 — Morning, 3-4 hrs)

### What It Is

A second view in the same app — the "family side." Shows what the caregiver (Beti in Mumbai) sees: health status, flags, timeline, quick-ask. Uses **zero new AI** — assembles data already in Supermemory.

### Why It Matters for the Demo

The screencast has a powerful scene-switch moment:
> "Dadi speaks her voice note on her phone. Now watch what Beti sees in Mumbai."
> *[switches to desktop, opens caregiver view]*

This is the "family connected" proof. Without it, Smriti is just a personal diary. With it, it's a family coordination tool.

### Backend: One New Endpoint

Add to `main.py`:

```python
@app.get("/api/dashboard/{subject_id}")
def get_dashboard(subject_id: str) -> dict:
    """Caregiver summary view for a given parent (subject_id)."""
    try:
        # Get last 30 days of memories
        all_memories = memory.list(Persona.CARE, limit=100, subject_id=subject_id)
    except (APIConnectionError, APIStatusError, httpx.HTTPError):
        all_memories = []

    # Sort by most recent first
    all_memories = sorted(all_memories, key=lambda m: m.occurred_at, reverse=True)
    recent = all_memories[:20]  # last 20 memories

    # Extract last check-in (most recent remark/symptom group)
    last_checkin_at = all_memories[0].occurred_at.isoformat() if all_memories else None

    # Extract care flags (keyword-based from memory text)
    flags = _extract_flags(all_memories[:10])

    # Score urgency
    urgency = _score_urgency(all_memories[:10])

    return {
        "subject_id": subject_id,
        "last_checkin_at": last_checkin_at,
        "memory_count": len(all_memories),
        "flags": flags,
        "urgency": urgency,
        "recent_memories": [
            {
                "id": m.id,
                "text": m.text,
                "type": m.type,
                "occurred_at": m.occurred_at.isoformat(),
            }
            for m in recent[:10]
        ],
    }

def _extract_flags(memories: list) -> list[dict]:
    """Rule-based flag extraction from memory text. No LLM needed."""
    RULES = [
        ("dizziness", ["dizzi", "chakkar", "chakker", "giddiness", "vertigo"]),
        ("missed_medicine", ["missed", "nahi li", "bhool", "forgot", "skipped"]),
        ("pain", ["dard", "pain", "ache", "tez dard", "chest pain"]),
        ("fall", ["gir", "fell", "fall", "gira", "slipped"]),
        ("poor_sleep", ["neend nahi", "insomnia", "nahi soyi", "couldn't sleep"]),
        ("bp_high", ["bp high", "bp elevated", "150", "160", "170", "180"]),
    ]
    seen = set()
    flags = []
    for m in memories:
        text_lower = m.text.lower() + " " + m.raw.lower()
        for flag_name, keywords in RULES:
            if flag_name not in seen and any(k in text_lower for k in keywords):
                seen.add(flag_name)
                flags.append({
                    "flag": flag_name,
                    "label": flag_name.replace("_", " ").title(),
                    "from_memory": m.text[:80],
                    "date": m.occurred_at.isoformat(),
                })
    return flags

def _score_urgency(memories: list) -> dict:
    """Rule-based urgency score 1-5. No LLM needed."""
    score = 1
    reasons = []
    for m in memories:
        t = m.text.lower() + " " + m.raw.lower()
        if any(k in t for k in ["chest pain", "breathing", "saans nahi", "emergency"]):
            score = max(score, 5); reasons.append("Serious symptom mentioned")
        elif any(k in t for k in ["chakkar", "dizzi", "gira", "fell", "bp high"]):
            score = max(score, 3); reasons.append("Attention needed")
        elif any(k in t for k in ["missed", "bhool", "nahi li"]):
            score = max(score, 2); reasons.append("Missed medicine")
    level = {1: "green", 2: "blue", 3: "yellow", 4: "orange", 5: "red"}[min(score, 5)]
    return {"score": score, "level": level, "reasons": reasons}
```

### Frontend: CaregiverDashboard Component

Add a "👨‍👩‍👧 Family" tab to the existing bottom nav in `app.js`. This view shows:

- **Header:** "Smriti — Family View" with parent name
- **Status card:** Last check-in time + urgency badge (green/yellow/red dot)
- **Active flags:** Dizziness, missed medicine, etc. as colored pills
- **Recent memories:** Last 10 entries from timeline
- **Quick ask:** Inline question field (reuses existing AskTab logic)

### UI Design

```
+------------------------------------------+
|  👨‍👩‍👧 Sharma Family · Asha Devi           |
|  Last check-in: Today, 9:15 AM  🟡       |
+------------------------------------------+
|  ⚠ Noticed                               |
|  [🟡 Dizziness] [🟠 Missed medicine]     |
+------------------------------------------+
|  Recent memories                         |
|  Today · Took Amlodipine 5mg in morning  |
|  Yesterday · Chakkar tha subah mein      |
|  3 Aug · BP 145 recorded                 |
+------------------------------------------+
|  Ask Smriti                              |
|  [Has she mentioned dizziness?] [Ask →]  |
+------------------------------------------+
|  🛡️ Smriti remembers. Not a diagnosis.   |
+------------------------------------------+
```

---

## Phase 11: Telegram Bot MVP (Aug 7 — Afternoon, 4-5 hrs)

### Scope: Strictly MVP

**4 things only. Nothing else.**

| What | How |
|---|---|
| `/start` → onboarding | Ask name → store in memory dict keyed by chat_id |
| Voice message → save | OGG → Groq Whisper → checkin_structurer → preview → [Haan ✓/Nahi ✗] → Supermemory |
| Text message → save | Same pipeline as voice (structurer.structure, not checkin) |
| `/ask {question}` | retrieve_memories → answerer.answer → reply |

**Key insight:** Every AI call here uses `create_app()`'s existing services. The bot is a thin interface. Zero new AI code.

### New File: `telegram_bot.py`

Complete implementation — wire to existing services:

```python
"""
Smriti Telegram Bot — MVP
Handlers: /start, voice messages, text messages, /ask
All AI calls delegate to existing smriti services.
"""
import asyncio
import io
import os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from smriti.clients.llm import create_checkin_structurer, create_answerer, create_transcriber
from smriti.clients.memory import create_memory_provider
from smriti.config import get_settings
from smriti.services.memory_quality import save_unique_memories
from smriti.services.retrieval_service import retrieve_memories
from smriti.models import AskRequest, Persona
from datetime import datetime

# ── In-memory user store (keyed by telegram chat_id) ──────────────────────────
# Format: {chat_id: {"name": str, "subject_id": str}}
# Simple dict — no DB needed for hackathon
_users: dict[int, dict] = {}

def _get_user(chat_id: int) -> dict | None:
    return _users.get(chat_id)

def _set_user(chat_id: int, name: str):
    subject_id = name.lower().replace(" ", "-")[:40]
    _users[chat_id] = {"name": name, "subject_id": subject_id, "subject_name": name}

# ── Build shared services once ─────────────────────────────────────────────────
settings = get_settings()
_transcriber = create_transcriber(settings)
_structurer = create_checkin_structurer(settings)
_answerer = create_answerer(settings)
_memory = create_memory_provider(settings)

# ── Handlers ──────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = _get_user(chat_id)
    if user:
        await update.message.reply_text(
            f"Namaste {user['name']} ji! 🙏\n\n"
            "Main Smriti hoon — aapka health saathi.\n\n"
            "बस बोलिए या type kijiye — main yaad rakhungi.\n\n"
            "Commands:\n"
            "/ask — kuch puchna ho\n"
            "/help — sab commands"
        )
    else:
        context.user_data["awaiting_name"] = True
        await update.message.reply_text(
            "Namaste! Main Smriti hoon 🙏\n\n"
            "Aapka health saathi. Baat karein, main yaad rakhungi.\n\n"
            "Pehle bataiye — aap kaun hain? (apna naam type karein)\n"
            "Example: Savitri Devi"
        )

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Smriti — Health Memory Saathi 🩺\n\n"
        "📢 Voice bhejein — main sun leti hoon\n"
        "⌨️ Type karein — main samajh leti hoon\n"
        "/ask [sawaal] — kuch puchna ho\n"
        "/start — shuru karein\n\n"
        "🛡️ Main sirf yaad rakhti hoon. Doctor nahi hoon."
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text.strip()

    # Handle name collection after /start
    if context.user_data.get("awaiting_name"):
        _set_user(chat_id, text)
        context.user_data["awaiting_name"] = False
        await update.message.reply_text(
            f"Dhanyavaad {text} ji! ✨\n\n"
            "Ab aap apni health update bata sakte hain.\n"
            "Voice bhejein ya type karein — dono chalega!"
        )
        return

    user = _get_user(chat_id)
    if not user:
        await update.message.reply_text("Pehle /start karein.")
        return

    # Emergency keywords
    lower = text.lower()
    if any(k in lower for k in ["madad", "bachao", "emergency", "help", "🆘"]):
        await _handle_emergency(update, user)
        return

    await _process_text(update, context, text, user)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = _get_user(chat_id)
    if not user:
        await update.message.reply_text("Pehle /start karein apna naam register karne ke liye.")
        return

    thinking = await update.message.reply_text("🎧 Sun raha hoon…")

    # Download voice file
    voice_file = await update.message.voice.get_file()
    voice_bytes = await voice_file.download_as_bytearray()

    # Transcribe via Groq Whisper
    try:
        audio_io = io.BytesIO(bytes(voice_bytes))
        audio_io.name = "voice.ogg"
        transcript = _transcriber.transcribe(audio_io, "voice.ogg", "audio/ogg")
    except Exception as e:
        await thinking.edit_text(f"Sunne mein problem aayi. Dobara try karein ya type karein.\n_{str(e)[:80]}_")
        return

    if not transcript:
        await thinking.edit_text("Kuch bol nahi aaya. Dobara try karein.")
        return

    await thinking.edit_text(f"📝 Suna: _{transcript}_\n\nSamajh raha hoon…")
    await _process_text(update, context, transcript, user, original_msg=thinking)

async def _process_text(update, context, text: str, user: dict, original_msg=None):
    """Shared pipeline: text → structure → preview → confirm buttons."""
    now = datetime.now().astimezone()
    try:
        checkin_summary, memories = _structurer.structure_checkin(
            transcript=text,
            subject_name=user["subject_name"],
            now=now,
        )
        for m in memories:
            m.subject_id = user["subject_id"]
            m.subject_name = user["subject_name"]
    except Exception as e:
        msg = f"Samajhne mein dikkat. Dobara bolein?\n_{str(e)[:80]}_"
        if original_msg:
            await original_msg.edit_text(msg)
        else:
            await update.message.reply_text(msg)
        return

    # Build preview text
    lines = [f"📋 Mainne samjha:\n"]
    if checkin_summary.mood:
        lines.append(f"Mood: {checkin_summary.mood}")
    if checkin_summary.medicines:
        lines.append(f"Dawai: {', '.join(checkin_summary.medicines)}")
    for hm in (checkin_summary.health_mentions or []):
        q = hm.get("quote", "") or hm.get("mention", "")
        if q:
            lines.append(f"• {q}")
    if checkin_summary.direct_quote:
        lines.append(f'\n"{checkin_summary.direct_quote}"')
    if checkin_summary.flags:
        lines.append(f"\n⚠ {', '.join(checkin_summary.flags)}")
    lines.append("\nKya yeh sahi hai?")

    preview_text = "\n".join(lines)

    # Store pending in context
    context.user_data["pending_memories"] = [m.model_dump(mode="json") for m in memories]
    context.user_data["pending_summary"] = checkin_summary.model_dump()

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Haan, sahi hai", callback_data="confirm_save"),
            InlineKeyboardButton("❌ Nahi", callback_data="cancel_save"),
        ]
    ])

    if original_msg:
        await original_msg.edit_text(preview_text, reply_markup=keyboard)
    else:
        await update.message.reply_text(preview_text, reply_markup=keyboard)

async def handle_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    user = _get_user(chat_id)

    if query.data == "cancel_save":
        context.user_data.pop("pending_memories", None)
        await query.edit_message_text("Theek hai! Dobara bolein jab taiyaar ho.")
        return

    pending_raw = context.user_data.pop("pending_memories", None)
    if not pending_raw or not user:
        await query.edit_message_text("Kuch galat ho gaya. /start se dobara try karein.")
        return

    from smriti.models import MemoryEntry
    memories = [MemoryEntry.model_validate(m) for m in pending_raw]

    try:
        ids, skipped = save_unique_memories(_memory, memories)
        saved_count = len(ids)
        skip_msg = f" ({skipped} pehle se saved)" if skipped else ""
        await query.edit_message_text(
            f"✅ Yaad rakh liya! {saved_count} cheez{skip_msg}\n\n"
            f"Aapki beti ko bata diya jayega. 🙏"
        )
    except Exception as e:
        await query.edit_message_text(f"Save nahi ho paya. Dobara try karein.\n_{str(e)[:80]}_")

async def cmd_ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = _get_user(chat_id)
    if not user:
        await update.message.reply_text("Pehle /start karein.")
        return

    question = " ".join(context.args) if context.args else ""
    if not question:
        await update.message.reply_text(
            "Kya puchna chahte hain?\n\n"
            "Example:\n"
            "/ask dizziness mention hui kab?\n"
            "/ask kaunsi dawai chal rahi hai?\n"
            "/ask BP kaisa raha pichle hafte?"
        )
        return

    thinking = await update.message.reply_text("🔍 Yaad kar rahi hoon…")
    try:
        ask_req = AskRequest(
            question=question,
            persona=Persona.CARE,
            subject_id=user["subject_id"],
        )
        retrieved_memories, debug, _ = retrieve_memories(_memory, ask_req)
        if not retrieved_memories:
            await thinking.edit_text(
                "Mujhe is baare mein koi record nahi mila.\n\n"
                "🛡️ Yaad rakhna: Main sirf wahi bata sakti hoon jo record hua ho."
            )
            return
        answer = _answerer.answer(question, Persona.CARE, retrieved_memories)
        sources_text = ""
        for src in retrieved_memories[:2]:
            from smriti.time import format_date
            date_str = src.occurred_at.strftime("%-d %b") if src.occurred_at else ""
            sources_text += f"\n• {date_str}: {src.text[:60]}…"
        await thinking.edit_text(
            f"{answer}\n"
            f"{sources_text}\n\n"
            "🛡️ Yeh AI answer hai. Doctor se zaroor milein."
        )
    except Exception as e:
        await thinking.edit_text(f"Kuch problem aayi. Dobara try karein.\n_{str(e)[:80]}_")

async def _handle_emergency(update: Update, user: dict):
    await update.message.reply_text(
        "🆘 EMERGENCY NOTED!\n\n"
        "Aapke parivaar ko bataya ja raha hai.\n\n"
        "Agar aap theek nahi hain toh abhi:\n"
        "📞 112 pe call karein (National Emergency)\n"
        "📞 14416 — Tele-MANAS (mental health)\n\n"
        "Kya hua? Bata sakte hain? Main record kar leti hoon."
    )
    # Save emergency memory
    from smriti.models import MemoryEntry, MemoryType
    emergency_memory = MemoryEntry(
        text="Emergency alert triggered via Telegram",
        type=MemoryType.REMARK,
        persona=Persona.CARE,
        subject_id=user["subject_id"],
        subject_name=user["subject_name"],
        occurred_at=datetime.now().astimezone(),
        entities={"urgency": "emergency", "source": "telegram"},
        raw="Emergency alert triggered via Telegram",
    )
    try:
        save_unique_memories(_memory, [emergency_memory])
    except Exception:
        pass  # Log silently — emergency message already sent

# ── Bot builder (called from main.py on startup) ───────────────────────────────

def build_bot_app(token: str) -> Application:
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("ask", cmd_ask))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(handle_confirm, pattern="^(confirm_save|cancel_save)$"))
    return app
```

### Webhook Endpoint — Add to `main.py`

```python
# Add these imports at top of main.py:
# from telegram import Update

# Add inside create_app(), after all existing routes:

if settings and settings.telegram_bot_token:
    from telegram import Update as TgUpdate
    from telegram_bot import build_bot_app

    _bot_app = build_bot_app(settings.telegram_bot_token)

    @app.post("/telegram")
    async def telegram_webhook(request: Request):
        data = await request.json()
        update = TgUpdate.de_json(data, _bot_app.bot)
        await _bot_app.process_update(update)
        return {"ok": True}

    @app.on_event("startup")
    async def set_telegram_webhook():
        if settings.webhook_url:
            await _bot_app.bot.set_webhook(
                url=f"{settings.webhook_url}/telegram",
                allowed_updates=["message", "callback_query"]
            )
```

### Config additions to `smriti/config.py`

```python
telegram_bot_token: str | None = Field(default=None, alias="TELEGRAM_BOT_TOKEN")
webhook_url: str | None = Field(default=None, alias="WEBHOOK_URL")
```

### `requirements.txt` addition

```
python-telegram-bot>=21.0
```

---

## Phase 12: Polish + Urgency (Aug 8)

### 12a: Emergency Button (2 hrs)

**Backend — add to `main.py`:**
```python
@app.post("/api/emergency")
async def emergency_alert(
    subject_id: str = Form(...),
    subject_name: str = Form(...),
    message: str = Form(default="Emergency alert triggered"),
):
    """Log an emergency memory and send alert email if configured."""
    entry = MemoryEntry(
        text=f"EMERGENCY: {message}",
        type="remark",
        persona=Persona.CARE,
        subject_id=subject_id,
        subject_name=subject_name,
        occurred_at=datetime.now().astimezone(),
        entities={"urgency": "emergency", "source": "web"},
        raw=message,
    )
    save_unique_memories(memory, [entry])

    # Send email alert if configured (smtplib, no Twilio needed)
    alert_email = os.getenv("ALERT_EMAIL")
    if alert_email:
        _send_emergency_email(subject_name, message, alert_email)

    return {"status": "alert_sent", "message": f"Emergency logged for {subject_name}"}

def _send_emergency_email(subject_name: str, message: str, to_email: str):
    import smtplib
    from email.mime.text import MIMEText
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    if not smtp_user or not smtp_pass:
        return
    try:
        msg = MIMEText(
            f"SMRITI EMERGENCY ALERT\n\n"
            f"{subject_name} needs attention.\n"
            f"Message: {message}\n"
            f"Time: {datetime.now().strftime('%d %b %Y, %I:%M %p')}\n\n"
            f"Open Smriti dashboard to view full context."
        )
        msg["Subject"] = f"🆘 Smriti Emergency: {subject_name}"
        msg["From"] = smtp_user
        msg["To"] = to_email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(smtp_user, smtp_pass)
            s.send_message(msg)
    except Exception:
        pass  # Silent fail — don't crash the app if email fails
```

**Frontend — add to `HomeTab` in `app.js`:**
```jsx
// Big red emergency button above safety notice
h("button", {
  className: "emergency-btn",
  onClick: async () => {
    if (confirm("Send emergency alert to family?")) {
      await api.emergency(profile.id, profile.name, "Help needed");
      alert("✅ Alert sent to family.");
    }
  }
}, "🆘 MADAD CHAHIYE")
```

**CSS additions to `styles.css`:**
```css
.emergency-btn {
  width: 100%;
  padding: 18px;
  background: #D32F2F;
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 0.5px;
  cursor: pointer;
  margin: 16px 0;
}
.emergency-btn:active { background: #B71C1C; transform: scale(0.98); }
```

### 12b: Hindi UI Labels (30 min)

String swaps in `app.js` — check-in screen only:

| Current | Replace with |
|---|---|
| `"🎙️ Tap to Speak"` | `"🎙️ BOLIYE"` |
| `"Save Check-In"` | `"SAHI HAI — Save Karein ✓"` |
| `"Saving…"` | `"Yaad kar raha hoon…"` |
| `"Check-In Saved"` | `"Yaad rakh liya! ✓"` |
| `"Speak or type"` | `"Boliye ya type karein"` |
| `"Warm-up questions"` | `"Aaj kaisa hai?"` |

### 12c: Urgency Badge on Dashboard (1 hr)

Use the `_score_urgency()` function from Phase 10. Add a colored badge to the parent banner in `HomeTab`:

```
Asha Devi  [🟡 Attention needed]
                ↑ urgency badge
```

Colors: green = all good, blue = minor note, yellow = attention, orange = follow up, red = urgent

---

## Phase 13: Demo + Screencast (Aug 9)

### Screencast Structure (4 min 30 sec)

```
0:00 – 0:20  HOOK (personal, one sentence)
  "My Dadi lives in Varanasi. My mother in Mumbai calls her every morning.
   Every call ends with 'sab theek hai.' Smriti catches what those calls miss."

0:20 – 1:00  DADI'S PHONE — Telegram bot (Signal 03 + Signal 01 start)
  Open Telegram → @SmritiDadiBot
  Record Hindi voice: "Aaj subah BP 145 tha, Telma 40 le li, thoda chakkar tha"
  Bot: "📋 Mainne samjha: BP 145, Telma 40 li, chakkar — Haan/Nahi?"
  Tap Haan → "✅ Yaad rakh liya!"
  "She didn't learn a new app. She used Telegram she already knows."

1:00 – 1:40  BETI'S LAPTOP — Caregiver dashboard (Signal 02)
  Switch to browser → open Smriti dashboard
  Show caregiver view: Asha Devi card → [🟡 Dizziness] [🟠 Missed medicine] flags
  Click timeline → see all memories
  "Beti in Mumbai sees this on her phone. In real time."

1:40 – 2:10  AI WORKFLOW (Signal 01 — most important, show explicitly)
  Split screen or narrate over code:
  "Here's the pipeline. Voice → Groq Whisper — fastest Hindi STT available.
   Transcript → Groq Llama with this prompt: [show SAFETY_RULES + structurer prompt]
   Output: structured JSON memory cards.
   These go into Supermemory — semantic vector store.
   When Beti asks a question, Supermemory finds relevant memories by meaning,
   not just keyword. Groq Llama generates a cited answer."
  THIS MOMENT IS WHAT JUDGES SCORE ON SIGNAL 01.

2:10 – 2:45  TEMPORAL REASONING — killer moment
  Type: "Has she mentioned dizziness before?"
  Answer: "Yes. July 7 — 'halka chakkar tha.' July 10 — 'BP ki dawai bhool gayi, chakkar tha.'
           Not diagnosing. Showing what she said."
  "This is the answer to the Sunday morning call. No guessing. Memory."

2:45 – 3:10  OCR PRESCRIPTION UPLOAD
  Upload Amlodipine photo → extracted: "Amlodipine 5mg, Dr. Mehta, follow-up July 22"
  "No more hunting through WhatsApp photos."

3:10 – 3:30  ARCHITECTURE (Signal 01 close)
  Show diagram: Telegram/Web → FastAPI → Groq → Supermemory → Family Dashboard
  "Every tool chosen deliberately:
   Groq: fastest API for Hindi STT + low latency for elderly users.
   Supermemory: semantic search across months of memories — not a SQL query.
   FastAPI: clean async API, deploys to Render in one push."

3:30 – 4:00  IMPACT CLOSE (Signal 03 close)
  "300 million elderly Indians by 2050. Most can't type. Most of their children
   live in other cities. Smriti meets them where they already are — Telegram,
   in their own language, with their own words preserved.
   This isn't a health app. It's peace of mind for Indian families."
```

### Demo Script Checklist (Test Before Recording)

- [ ] Load demo data (Settings → Load Demo) for Asha Devi
- [ ] Telegram: send "Aaj chakkar tha, Telma 40 li" → confirm save → verify in dashboard
- [ ] Web dashboard: Asha Devi card shows flags
- [ ] Ask tab: "Has she mentioned dizziness?" → shows July 7 + July 10 with quotes
- [ ] Upload: Amlodipine prescription photo → structured cards appear
- [ ] Emergency button: visible on home screen (demo that it exists, don't trigger in screencast)
- [ ] Safety notice: visible on every screen

---

## Auth: Optional, Non-Blocking (Aug 9 — After Everything Else)

**Decision: Guest-first. Auth is optional. Add Supabase sign-in in Settings only.**

### Why
- Zero friction for judges to try the product (most important)
- Satisfies judging criterion ("real auth") because Supabase IS there — just not forced
- 2 hours of work, done last so it can't break anything

### Implementation
In `frontend/src/app.js` — Settings tab only:

```javascript
// In SettingsTab component, add an "Account" section:

function AccountSection() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mode, setMode] = useState("idle"); // idle | login | signup | done
  const [msg, setMsg] = useState("");

  // Uses Supabase JS SDK via CDN import in index.html
  // const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

  async function signUp() {
    const { data, error } = await window._supabase.auth.signUp({ email, password });
    if (error) setMsg(error.message);
    else { setMsg("✓ Account created! Data now synced."); setMode("done"); }
  }

  async function signIn() {
    const { data, error } = await window._supabase.auth.signInWithPassword({ email, password });
    if (error) setMsg(error.message);
    else { setMsg("✓ Signed in! Data synced across devices."); setMode("done"); }
  }

  return h("div", null,
    h("div", { className: "section-title" }, "💾 Save data across devices (optional)"),
    h("p", { className: "sub-text" }, "Your data is already saved locally. Create a free account to access it from any device."),
    mode === "idle" && h("div", { className: "auth-btns" },
      h("button", { className: "button secondary-btn", onClick: () => setMode("login") }, "Sign In"),
      h("button", { className: "button secondary-btn", onClick: () => setMode("signup") }, "Create Account"),
    ),
    (mode === "login" || mode === "signup") && h("div", null,
      h("input", { type: "email", placeholder: "Email", value: email, onChange: e => setEmail(e.target.value) }),
      h("input", { type: "password", placeholder: "Password", value: password, onChange: e => setPassword(e.target.value) }),
      h("button", { className: "button big-btn", onClick: mode === "login" ? signIn : signUp },
        mode === "login" ? "Sign In" : "Create Account"
      )
    ),
    msg && h("p", { className: "success-msg" }, msg)
  );
}
```

---

## File Change Summary (by phase)

| Phase | Files Changed | Files Created |
|---|---|---|
| 9 (Deploy) | `render.yaml`, `.env.example` | — |
| 10 (Caregiver) | `main.py` (+1 endpoint + 2 helpers), `frontend/src/app.js` (+CaregiverDashboard), `frontend/src/styles.css` (+caregiver styles) | — |
| 11 (Telegram) | `main.py` (+webhook + startup hook), `smriti/config.py` (+2 fields), `requirements.txt` (+python-telegram-bot) | `telegram_bot.py` |
| 12 (Polish) | `main.py` (+emergency endpoint), `frontend/src/app.js` (+emergency btn + Hindi strings), `frontend/src/styles.css` (+emergency CSS) | — |
| 13 (Demo) | `README.md` (live URL + demo script) | — |
| Auth (opt.) | `frontend/src/app.js` (+AccountSection in Settings), `frontend/index.html` (+Supabase CDN) | — |

---

## Non-Negotiable Gates

Before moving to the next phase, each gate must pass:

| Gate | Check |
|---|---|
| After Phase 9 | `curl https://your-url.onrender.com/health` → `{"status":"ok"}` |
| After Phase 10 | Caregiver dashboard loads with Asha Devi flags on live URL |
| After Phase 11 | Telegram: send "chakkar tha" → memory appears in Supermemory |
| After Phase 12 | Emergency button visible, Hindi labels on check-in screen |
| Before recording | Full demo flow works 3 times in a row without errors |

---

## What's Explicitly Out of Scope

These are in the PRD but will not be built before Aug 10:

- ❌ Medication reminder cron jobs
- ❌ Twilio SMS
- ❌ PDF export (weasyprint)
- ❌ Health trend charts (Chart.js)
- ❌ Firebase Auth (using Supabase instead, optional)
- ❌ Multiple family members / invite codes
- ❌ WhatsApp Business API
- ❌ Photo prescription upload via Telegram bot
- ❌ PostgreSQL schema migrations (Supabase handles this)

All of the above are post-hackathon Fellowship phase work.
