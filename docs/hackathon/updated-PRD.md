# Smriti - Dadi Ka Health Saathi
## Product Requirements Document (PRD)
### Version 1.0 | BestPossible.AI Hackathon | Aug 2026

---

## 1. Product Overview

**Product Name:** Smriti (smriti) - Dadi Ka Health Saathi  
**Tagline:** *"Boli. Yaad Rakh. Parivaar Judaa."* (Speak. Remember. Family Connected.)  
**Category:** Health & Wellbeing / Elderly Care  
**Platform:** Web App + Telegram Bot  
**Target Market:** Indian families with elderly members (60+ years), especially those living in different cities.

### 1.1 Problem Statement

India will have **300 million elderly citizens by 2050**. The current elderly care landscape is:
- **Fragmented:** Every app does one thing (medication, fall detection, telemedicine) but nothing connects them.
- **Typing-dependent:** Most elderly Indians cannot or will not type health updates into apps.
- **Family-disconnected:** Children living in other cities have no visibility into their parents' daily health.
- **Doctor-unfriendly:** Scattered notes, WhatsApp forwards, and memory-dependent recall during doctor visits.

### 1.2 Solution

Smriti is a **voice-first, family-connected health memory app** built for Indian elderly. A grandmother speaks her health update in Hindi. AI structures it. Her daughter in Mumbai sees it instantly. The doctor gets a structured summary. One voice note. Three lives connected.

### 1.3 Why This Wins the Hackathon

| Judging Criteria | How Smriti Delivers |
|---|---|
| **Clear purpose** | Solves a real, quantified problem (300M elderly, fragmented care) |
| **Built with AI** | STT (Hindi), vision (prescriptions), structuring, retrieval, summarization, urgency scoring |
| **Usable UI** | Mobile-first, large fonts (18px+), high contrast, minimal taps |
| **Responsive** | Works on phone (Dadi) and laptop (Beti) |
| **User login** | Real Firebase Auth with family roles (Elder + Caregiver) |
| **Real backend** | FastAPI + Supermemory + PostgreSQL. Real data persistence. |
| **Deployed & live** | Render deployment + Telegram Bot live |
| **Open source** | Public GitHub repo with clean commit history |
| **Nice extras** | Telegram Bot, WhatsApp share, email summaries, PDF export, push notifications |

---

## 2. Target Users & Personas

### 2.1 Primary: The Elder (Dadi/Nana)
- **Age:** 60-85 years
- **Location:** Tier-2/3 city or village in India
- **Tech comfort:** Uses WhatsApp, watches YouTube, cannot type comfortably
- **Language:** Hindi, Hinglish, or regional language
- **Pain:** Forgets medicine, forgets doctor's advice, children worry
- **Goal:** Speak health updates easily. Feel cared for, not surveilled.

### 2.2 Secondary: The Caregiver (Beti/Beta)
- **Age:** 30-50 years
- **Location:** Metro city (Mumbai, Delhi, Bangalore)
- **Tech comfort:** High
- **Pain:** Daily anxiety call to parents. No visibility into health trends. Scattered WhatsApp notes.
- **Goal:** See parent's health at a glance. Get alerts when something is wrong. Share structured history with doctors.

### 2.3 Tertiary: The Doctor
- **Age:** 35-60 years
- **Pain:** Patients forget symptoms, medication history, and past vitals. Wastes 10+ minutes per visit.
- **Goal:** Receive a structured, chronological health summary before the appointment.

---

## 3. Core Features

### 3.1 Feature Matrix

| Feature | Priority | Platform | Status |
|---|---|---|---|
| Voice health memory (Hindi + English) | P0 | Web + Telegram | Exists |
| Preview before save | P0 | Web | Exists |
| Person-specific memory isolation | P0 | Web | Exists |
| Ask questions from memory | P0 | Web | Exists |
| Visit summary generation | P0 | Web | Exists |
| Report/prescription upload & extraction | P0 | Web | Exists |
| **Telegram Bot integration** | **P0** | **Telegram** | **NEW** |
| **Real authentication + family roles** | **P0** | **Web** | **NEW** |
| **Caregiver dashboard** | **P0** | **Web** | **NEW** |
| **Hindi-first voice input** | **P0** | **Web + Telegram** | **NEW** |
| **Medication reminders** | **P1** | Web + Telegram | **NEW** |
| **Health trend charts (BP, Sugar)** | **P1** | Web | **NEW** |
| **Emergency / "Need Help" button** | **P1** | Web + Telegram | **NEW** |
| **Urgency scoring (AI)** | **P1** | Backend | **NEW** |
| **PDF visit summary export** | **P1** | Web | **NEW** |
| **WhatsApp share for summaries** | **P2** | Web | **NEW** |
| **Tele-MANAS integration** | **P2** | Web | **NEW** |
| Fall detection (phone accelerometer) | P3 | Mobile | Future |
| Daily loneliness check-in | P3 | Telegram | Future |

---

## 4. Telegram Bot Specification

### 4.1 Bot Name & Handle
- **Name:** Smriti Health Saathi
- **Handle:** `@SmritiHealthBot` (or `@SmritiDadiBot`)
- **Description:** *"Boli. Yaad Rakh. Parivaar Judaa. Speak your health update in Hindi or English, and Smriti remembers it for your family."*

### 4.2 User Onboarding Flow

```
User starts bot -> /start
  |
  v
Bot: "Namaste! Main Smriti hoon - aapka health saathi. 
      Kripya apna phone number share karein."
  |
  v
User shares phone number (Telegram contact button)
  |
  v
Backend: Check if phone exists in Smriti DB
  |-- YES -> Link Telegram ID to existing account
  |         Bot: "Aapka account jod diya gaya hai! 
  |               Ab aap apni health update bata sakte hain."
  |
  +-- NO  -> Create new elder account
            Bot: "Aapka naya account ban gaya hai! 
                  Kripya apna naam batayein."
            User: "Savitri Devi"
            Bot: "Dhanyavaad Savitri ji! Ab aap apni health 
                  update bata sakte hain."
```

### 4.3 Core Bot Commands

| Command | Description | Flow |
|---|---|---|
| `/start` | Begin onboarding | See 4.2 |
| `/record` | Start voice health note | Prompts user to send voice message |
| `/ask` | Ask a question about health | "Aap kya puchna chahte hain?" -> User types question -> AI answers from memory |
| `/summary` | Generate visit summary | Returns last 30 days structured summary |
| `/reminders` | View/set medication reminders | Shows active reminders. Inline keyboard to add new. |
| `/emergency` | Trigger emergency alert | Sends SMS/WhatsApp to caregiver + logs emergency |
| `/help` | Show all commands | Hindi + English bilingual help |

### 4.4 Voice Message Flow (Primary Use Case)

```
User sends voice message (Hindi/English)
  |
  v
Bot: "Sun raha hoon..." (transcribing)
  |
  v
Groq Whisper STT (auto-detect language)
  |
  v
Groq AI structures into memory cards
  |
  v
Bot: "Maine samjha:
      - BP: 145/95
      - Dawa: Dabur Chyawanprash liya
      - Date: 6 Aug 2026

      Kya yeh sahi hai? [Haan] [Nahi]"
  |
  v
User taps [Haan]
  |
  v
Save to Supermemory with:
  - persona: elder
  - subject_id: savitri_devi
  - subject_name: Savriti Devi
  - source: telegram
  - telegram_chat_id: 123456789
  |
  v
Bot: "Yaad rakh liya! Aapki beti ko bata diya gaya."
  |
  v
[Background] Caregiver dashboard updates in real-time
[Background] Urgency scorer runs: BP 145/95 -> Score 3 (Yellow)
[Background] If score >= 4 -> Send alert to caregiver
```

### 4.5 Text Message Flow (Fallback)

```
User types: "Aaj subah BP 150 tha, sugar 180"
  |
  v
Same structuring pipeline as voice
  |
  v
Preview -> Confirm -> Save
```

### 4.6 Photo Upload Flow (Prescriptions/Reports)

```
User sends photo of prescription
  |
  v
Bot: "Photo mil gayi. Main dawa aur salah padh raha hoon..."
  |
  v
Groq Vision (Llama-4-Scout) extracts:
  - Medicine names
  - Dosage
  - Duration
  - Doctor's notes
  |
  v
Bot: "Maine samjha:
      - Dawa 1: Telma 40 - 1 goli subah
      - Dawa 2: Metformin 500 - 1 goli raat ko
      - Doctor ne kaha: 1 hafte baad dubara check karein

      Kya yeh sahi hai? [Haan] [Nahi]"
  |
  v
User confirms -> Save as memory cards
```

### 4.7 Medication Reminder Flow (Telegram)

```
User: /reminders
Bot: "Aapki dawa:
      8:00 AM - Telma 40 [On]
      9:00 PM - Metformin 500 [On]

      [Nayi dawa jodo]"

User taps [Nayi dawa jodo]
Bot: "Dawa ka naam?"
User: "Calcium tablet"
Bot: "Kitni baar?"
Inline keyboard: [Subah] [Dopahar] [Raat] [Subah+Raat]
User: [Subah+Raat]
Bot: "Kitne baje?"
User: "8 baje subah, 8 baje raat"
Bot: "Calcium tablet - 8 AM & 8 PM. Yaad dilaya jayega!"

--- At 8 AM ---
Bot: "Savitri ji, Telma 40 aur Calcium tablet ka time ho gaya!
      [Le liya] [10 min baad yaad dilana]"

User taps [Le liya]
Bot: "Record kar liya. Achi baat!"
-> Logged as memory: "Took Telma 40 and Calcium tablet at 8 AM"
-> Caregiver dashboard updates
```

### 4.8 Emergency Flow

```
User taps /emergency OR sends "madad" / "help" / "bachao"
  |
  v
Bot: "EMERGENCY ALERT BHEJA GAYA!
      Aapke parivaar ko SMS aur call kar diya gaya hai.
      Kya hua? Bata sakte hain?"
  |
  v
User sends voice: "Gir gayi hoon, pair dard ho raha hai"
  |
  v
Bot logs emergency memory
  |
  v
Backend triggers:
  1. SMS to caregiver: "Savitri ji ne emergency alert bheja: 'Gir gayi hoon, pair dard ho raha hai'. Location: [if shared]"
  2. Push notification to caregiver app
  3. Emergency memory card saved with HIGH urgency score (5/5)
```

### 4.9 Technical Implementation

```python
# telegram_bot.py - FastAPI webhook handler

from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g., https://smriti.onrender.com/telegram

app = FastAPI()

# Initialize bot application
bot_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

async def start(update: Update, context):
    """Handle /start - onboarding flow"""
    user = update.effective_user
    chat_id = update.effective_chat.id

    # Check if user exists by phone (will be shared later) or chat_id
    existing = await get_user_by_telegram_chat_id(chat_id)

    if existing:
        await update.message.reply_text(
            f"Namaste {existing['subject_name']} ji! \n"
            f"Main Smriti hoon. Aap apni health update bata sakte hain.\n\n"
            f"Commands:\n/record - Health note bhejein\n"
            f"/ask - Kuch puchna ho\n"
            f"/summary - Doctor ke liye summary\n"
            f"/reminders - Dawa ka time\n"
            f"/emergency - Madad chahiye"
        )
    else:
        # Request phone number
        keyboard = [[InlineKeyboardButton("Phone number share karein", request_contact=True)]]
        await update.message.reply_text(
            "Namaste! Main Smriti hoon - aapka health saathi. \n\n"
            "Shuru karne ke liye, kripya apna phone number share karein:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def handle_contact(update: Update, context):
    """Handle phone number sharing"""
    contact = update.message.contact
    phone = contact.phone_number
    chat_id = update.effective_chat.id

    # Link or create user
    user = await link_or_create_user(phone=phone, telegram_chat_id=chat_id)

    await update.message.reply_text(
        f"Dhanyavaad! Aapka account taiyaar hai.\n\n"
        f"Ab bas boliye ya type kijiye - main yaad rakhungi!\n\n"
        f"Try karein: /record"
    )

async def handle_voice(update: Update, context):
    """Handle voice messages - primary input method"""
    chat_id = update.effective_chat.id
    user = await get_user_by_telegram_chat_id(chat_id)

    if not user:
        await update.message.reply_text("Pehle /start karein aur phone number share karein.")
        return

    # Download voice file
    voice_file = await update.message.voice.get_file()
    voice_bytes = await voice_file.download_as_bytearray()

    # Show typing indicator
    await update.message.reply_text("Sun raha hoon...")

    # STT via Groq Whisper
    transcript = await groq_stt(voice_bytes, language="auto")

    # Structure via Groq
    memory_cards = await groq_structure(transcript, user["subject_id"])

    # Build preview message
    preview = build_preview(memory_cards)

    # Store in context for confirmation
    context.user_data["pending_memory"] = memory_cards
    context.user_data["transcript"] = transcript

    keyboard = [
        [InlineKeyboardButton("Haan, sahi hai", callback_data="confirm_save")],
        [InlineKeyboardButton("Nahi, dobara bolunga", callback_data="cancel_save")],
        [InlineKeyboardButton("Edit karna hai", callback_data="edit_memory")]
    ]

    await update.message.reply_text(
        f"Mainne samjha:\n\n{preview}\n\nKya yeh sahi hai?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_confirm(update: Update, context):
    """Handle confirmation button"""
    query = update.callback_query
    await query.answer()

    chat_id = update.effective_chat.id
    user = await get_user_by_telegram_chat_id(chat_id)
    memory_cards = context.user_data.get("pending_memory")

    if not memory_cards:
        await query.edit_message_text("Kuch galat ho gaya. Dobarah /record karein.")
        return

    # Save to Supermemory
    for card in memory_cards:
        await save_memory(
            text=card["text"],
            type=card["type"],
            subject_id=user["subject_id"],
            subject_name=user["subject_name"],
            persona="elder",
            source="telegram",
            telegram_chat_id=chat_id
        )

    # Run urgency scoring
    urgency = await score_urgency(memory_cards, user["subject_id"])

    # Notify caregiver if urgent
    if urgency["score"] >= 4:
        await notify_caregiver(user, urgency, context.user_data.get("transcript", ""))

    await query.edit_message_text(
        f"Yaad rakh liya! {len(memory_cards)} cheezein save ho gayi.\n\n"
        f"Aapki beti ko bata diya gaya."
    )

    # Clear pending
    context.user_data.pop("pending_memory", None)

async def handle_emergency(update: Update, context):
    """Handle emergency command"""
    chat_id = update.effective_chat.id
    user = await get_user_by_telegram_chat_id(chat_id)

    # Log emergency
    await save_memory(
        text="Emergency alert triggered via Telegram",
        type="emergency",
        subject_id=user["subject_id"],
        subject_name=user["subject_name"],
        persona="elder",
        source="telegram",
        urgency_score=5
    )

    # Send SMS to caregiver
    await send_emergency_sms(user)

    # Send push to caregiver dashboard
    await send_emergency_push(user)

    await update.message.reply_text(
        "EMERGENCY ALERT BHEJA GAYA!\n\n"
        "Aapke parivaar ko SMS aur notification bhej diya gaya hai.\n"
        "Kya hua? Bata sakte hain? Main record kar raha hoon."
    )

async def handle_ask(update: Update, context):
    """Handle /ask - question answering from memory"""
    chat_id = update.effective_chat.id
    user = await get_user_by_telegram_chat_id(chat_id)

    # Check if question is in context
    if context.args:
        question = " ".join(context.args)
    else:
        await update.message.reply_text("Kya puchna chahte hain? Type karein ya boliye.")
        return

    # Retrieve from Supermemory
    memories = await retrieve_memories(user["subject_id"], question)

    # Generate answer via Groq
    answer = await groq_answer(question, memories, user["subject_name"])

    await update.message.reply_text(f"{answer}")

async def handle_summary(update: Update, context):
    """Handle /summary - generate visit summary"""
    chat_id = update.effective_chat.id
    user = await get_user_by_telegram_chat_id(chat_id)

    # Get last 30 days memories
    memories = await retrieve_memories_by_date(user["subject_id"], days=30)

    # Generate summary
    summary = await generate_visit_summary(memories, user["subject_name"])

    # Generate PDF
    pdf_url = await generate_pdf_summary(summary, user["subject_name"])

    await update.message.reply_text(
        f"{user['subject_name']} ji ka health summary (last 30 days):\n\n"
        f"{summary}\n\n"
        f"PDF: {pdf_url}\n"
        f"Doctor ke saath share kar sakte hain."
    )

# Register handlers
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("record", handle_voice))
bot_app.add_handler(CommandHandler("ask", handle_ask))
bot_app.add_handler(CommandHandler("summary", handle_summary))
bot_app.add_handler(CommandHandler("emergency", handle_emergency))
bot_app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
bot_app.add_handler(MessageHandler(filters.VOICE, handle_voice))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
bot_app.add_handler(CallbackQueryHandler(handle_confirm, pattern="^confirm_save$"))
bot_app.add_handler(CallbackQueryHandler(handle_cancel, pattern="^cancel_save$"))

# FastAPI webhook endpoint
@app.post("/telegram")
async def telegram_webhook(request: Request):
    """Receive updates from Telegram"""
    update = Update.de_json(await request.json(), bot_app.bot)
    await bot_app.process_update(update)
    return {"status": "ok"}

@app.on_event("startup")
async def set_webhook():
    """Set webhook on startup"""
    await bot_app.bot.set_webhook(WEBHOOK_URL)
```

### 4.10 Bot UI Principles

- **Bilingual:** All bot messages in Hindi + English. Primary Hindi.
- **Emoji-heavy:** Visual cues for low-literacy users.
- **Minimal text:** No paragraphs. 2-3 lines max per message.
- **Inline keyboards:** Taps over typing wherever possible.
- **Voice-first:** Encourage voice messages. Text is fallback.
- **Confirmation loop:** Always preview -> confirm -> save. No silent saves.

---

## 5. Web App Feature Specifications

### 5.1 Authentication & Family Roles

**Tech:** Firebase Authentication (email/password + Google Sign-In)

**User Roles:**

| Role | Permissions | Onboarding |
|---|---|---|
| **Elder** | Add memories (voice/text/photo), view own timeline, trigger emergency, set reminders | Phone OTP + name + age + language preference |
| **Caregiver** | View elder's timeline, charts, alerts, summaries. Cannot edit elder's memories without permission. | Google sign-in + link to elder via phone number or invite code |
| **Admin (Family Head)** | Full permissions across all family members. Can add/remove caregivers. | Same as caregiver + family creation |

**Family Linking Flow:**
```
Caregiver signs up -> Creates "Family" -> Gets 6-digit invite code
Elder signs up -> Enters invite code -> Linked to family
Multiple caregivers can join with same code
```

### 5.2 Elder Dashboard (Mobile-First)

**Screen 1: Home**
```
+----------------------------------+
|  Namaste, Savitri ji             |
|                                  |
|  [    BOLIYE    ]                |  <- Big voice button
|                                  |
|  [Photo upload]                  |
|                                  |
|  [MADAD CHAHIYE]                 |  <- Red emergency button
|                                  |
|  Aaj ki dawa:                    |
|     [x] Telma 40 (8 AM)         |
|     [ ] Calcium (8 PM)          |
|                                  |
|  Aapka BP (7 din):               |
|     [simple sparkline]           |
|     145 -> 142 -> 148 -> 140    |
|                                  |
|  [Timeline] [Ask] [Summary]     |
+----------------------------------+
```

**Design specs:**
- Font size: 18px minimum, 24px for buttons
- High contrast: White background, black text, colored accents only for actions
- Touch targets: 56px minimum
- No hamburger menus. Everything visible or one tap away.

**Screen 2: Voice Input -> Preview -> Confirm**
```
User taps BOLIYE -> Recording starts -> Release to stop
  |
  v
Transcript shown (Hindi + English if mixed)
  |
  v
AI-structured cards shown:
  - BP: 145/95
  - Medicine: Dabur Chyawanprash
  - Date: 6 Aug 2026
  |
  v
[Sahi hai] [Dobarah] [Edit]
```

**Screen 3: Timeline**
```
Chronological list of all memories for selected person
Filter by: All | BP | Sugar | Medicine | Doctor Visit | Emergency
Each card shows: icon, text, date, source (Web/Telegram)
Tap to expand: full details + source memory debug
```

### 5.3 Caregiver Dashboard (Desktop + Mobile)

**Screen 1: Family Overview**
```
+------------------------------------------------+
|  Sharma Family                                 |
|                                                |
|  +-------------+  +-------------+              |
|  | Savitri     |  | Ram         |              |
|  | [Active]    |  | [2 days]    |              |
|  | BP: 145/95  |  | No update   |              |
|  | Last: Today |  | Last: 4 Aug |              |
|  | [View]      |  | [View]      |              |
|  +-------------+  +-------------+              |
|                                                |
|  Alerts:                                       |
|  ! Savitri's BP high for 3 days               |
|  X Ram hasn't logged in for 2 days            |
|                                                |
+------------------------------------------------+
```

**Screen 2: Individual Elder View**
```
Tabs: Timeline | Charts | Summary | Reminders | Settings

Charts tab:
  - BP over time (line chart, 7/30/90 days)
  - Blood Sugar over time
  - Medication adherence (bar chart)
  - Weight over time

Summary tab:
  - Auto-generated visit summary
  - [Download PDF] [Share via WhatsApp]

Reminders tab:
  - View all active reminders
  - Add new reminder for elder
  - See adherence rate
```

### 5.4 Medication Reminder System

**Data Model:**
```json
{
  "reminder_id": "uuid",
  "subject_id": "savitri_devi",
  "medicine_name": "Telma 40",
  "dosage": "1 tablet",
  "schedule": {
    "type": "daily",
    "times": ["08:00", "20:00"],
    "days": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
  },
  "start_date": "2026-08-01",
  "end_date": null,
  "instructions": "After food",
  "created_by": "caregiver_id",
  "status": "active"
}
```

**Reminder Delivery:**
- Push notification (web)
- Telegram message (if linked)
- SMS fallback (if no Telegram/web activity in 15 min)

**Adherence Logging:**
- Elder taps "Le liya" / "Taken" -> logged as memory
- Missed dose -> logged as "Missed: Telma 40 at 8 AM"
- 3 missed doses in a row -> caregiver alert

### 5.5 Health Trend Charts

**Data Extraction Pipeline:**
```
Memory text: "BP 145/95 today morning"
  |
  v
Regex + Groq extraction: {"type": "bp", "systolic": 145, "diastolic": 95, "unit": "mmHg"}
  |
  v
Store in vitals table (separate from memory for charting)
  |
  v
Chart.js renders line chart with date filters
```

**Supported Vitals:**
- Blood Pressure (systolic/diastolic)
- Blood Sugar (fasting/post-meal)
- Weight
- Temperature
- SpO2
- Heart Rate

### 5.6 Emergency Button

**Trigger Methods:**
1. Web app: Big red button on home screen
2. Telegram: /emergency command or "madad"/"help"/"bachao"
3. Long-press volume button (future - requires native app)

**Emergency Flow:**
```
Trigger -> Log emergency memory (urgency_score: 5)
      -> Send SMS to all caregivers
      -> Send push notification to caregiver dashboard
      -> Send Telegram message to caregivers
      -> If no response in 10 min -> escalate to secondary contact
      -> If no response in 20 min -> suggest calling 112
```

**SMS Template:**
```
SMRITI EMERGENCY ALERT
Savitri Devi (Varanasi) needs help.
Message: "Gir gayi hoon, pair dard ho raha hai"
Location: [if shared]
Time: 6 Aug 2026, 10:30 AM
Reply HELP for next steps.
```

### 5.7 Urgency Scoring (AI Feature)

**Purpose:** Detect patterns that need caregiver attention without diagnosing.

**Scoring Logic:**
```python
async def score_urgency(memory_cards, subject_id):
    score = 1  # Default: green
    reasons = []

    for card in memory_cards:
        # BP analysis
        if card["type"] == "bp":
            if card["systolic"] > 180 or card["diastolic"] > 110:
                score = max(score, 5)
                reasons.append("BP critically high")
            elif card["systolic"] > 140 or card["diastolic"] > 90:
                # Check history
                recent_bp = await get_recent_vitals(subject_id, "bp", days=7)
                high_count = sum(1 for b in recent_bp if b["systolic"] > 140)
                if high_count >= 3:
                    score = max(score, 4)
                    reasons.append(f"BP high for {high_count} days")
                else:
                    score = max(score, 3)
                    reasons.append("BP elevated")

        # Sugar analysis
        if card["type"] == "sugar":
            if card["value"] > 300:
                score = max(score, 4)
                reasons.append("Sugar critically high")
            elif card["value"] > 200:
                score = max(score, 3)
                reasons.append("Sugar elevated")

        # Missed medication
        if card["type"] == "missed_medicine":
            recent_missed = await get_recent_memories(subject_id, "missed_medicine", days=7)
            if len(recent_missed) >= 3:
                score = max(score, 3)
                reasons.append("Multiple missed doses")

        # Emergency
        if card["type"] == "emergency":
            score = 5
            reasons.append("Emergency alert triggered")

    return {
        "score": score,  # 1-5
        "level": ["green", "blue", "yellow", "orange", "red"][score - 1],
        "reasons": reasons,
        "action": get_recommended_action(score)
    }
```

**Actions by Score:**
| Score | Color | Action |
|---|---|---|
| 1 | Green | Log silently |
| 2 | Blue | Show on dashboard, no alert |
| 3 | Yellow | Notify caregiver (non-urgent) |
| 4 | Orange | Notify caregiver + suggest check-in call |
| 5 | Red | Immediate SMS + push + suggest calling elder |

### 5.8 Visit Summary PDF Export

**Template:**
```
+----------------------------------------+
|  SMRITI HEALTH SUMMARY                 |
|  Patient: Savitri Devi                 |
|  Period: 1 Jul 2026 - 6 Aug 2026       |
|  Generated: 6 Aug 2026                 |
+----------------------------------------+
|  VITAL TRENDS                          |
|  * BP: Avg 142/92 (elevated)           |
|  * Sugar: Avg 165 mg/dL (controlled)   |
|  * Weight: 58kg -> 57kg                |
+----------------------------------------+
|  MEDICATION ADHERENCE                  |
|  * Telma 40: 85% (missed 4 doses)      |
|  * Metformin: 92% (missed 2 doses)     |
+----------------------------------------+
|  KEY EVENTS                            |
|  * 15 Jul: Doctor visit - BP noted high|
|  * 22 Jul: Started new medicine        |
|  * 1 Aug: Fall - no injury reported    |
+----------------------------------------+
|  DOCTOR'S NOTES                        |
|  [Extracted from prescription photos]  |
|  * Reduce salt intake                  |
|  * Follow-up in 2 weeks                |
+----------------------------------------+
|  ALERTS                                |
|  * BP elevated for 5 of last 7 days    |
|  * 2 missed doses this week            |
+----------------------------------------+
```

**Tech:** Python `reportlab` or `weasyprint` for PDF generation.

---

## 6. Data Model

### 6.1 Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    firebase_uid VARCHAR(255) UNIQUE,
    phone VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(255),
    name VARCHAR(255) NOT NULL,
    role ENUM('elder', 'caregiver', 'admin') DEFAULT 'elder',
    language_preference VARCHAR(10) DEFAULT 'hi',
    telegram_chat_id BIGINT,
    family_id UUID REFERENCES families(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 6.2 Families Table
```sql
CREATE TABLE families (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    invite_code VARCHAR(10) UNIQUE NOT NULL,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 6.3 Memories Table (Supermemory or PostgreSQL)
```sql
CREATE TABLE memories (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    subject_id VARCHAR(255) NOT NULL,
    subject_name VARCHAR(255) NOT NULL,
    text TEXT NOT NULL,
    type VARCHAR(50),
    structured_data JSONB,
    source VARCHAR(50) DEFAULT 'web',
    telegram_chat_id BIGINT,
    urgency_score INT DEFAULT 1,
    occurred_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 6.4 Vitals Table (For Charting)
```sql
CREATE TABLE vitals (
    id UUID PRIMARY KEY,
    memory_id UUID REFERENCES memories(id),
    user_id UUID REFERENCES users(id),
    subject_id VARCHAR(255) NOT NULL,
    vital_type VARCHAR(50) NOT NULL,
    value NUMERIC,
    value_secondary NUMERIC,
    unit VARCHAR(20),
    recorded_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 6.5 Reminders Table
```sql
CREATE TABLE reminders (
    id UUID PRIMARY KEY,
    subject_id VARCHAR(255) NOT NULL,
    medicine_name VARCHAR(255) NOT NULL,
    dosage VARCHAR(100),
    schedule JSONB NOT NULL,
    instructions TEXT,
    created_by UUID REFERENCES users(id),
    status ENUM('active', 'paused', 'completed') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 6.6 Reminder Logs Table
```sql
CREATE TABLE reminder_logs (
    id UUID PRIMARY KEY,
    reminder_id UUID REFERENCES reminders(id),
    scheduled_time TIMESTAMP NOT NULL,
    taken_at TIMESTAMP,
    status ENUM('pending', 'taken', 'missed', 'snoozed') DEFAULT 'pending',
    response_source VARCHAR(50)
);
```

---

## 7. Technical Architecture

### 7.1 System Diagram

```
+---------------------------------------------------------------+
|                         CLIENTS                                |
|  +--------------+  +--------------+  +----------------------+  |
|  |  Web App     |  |  Telegram    |  |  Caregiver Dashboard |  |
|  |  (React)     |  |  Bot         |  |  (React Desktop)     |  |
|  |  Mobile-first|  |  (Python)    |  |  Responsive          |  |
|  +------+-------+  +------+-------+  +----------+-----------+  |
+--------|----------|----------|-------------------|-------------+
         |          |          |
         +----------+----------+
                    |
            +-------v--------+
            |   FastAPI App   |
            |   (Render)      |
            |                 |
            |  * Auth (Firebase)
            |  * Memory API
            |  * Telegram webhook
            |  * Reminder cron
            |  * PDF generation
            |  * Urgency scoring
            +-------+--------+
                    |
        +-----------+-----------+
        |           |           |
  +-----v-----+ +---v-------+ +---v-------+
  |  Groq AI  | |Supermemory| |PostgreSQL |
  |  * STT    | |  * Vector | |  * Users  |
  |  * Struct | |    store  | |  * Families|
  |  * Vision | |  * Search | |  * Vitals |
  |  * Answer | |  * RAG    | |  *Reminders|
  |  * Summary| |           | |  * Logs   |
  +-----------+ +-----------+ +-----------+
        |
  +-----v-----+
  |  External |
  |  Services |
  |  * Twilio |  (SMS for emergency)
  |  *Firebase| (Auth, Push)
  |  *Telegram| (Bot API)
  +-----------+
```

### 7.2 API Endpoints

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/api/auth/register` | POST | No | Register new user |
| `/api/auth/login` | POST | No | Login, return JWT |
| `/api/families` | POST | Yes | Create family |
| `/api/families/join` | POST | Yes | Join family with invite code |
| `/api/memories` | POST | Yes | Add memory (voice/text/photo) |
| `/api/memories` | GET | Yes | Retrieve memories with filters |
| `/api/memories/ask` | POST | Yes | Ask question from memories |
| `/api/memories/summary` | POST | Yes | Generate visit summary |
| `/api/memories/summary/pdf` | GET | Yes | Download PDF summary |
| `/api/vitals` | GET | Yes | Get vitals for charting |
| `/api/reminders` | POST | Yes | Create reminder |
| `/api/reminders` | GET | Yes | Get reminders |
| `/api/reminders/{id}/log` | POST | Yes | Log taken/missed |
| `/api/urgency/score` | POST | Yes | Score urgency of new memories |
| `/telegram` | POST | No | Telegram webhook |

### 7.3 Environment Variables

```env
# Database
DATABASE_URL=postgresql://...

# Firebase
FIREBASE_PROJECT_ID=...
FIREBASE_PRIVATE_KEY=...
FIREBASE_CLIENT_EMAIL=...

# Groq
GROQ_API_KEY=...
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_STT_MODEL=whisper-large-v3-turbo
GROQ_VISION_MODEL=meta-llama/llama-4-scout-17b-16e-instruct

# Supermemory
SMRITI_MEMORY_MODE=cloud
SUPERMEMORY_BASE_URL=https://api.supermemory.ai
SUPERMEMORY_API_KEY=...

# Telegram
TELEGRAM_BOT_TOKEN=...
WEBHOOK_URL=https://smriti.onrender.com/telegram

# SMS (Twilio)
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=...

# App
APP_ENV=production
SECRET_KEY=...
```

---

## 8. AI Prompts & Guardrails

### 8.1 Health Memory Structuring Prompt

```
You are Smriti, a health memory structuring assistant for elderly Indian patients.

INPUT: A voice transcript or text note from an elderly person about their health.
LANGUAGE: The input may be in Hindi, Hinglish, or English. Respond in the same language as the input.

TASK: Extract structured health memory cards from the input. Each card should have:
- text: A clean, structured sentence describing the health fact
- type: One of [bp, sugar, weight, medicine, symptom, doctor_visit, diet, activity, emergency, other]
- occurred_at: The date mentioned (default to today if not specified)
- notes: Any additional context

RULES:
1. DO NOT diagnose. DO NOT recommend medication changes.
2. If the input mentions symptoms that sound serious (chest pain, severe headache, difficulty breathing), add a flag: "urgency": "high"
3. For BP: Extract systolic and diastolic. Example: "BP 150 over 95" -> {"type": "bp", "systolic": 150, "diastolic": 95}
4. For sugar: Extract value and note if fasting or post-meal. Example: "sugar 180 fasting" -> {"type": "sugar", "value": 180, "context": "fasting"}
5. For medicine: Extract name, dosage, and time. Example: "Telma 40 li subah" -> {"type": "medicine", "name": "Telma 40", "dosage": "1 tablet", "time": "morning"}
6. Keep text concise. One fact per card.
7. If the input is unclear, create a card with type "other" and note the ambiguity.

OUTPUT FORMAT: JSON array of memory cards.

EXAMPLE INPUT: "Aaj subah BP 145 tha, sugar 180 fasting, aur Telma 40 le li"
EXAMPLE OUTPUT:
[
  {"text": "BP 145/90 recorded in the morning", "type": "bp", "systolic": 145, "diastolic": 90, "occurred_at": "2026-08-06", "notes": "Morning reading"},
  {"text": "Blood sugar 180 mg/dL (fasting)", "type": "sugar", "value": 180, "context": "fasting", "occurred_at": "2026-08-06"},
  {"text": "Took Telma 40 in the morning", "type": "medicine", "name": "Telma 40", "dosage": "1 tablet", "time": "morning", "occurred_at": "2026-08-06"}
]
```

### 8.2 Question Answering Prompt

```
You are Smriti, a health memory assistant. You help family members recall health facts about their loved ones.

CONTEXT: You have access to the following health memories about {subject_name}:
{retrieved_memories}

USER QUESTION: {question}

RULES:
1. Answer ONLY from the provided memories. If the answer is not in the memories, say: "Mujhe iske baare mein koi record nahi mila. Kripya {subject_name} ji se puch kar record karein."
2. DO NOT make up information. DO NOT diagnose.
3. Be concise. 2-3 sentences max.
4. If the question is about a trend ("How has BP been?"), summarize the pattern.
5. If the question is about a specific event ("When did they last visit the doctor?"), give the exact date if available.
6. Always cite the source memory date.

OUTPUT: Direct answer in the same language as the question.
```

### 8.3 Visit Summary Prompt

```
You are Smriti, a health summary generator for doctor visits.

PATIENT: {subject_name}
PERIOD: Last {days} days
MEMORIES:
{memories}

TASK: Generate a structured visit summary that a doctor can read in 60 seconds.

SECTIONS:
1. VITAL TRENDS: Summarize BP, sugar, weight trends. Note any concerning patterns.
2. MEDICATION ADHERENCE: List medicines and adherence rate.
3. KEY EVENTS: Doctor visits, hospitalizations, falls, new symptoms.
4. CURRENT CONCERNS: Any ongoing symptoms or issues.
5. QUESTIONS FOR DOCTOR: Suggest 2-3 questions based on the data.

RULES:
1. DO NOT diagnose. DO NOT recommend treatment.
2. Use medical terminology where appropriate but keep it readable.
3. Flag any data gaps ("BP recorded only 3 times in 30 days").
4. If there are prescription photos, extract doctor instructions.

OUTPUT: Structured markdown text.
```

### 8.4 Safety Guardrails

```
CRITICAL SAFETY RULES:
1. NEVER diagnose a condition.
2. NEVER recommend specific medication doses.
3. NEVER interpret lab values as "normal" or "abnormal."
4. NEVER dismiss symptoms as "nothing to worry about."
5. ALWAYS suggest consulting a doctor for any health concern.
6. If the user mentions chest pain, severe headache, difficulty breathing, or suicidal thoughts:
   - Immediately flag as high urgency
   - Suggest calling emergency services (112) or Tele-MANAS (14416)
   - Notify caregiver
7. Include disclaimer in every response: "Yeh AI assistant hai. Kripya kisi bhi health concern ke liye doctor se salah lein."
```

---

## 9. UI/UX Design System

### 9.1 Color Palette

| Token | Hex | Usage |
|---|---|---|
| `--primary` | `#1A5F2A` | Primary actions, buttons, headers (trust, health) |
| `--primary-light` | `#E8F5E9` | Button hover, light backgrounds |
| `--accent` | `#FF6F00` | Urgency alerts, reminders, CTAs |
| `--danger` | `#D32F2F` | Emergency button, critical alerts |
| `--warning` | `#F9A825` | Yellow urgency, missed doses |
| `--success` | `#388E3C` | Taken medicine, confirmed actions |
| `--bg` | `#FAFAFA` | Page background |
| `--surface` | `#FFFFFF` | Cards, modals |
| `--text-primary` | `#212121` | Headings, body text |
| `--text-secondary` | `#757575` | Captions, metadata |
| `--border` | `#E0E0E0` | Dividers, card borders |

### 9.2 Typography

| Element | Font | Size | Weight |
|---|---|---|---|
| H1 (Screen title) | Inter / Noto Sans Devanagari | 28px | 700 |
| H2 (Section title) | Inter / Noto Sans Devanagari | 22px | 600 |
| Body | Inter / Noto Sans Devanagari | 18px | 400 |
| Button | Inter / Noto Sans Devanagari | 20px | 600 |
| Caption | Inter / Noto Sans Devanagari | 14px | 400 |
| Elder UI Body | Inter / Noto Sans Devanagari | 20px | 400 |
| Elder UI Button | Inter / Noto Sans Devanagari | 24px | 600 |

### 9.3 Component Specs

**Voice Button (Elder Home):**
```
Size: 120px x 120px (touch target)
Shape: Circle
Color: --primary (#1A5F2A)
Icon: Microphone, 48px, white
Label below: "BOLIYE" (Speak), 20px bold
Animation: Pulse when recording
```

**Emergency Button:**
```
Size: Full width, 72px height
Color: --danger (#D32F2F)
Icon: Alert triangle, 32px
Label: "MADAD CHAHIYE" (Need Help), 22px bold
Position: Fixed bottom or prominent on home screen
Requires: Long-press or confirmation to prevent accidental trigger
```

**Memory Card:**
```
Background: --surface
Border: 1px solid --border
Border-radius: 16px
Padding: 16px
Icon: 32px, left-aligned
Text: 18px, --text-primary
Date: 14px, --text-secondary
Source badge: "Web" or "Telegram", 12px, pill shape
```

**Preview Card (Before Save):**
```
Background: --primary-light
Border: 2px dashed --primary
Border-radius: 16px
Padding: 16px
Editable: Inline editing enabled
Actions: [Confirm] [Cancel] [Edit]
```

---

## 10. Security & Privacy

### 10.1 Data Protection

| Feature | Implementation |
|---|---|
| Encryption at rest | PostgreSQL encrypted volumes |
| Encryption in transit | HTTPS everywhere, TLS 1.3 |
| API authentication | Firebase JWT tokens, 1-hour expiry |
| Data minimization | Only store health data user explicitly shares |
| Right to deletion | One-click "Delete all my data" in settings |
| Audit log | All data access logged |

### 10.2 Privacy Manifesto (Public-facing)

```markdown
# Smriti Privacy Promise

1. **Your data is yours.** We never sell health data to third parties.
2. **Family-only.** Only people you explicitly invite can see your health data.
3. **Delete anytime.** One tap deletes all your data permanently.
4. **No ads.** We don't show ads based on your health conditions.
5. **AI transparency.** We tell you exactly what our AI understood before saving.
6. **Local-first option.** Use Supermemory Local to keep data on your own server.
```

### 10.3 Compliance

- **DPDP Act 2023:** Consent-based data collection, right to deletion, data localization
- **HIPAA-inspired:** Not full HIPAA (not US healthcare), but follows principles
- **Tele-MANAS integration:** Only with explicit user consent per call

---

## 11. Deployment Plan

### 11.1 Pre-Hackathon Checklist (Aug 6-10)

| Day | Task | Owner |
|---|---|---|
| Aug 6 (Today) | Add Firebase Auth + family roles | You |
| Aug 6 (Today) | Create Telegram Bot + webhook | You |
| Aug 7 | Hindi STT + caregiver dashboard | You |
| Aug 7 | Medication reminders + trend charts | You |
| Aug 8 | Emergency button + urgency scoring | You |
| Aug 8 | PDF export + WhatsApp share | You |
| Aug 9 | Deploy to Render, test live URL | You |
| Aug 9 | Record demo video (Loom, 3 min) | You |
| Aug 10 | Polish UI, fix bugs, submit | You |

### 11.2 Render Deployment

```yaml
# render.yaml
services:
  - type: web
    name: smriti-api
    runtime: python
    plan: starter
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port 10000
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: smriti-db
          property: connectionString
      - key: GROQ_API_KEY
        sync: false
      - key: FIREBASE_PROJECT_ID
        sync: false
      - key: TELEGRAM_BOT_TOKEN
        sync: false
      - key: WEBHOOK_URL
        value: https://smriti-api.onrender.com/telegram

databases:
  - name: smriti-db
    plan: starter
```

### 11.3 Telegram Bot Setup

1. Message @BotFather on Telegram
2. Send `/newbot`
3. Name: `Smriti Health Saathi`
4. Username: `SmritiDadiBot`
5. Copy the token -> set as `TELEGRAM_BOT_TOKEN`
6. Set webhook: `curl -F "url=https://your-render-url/telegram" https://api.telegram.org/bot<TOKEN>/setWebhook`

### 11.4 GitHub Repo Structure

```
smriti-health-saathi/
├── .github/
│   └── workflows/
│       └── deploy.yml
├── docs/
│   ├── architecture.md
│   └── prd.md
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── VoiceRecorder.jsx
│   │   │   ├── MemoryCard.jsx
│   │   │   ├── PreviewCard.jsx
│   │   │   ├── VitalChart.jsx
│   │   │   ├── EmergencyButton.jsx
│   │   │   └── CaregiverDashboard.jsx
│   │   ├── pages/
│   │   │   ├── ElderHome.jsx
│   │   │   ├── CaregiverDashboard.jsx
│   │   │   ├── Timeline.jsx
│   │   │   └── Settings.jsx
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── App.jsx
│   │   └── index.css
│   ├── index.html
│   └── package.json
├── smriti/
│   ├── __init__.py
│   ├── models.py
│   ├── config.py
│   ├── clients/
│   │   ├── groq_client.py
│   │   ├── supermemory_client.py
│   │   ├── firebase_client.py
│   │   └── twilio_client.py
│   ├── services/
│   │   ├── memory_service.py
│   │   ├── auth_service.py
│   │   ├── reminder_service.py
│   │   ├── urgency_service.py
│   │   └── pdf_service.py
│   └── routers/
│       ├── auth.py
│       ├── memories.py
│       ├── vitals.py
│       ├── reminders.py
│       └── telegram.py
├── telegram_bot.py
├── main.py
├── requirements.txt
├── render.yaml
├── Dockerfile
├── README.md
└── .env.example
```

---

## 12. Demo Day Script (3 Minutes)

### 12.1 Opening (0:00-0:30)

> "My Dadi lives in Varanasi. My mother lives in Mumbai. Every morning, my mother calls to ask three questions: Did you take your medicine? What was your BP? What did the doctor say last week? 
>
> Smriti answers all three - without Dadi typing a single word. Because Dadi can't type. But she can speak."

### 12.2 Live Demo: Dadi's Phone (0:30-1:15)

**Screen: Mobile web app or Telegram**

1. **Show home screen:** Big "BOLIYE" button. Hindi labels. Large fonts.
2. **Tap BOLIYE:** Record voice in Hindi: "Aaj subah BP 145 tha, sugar 180 fasting, aur Telma 40 le li. Thoda chakkar aa raha tha."
3. **Show preview:** AI structured it into 4 cards - BP, Sugar, Medicine, Symptom.
4. **Tap Sahi hai:** Saved. Notification: "Aapki beti ko bata diya gaya."

### 12.3 Live Demo: Beti's Laptop (1:15-1:45)

**Screen: Caregiver dashboard**

1. **Switch to laptop:** "Now my mother in Mumbai opens her dashboard."
2. **Show real-time update:** Dadi's memory appeared instantly.
3. **Show trend chart:** "BP has been 145+ for 5 days. Yellow flag."
4. **Show urgency alert:** "Chakkar aa raha tha" -> Urgency score 3 -> "Suggest calling Dadi."
5. **Show visit summary:** "Next doctor visit? One click, PDF generated. Share on WhatsApp."

### 12.4 Telegram Bot Demo (1:45-2:15)

**Screen: Telegram on phone**

1. "But what if Dadi doesn't even open the app?"
2. **Show Telegram:** Send voice message to @SmritiDadiBot
3. **Same flow:** Speak -> Preview -> Confirm -> Saved
4. "She already knows WhatsApp. Smriti meets her where she is."

### 12.5 Closing (2:15-2:30)

> "300 million elderly Indians by 2050. Most can't type. Most of their children live in other cities. Smriti is the first health memory built for them - voice-first, family-connected, and actually usable.
>
> This isn't a health app. This is peace of mind for Indian families."

---

## 13. Success Metrics

### 13.1 Hackathon Judging Metrics

| Metric | Target | How to Measure |
|---|---|---|
| Demo completion | 100% | All features demoed without crashes |
| Hindi voice accuracy | >85% | Test with 10 Hindi phrases, count correct |
| Real-time sync | <3 sec | Time from voice save to caregiver dashboard update |
| Mobile usability | Score 8+/10 | Test with one real elder, observe confusion |
| Code quality | Clean commits | No "fix bug" commits, good README |

### 13.2 Post-Launch Metrics (Month 1-3)

| Metric | Target |
|---|---|
| Active elders | 50 families |
| Daily voice notes | 3+ per elder |
| Caregiver engagement | 70% open dashboard weekly |
| Medication adherence | 80%+ (vs 50% baseline) |
| Emergency response time | <5 min from trigger to caregiver notification |
| NPS score | >50 |

---

## 14. Post-Hackathon Roadmap

### 14.1 Fellowship Phase (Months 1-3)

**Month 1: Validation**
- Onboard 50 families through personal networks
- Partner with 1 local clinic for doctor feedback
- Iterate on UI based on real elder usage

**Month 2: Scale**
- WhatsApp Bot (not just Telegram - WhatsApp is where Indian elders live)
- ASHA worker integration (log vitals during home visits)
- Regional language expansion (Tamil, Bengali, Marathi)

**Month 3: Revenue Model**
- **Freemium:** Free for families, Rs 99/month for advanced analytics + unlimited PDFs
- **B2B:** Sell to old age homes and geriatric clinics
- **Government:** Pilot with National Programme for Health Care of Elderly (NPHCE)

### 14.2 Long-term Vision (6-12 Months)

- **Tele-MANAS Integration:** One-tap mental health support for elderly loneliness
- **Fall Detection:** Phone accelerometer + smartwatch integration
- **Medication Delivery:** Partner with 1mg/PharmEasy for medicine reminders -> one-tap reorder
- **Insurance Integration:** Share structured health data with insurers for preventive care discounts

---

## 15. Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Hindi STT accuracy low | Medium | High | Fallback to text input + manual correction UI |
| Elders don't adopt | Medium | Critical | Start with caregivers driving adoption; Telegram bot reduces friction |
| Data privacy concerns | Medium | High | Privacy manifesto, local-first option, DPDP compliance |
| Groq API costs | Low | Medium | Rate limiting, caching, fallback to cheaper models |
| Competition from big players | Low | Medium | Niche focus on Indian elderly + voice-first = moat |
| Emergency liability | Low | High | Clear disclaimers, suggest 112, not a replacement for emergency services |

---

## 16. Appendices

### 16.1 Glossary

| Term | Definition |
|---|---|
| **STT** | Speech-to-Text |
| **RAG** | Retrieval-Augmented Generation |
| **Supermemory** | Vector database for semantic memory storage |
| **ASHA** | Accredited Social Health Activist - community health worker in India |
| **Tele-MANAS** | India's 24/7 mental health helpline (14416) |
| **DPDP** | Digital Personal Data Protection Act 2023 |

### 16.2 Research Citations

1. TCS Research: "Most elderly care solutions remain fragmented, single-dimension offerings lacking integrated, AI-driven, longitudinal care capabilities."
2. Systematic Review (350 mental health apps): "65.1% apps did not mention involvement of mental health professionals. Absence of crisis support."
3. India Census: "300 million elderly by 2050."
4. ASER Report: "50% of Grade 5 students cannot do basic subtraction." (Context: education gap parallels health literacy gap)
5. Disaster App Review (28,161 reviews): "Signup failures, network dependency, app crashes, battery drain are top complaints."

### 16.3 Competitor Analysis

| Competitor | What They Do | Smriti's Edge |
|---|---|---|
| Practo | Doctor booking + records | No voice-first. No family coordination. |
| 1mg | Medicine delivery | No health memory. No elderly-focused UI. |
| mfine | Telemedicine | No longitudinal memory. No family dashboard. |
| Emoha | Elderly care services | Expensive. No AI voice input. No open source. |
| Generic health apps (Fitbit, Apple Health) | Western-focused, typing-dependent | No Hindi. No family roles. No Indian context. |

---

**Document Owner:** Smriti Team  
**Last Updated:** 6 Aug 2026  
**Status:** Draft -> Final by Aug 7

---

*"Boli. Yaad Rakh. Parivaar Judaa."*
