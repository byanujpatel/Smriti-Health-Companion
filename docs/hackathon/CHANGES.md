# Engineering Changes Plan

## Current Product Direction

Transform Smriti from a general AI memory assistant into **Smriti Saathi**, a focused family elder-care memory product.

The pivot should reuse existing strengths:

- Voice transcription
- OCR/vision
- Text reasoning
- Retrieval
- Supermemory integration
- Existing frontend/backend foundation

## Change Philosophy

Brand/story pivot hard. Code pivot moderately. Avoid full rewrite.

## Phase 1: Product Framing

### Add

- Smriti Saathi name and tagline
- Elder-care landing page copy
- Safety banner across health-related screens
- Consent language
- Family-care wording

### Replace

- Generic “memory assistant” wording
- Clinical-sounding labels
- “Patient” terminology

### Preferred Language

Use:

- Parent
- Family member
- Care memory
- Check-in
- Noticed changes
- Family attention suggested

Avoid:

- Patient
- Diagnosis
- Risk detected
- Medical alert
- Compliance detected
- Treatment suggestion

## Phase 2: Data Model

### Parent Profile

Add or model:

- Name
- Age optional
- Preferred language
- City
- Relationship
- Medicines
- Important context
- Consent enabled
- Check-in schedule optional

### Check-In Summary

Every voice check-in should store:

- Raw transcript
- Date/time
- Mood summary
- Medicines mentioned
- Missed medicine mention
- Health mentions with exact quote
- Food/sleep/activity/social notes
- One direct quote
- Flags

### Document Summary

Every OCR upload should store:

- Document type
- OCR text
- Extracted medicines
- Doctor/date/follow-up if present
- Instructions if present
- Uncertain fields
- Source filename

## Phase 3: Voice Check-In Flow

### Add Page Or Mode

Create a senior-friendly check-in screen:

- Large button
- Simple prompt
- Voice recording
- Transcription result
- Confirmation screen

### Check-In Questions

Start with 4-5 questions:

1. How are you feeling today?
2. Did you take your medicines?
3. Any pain, dizziness, sleep trouble, or discomfort?
4. Did you eat properly today?
5. Is there anything else you want your family to know?

### AI Output

Use structured JSON or strict markdown with fields:

- overall_mood
- medicines
- health_mentions
- daily_wellbeing
- direct_quote
- flags

## Phase 4: Family Dashboard

### Dashboard Cards

- Today’s status
- Last check-in
- Latest summary
- Care flags
- Recent memories
- Documents
- Ask Smriti

### Care Flags

Start simple and rule-based:

- missed medicine
- dizziness
- fall mention
- pain mention
- poor sleep repeated
- missed check-in
- unclear OCR medicine

### Flag Language

Use:

> Family attention suggested

Do not use:

> Medical emergency detected

## Phase 5: Temporal Reasoning

### Feature 1: Has She Mentioned X Before?

Input:

- User query
- Parent memory timeline

Output:

- Yes/no
- Dates
- Exact quotes
- Related context
- Safety disclaimer

### Feature 2: Weekly Noticed Changes

Input:

- Last 7-14 days check-ins

Find:

- Repeated symptom mentions
- Repeated missed medicine
- Mood change
- Food/sleep changes
- Activity/social decline

Only surface a pattern if it appears 2+ times or is explicitly severe language such as fall/breathing difficulty.

### Feature 3: Medicine + Symptom Timeline

Show events near each other without claiming causality.

Good:

> Medicine was missed on Aug 1. Dizziness was mentioned on Aug 2.

Bad:

> Missing medicine caused dizziness.

## Phase 6: OCR Document Memory

### Prescription Extraction

Extract:

- Doctor name
- Date
- Medicines
- Dosage/frequency
- Duration
- Follow-up date
- Tests
- Instructions
- Unclear fields

### Lab Report Simplification

Extract:

- Test name
- Value
- Unit
- Reference range
- Simple HIGH/LOW/NORMAL if range is explicit

Always include:

> This is not a diagnosis. Share reports with a doctor.

### Document Cross-Reference

When parent mentions medicine or doctor change, search uploaded document memory.

Output:

- Matching document if found
- “No matching uploaded document found” if absent
- Ask family to verify manually

## Phase 7: UI Polish

### Senior Check-In UI

- Big buttons
- High contrast
- Minimal text
- Hindi/English toggle
- One task per screen
- Confirmation after each step

### Family Dashboard UI

- Clear status cards
- Warm copy
- Evidence-first answers
- Dates and quotes visible
- Mobile-first layout

## Phase 8: Demo + Docs

### Add Demo Data

Create sample parent:

- Asha Devi
- Hindi
- BP medicine
- 5-7 check-ins
- 1 prescription OCR example
- repeated dizziness pattern

### Add README Sections

- Mission
- Problem
- Safety boundary
- Tech stack
- Local setup
- Demo flow
- Open-source vision

### Add Screencast Script

Keep to 4-5 minutes:

1. Problem
2. Parent check-in
3. Family dashboard
4. Temporal reasoning
5. Architecture
6. Vision

## Priority List

### P0

- Safety banner
- Parent profile
- Voice check-in to structured summary
- Memory timeline
- Ask Smriti temporal query
- Family dashboard

### P1

- OCR prescription extraction
- Weekly noticed changes
- Demo seed data
- Responsive polish

### P2

- Document cross-reference
- Hindi copy polish
- README mission docs
- Screencast script

### Later

- Real phone calls
- WhatsApp alerts
- Payments
- Multi-family invites
- Caregiver roles
- B2B dashboards

---

## Phase 9: Deploy + Supabase Auth (NEW — Aug 6)

### Why
Hackathon judging criterion: "Real authentication, not a mock-up."
Current localStorage session does not satisfy this. Supabase Auth is the fastest path — no backend changes needed, just client-side JS SDK.

### Changes

**frontend/src/app.js**
- Replace `loadProfile()` / `saveProfile()` with Supabase `signUp` / `signInWithPassword`
- Add `LoginScreen` component (email + password fields, Sign Up / Sign In buttons)
- On successful auth: `supabase.auth.getUser()` → user.id used as subject_id prefix
- Keep all existing profile/memory logic unchanged — only the identity layer changes
- Add sign-out button in Settings tab

**frontend/src/vendor/** (or CDN)
- Add `@supabase/supabase-js` (ESM CDN import — no build step needed)

**frontend/src/constants.js**
- Add `SUPABASE_URL` and `SUPABASE_ANON_KEY` (public, safe to expose in JS)

**render.yaml / .env.example**
- No backend changes needed — Supabase auth is handled entirely client-side

### What Does NOT Change
- All backend endpoints in `main.py`
- All Supermemory memory storage logic
- Subject ID format — just prefix with Supabase user.id
- All AI pipelines (Groq Whisper, Llama, Vision)

---

## Phase 10: Caregiver Dashboard (NEW — Aug 7)

### Why
Most visually impressive addition for the screencast. Shows the "family coordination" story judges respond to. All data already exists in Supermemory — this is a new view, not new backend logic.

### New Backend

**main.py** — add endpoint:
```python
@app.get("/api/dashboard/{subject_id}")
async def get_dashboard(subject_id: str) -> dict:
    # Fetch last 7 days memories from Supermemory
    # Extract: last_checkin, flags, urgency_level, recent_memories
    # Return structured JSON for caregiver view
```

**smriti/services/urgency_service.py** — new file:
```python
def score_urgency(memories: list[MemoryEntry]) -> dict:
    # Rule-based, no LLM needed:
    # - dizziness/chakkar → yellow (3)
    # - chest pain / breathing → red (5)
    # - missed medicine 3+ times → orange (4)
    # - emergency type → red (5)
    # Returns: {"score": 1-5, "level": "green/yellow/orange/red", "reasons": [...]}
```

### New Frontend

**frontend/src/app.js** — add `CaregiverDashboard` component:
- Family member card: name, last seen, latest mood emoji, urgency badge
- Active flags list with color coding
- Memory timeline (last 7 days)
- "Ask Smriti" quick-query field
- Switch between Elder view (mobile) and Caregiver view (desktop) based on screen width or role

**frontend/src/styles.css** — add:
- `.caregiver-dashboard` layout (wider, two-column on desktop)
- `.urgency-badge` colors: green / yellow / orange / red
- `.flag-card` component styles
- `.family-member-card` grid styles

---

## Phase 11: Telegram Bot MVP (NEW — Aug 7-8)

### Why
- Signal 03 (social/impact): "Dadi already uses Telegram. Smriti meets her where she is."
- Signal 01 (AI workflow): Shows the pipeline working on a *different surface* — same AI, new interface
- Signal 02 (usable): A real bot at a real @handle that anyone can open

### Core Philosophy
**The Telegram bot is a new interface to existing services. Zero new AI logic.**
- `create_transcriber()` — already exists
- `create_checkin_structurer()` — already exists
- `save_unique_memories()` — already exists
- `retrieve_memories()` — already exists

### New Files

**telegram_bot.py** — bot handlers (150-200 lines):
```
/start handler → ask name → store in users dict keyed by chat_id
voice message handler → download OGG → Groq Whisper → structure → preview → [Haan/Nahi] buttons
text message handler → same structuring pipeline (fallback for typing)
/ask handler → retrieve_memories → Groq answer → reply with dates + quotes
callback handler → confirm_save / cancel_save
```

**smriti/routers/telegram.py** — webhook endpoint:
```python
@router.post("/telegram")
async def telegram_webhook(request: Request):
    update = Update.de_json(await request.json(), bot_app.bot)
    await bot_app.process_update(update)
    return {"status": "ok"}
```

### Modified Files

**main.py**
- Import and mount telegram router
- On startup: set Telegram webhook URL

**requirements.txt**
- Add: `python-telegram-bot>=21.0`

**render.yaml / .env.example**
- Add: `TELEGRAM_BOT_TOKEN`, `WEBHOOK_URL`

### MVP ONLY — Explicitly Out of Scope for Hackathon
- ❌ Medication reminders / cron scheduler
- ❌ SMS via Twilio
- ❌ Emergency alert chain
- ❌ Photo prescription upload via bot (web app handles this)
- ❌ Multi-family management via bot

---

## Phase 12: Emergency Button + Polish (NEW — Aug 8)

### Why
- Closes the "family coordination" loop visually
- "MADAD CHAHIYE" button is a powerful visual in the screencast
- Takes 2 hours — high impact/effort ratio

### Emergency Button

**main.py** — add endpoint:
```python
@app.post("/api/emergency")
async def emergency_alert(subject_id: str, subject_name: str, message: str = ""):
    # 1. Save emergency memory with urgency_score=5
    # 2. Send email to ALERT_EMAIL using smtplib (Python built-in, no Twilio)
    # 3. Return confirmation
```

**frontend/src/app.js** — add to Elder home screen:
- Big red button: "🆘 MADAD CHAHIYE"
- Long-press or double-tap confirmation to prevent accidents
- On confirm: POST /api/emergency → show "Alert sent to family ✓"

**frontend/src/styles.css**
- `.emergency-btn` — full-width, 72px height, #D32F2F red, white text

### Hindi UI Labels (30 minutes)

**frontend/src/app.js** — string replacements on elder check-in screen:
- "Tap to Speak" → "BOLIYE 🎙️"
- "Confirm" → "SAHI HAI ✓"
- "Redo" → "DOBARA"
- "Saving..." → "Yaad kar raha hoon..."
- "Saved!" → "Yaad rakh liya! ✓"

---

## Updated Priority List (Phases 9-12)

### Must Ship (blocks Silver/Gold eligibility)
- Deploy to Render — live URL
- Supabase Auth — real sign-in, not localStorage

### Should Ship (major demo impact)
- Caregiver dashboard — shows family coordination story
- Telegram Bot MVP — closes "meets elderly where they are" story

### Nice to Have (demo polish)
- Emergency button — visual impact
- Hindi UI labels — cultural authenticity
- Urgency scoring badge — shows AI adds value beyond storage

### Explicitly Out of Scope (post-hackathon)
- WhatsApp Business API
- Twilio SMS
- Medication reminders + cron
- PDF export (weasyprint)
- Firebase Auth (Supabase is simpler and faster)
- Health trend charts (Chart.js) — time-consuming, demo value is lower than Telegram
- PostgreSQL schema migration (Supabase handles this)
