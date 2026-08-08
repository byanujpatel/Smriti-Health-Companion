# Smriti — Local Testing Guide
## Complete end-to-end test checklist before pushing to GitHub / Render

---

## Before You Start

**Run the server in one terminal. Keep it open the whole time.**
```bash
uv run uvicorn main:app --port 8000 --reload
```

**Open the app in your browser:**
```
http://localhost:8000
```

**Keep this file open alongside** — tick each test as you go.

---

## SECTION 1 — Server Health

Open a **second terminal** and run these commands one by one.

### T1.1 — Health check
```bash
curl http://localhost:8000/health
```
**Expected:**
```json
{"status": "ok"}
```

### T1.2 — Status (Groq + Supermemory connected)
```bash
curl http://localhost:8000/status
```
**Expected:**
```json
{
  "api": "ok",
  "supermemory": "ok",
  "groq": "configured",
  "memory_mode": "cloud"
}
```
> ❌ If `supermemory` shows `"error"` — check your `SUPERMEMORY_API_KEY` and `SMRITI_MEMORY_MODE=cloud` in `.env`
> ❌ If `groq` shows `"missing"` — check your `GROQ_API_KEY` in `.env`

---

## SECTION 2 — Welcome Screen & Profile

### T2.1 — Welcome screen loads
Go to `http://localhost:8000`

**Expected:** White screen with "स" logo, "Smriti Saathi", a name input field, "Get Started →" button, safety notice at bottom.

### T2.2 — Create a parent profile
- Type `Asha Devi` in the name field
- Click **Get Started →**

**Expected:** App opens to Home tab. Top bar shows "Asha Devi". Bottom nav shows: 🏠 Home · 🎙️ Check-In · 📄 Upload · 💬 Ask · 👨‍👩‍👧 Family

### T2.3 — Profile persists on reload
- Press `Cmd+R` (refresh)

**Expected:** App reopens directly to Home tab — no name re-entry needed. "Asha Devi" still shown in top bar.

---

## SECTION 3 — Demo Data Load

### T3.1 — Load Asha Devi demo data
- Click **⚙** (settings icon, top right)
- Scroll down to **Demo** section
- Click **Load Demo**

**Expected:** Green message: `✓ Loaded 8 demo memories (Asha Devi scenario)...`

> This seeds: 2 dizziness mentions, 1 missed medicine, BP 148/92, Amlodipine prescription, Dr. Mehta follow-up.
> All tests in Sections 5–7 depend on this data being loaded.

---

## SECTION 4 — Check-In (Voice + Text)

### T4.1 — Check-in screen opens correctly
- Click **🎙️ Check-In** in the bottom nav

**Expected:**
- Section title says **"Aaj kaisa hai? 🙏"**
- 4 warm-up prompts shown in teal boxes
- Section title says **"Boliye ya type karein"**
- Big button: **🎙️ BOLIYE**
- Textarea placeholder: "Aaj subah chakkar aaya…"
- Submit button: **SAHI HAI — Save Karein ✓**

### T4.2 — Text check-in (type manually)
- In the textarea, type: `Aaj subah thoda chakkar tha. Amlodipine le li. Chai piya.`
- Click **SAHI HAI — Save Karein ✓**

**Expected during processing:**
- Button shows spinner + "Yaad kar raha hoon…"

**Expected result screen:**
- Big green checkmark circle
- Title: **"Check-In Saved"** (or "Yaad rakh liya! ✓")
- Mood shown (e.g. "🙂 neutral" or "😊 cheerful")
- Summary text (2-3 sentences)
- A direct quote (e.g. `"Aaj subah thoda chakkar tha"`)
- Flag pills: ⚠ dizziness (or similar)
- Medicines listed: Amlodipine
- Two buttons: **Back to Home** · **New Check-In**

> ✅ This confirms: Groq Whisper + Llama pipeline works, Supermemory save works

### T4.3 — Sample check-in shortcut
- Click **New Check-In**
- Click **Try a sample** (dropdown)
- Click one of the sample phrases — it fills the textarea
- Click **SAHI HAI — Save Karein ✓**

**Expected:** Same result screen as T4.2 (with different content)

### T4.4 — Voice check-in (requires microphone)
> Skip this if you don't have a mic available. It's tested on live URL later.

- Click **🎙️ BOLIYE**
- Allow microphone permission if browser asks
- Say clearly: *"Aaj subah BP 145 tha, dawa le li, thoda chakkar tha"*
- Stop recording

**Expected:**
- Transcript appears in the textarea
- You can edit it before submitting
- Submit → same result screen

---

## SECTION 5 — Family Dashboard (Caregiver View)

> ⚠️ **Load demo data first** (Section 3) if you haven't already.

### T5.1 — Family tab opens
- Click **👨‍👩‍👧 Family** in the bottom nav

**Expected:**
- Header card with "Asha Devi" name
- Urgency badge (green = ✓ All OK, yellow = ⚠ Attention, red = 🆘 Urgent)
- "Last check-in: [time] · 8 memories" (or similar count)
- ↻ Refresh button

### T5.2 — Care flags appear
After loading demo data (which includes dizziness + missed medicine):

**Expected flags shown (as coloured cards in a 2-column grid):**
| Flag | Icon |
|---|---|
| Dizziness | 💫 |
| Missed Medicine | 💊 |

Each flag card shows:
- Icon + label
- Short quote from the memory (italicised)
- Date of the memory

> ✅ If you see these flags, the `/api/dashboard` endpoint + `_extract_flags()` works correctly

### T5.3 — Recent memories list
**Expected:** Below flags, a list of the 10 most recent memories showing type pill + date + text.

### T5.4 — Quick ask from Family tab
- In the "Ask about Asha Devi" section, click the suggestion: **"Has she mentioned dizziness?"**

**Expected:**
- Answer card appears in teal
- Answer mentions dizziness on **July 7** and **July 10**
- Sources shown below (2 dated memory entries)
- Disclaimer: "Smriti recalls recorded facts only. Not a diagnosis."

### T5.5 — Urgency badge reflects data
With dizziness in the demo data:

**Expected:** Urgency badge shows **"⚠ Attention"** in yellow, NOT green.

> If it shows green — the `_score_urgency()` function may need the demo data. Make sure T3.1 was done.

---

## SECTION 6 — Ask Tab (Temporal Reasoning)

> ⚠️ **Load demo data first** (Section 3) — all expected answers below are from Asha Devi's data.

### T6.1 — Suggested question: dizziness history
- Click **💬 Ask** tab
- Click suggestion: **"Has she mentioned dizziness before?"**

**Expected answer (exact quotes from memory):**
```
Yes. Dizziness was mentioned on [2026-07-07] and [2026-07-10].
On July 7, Asha Devi felt dizzy in the morning and had to sit down.
On July 10, she felt dizzy again after getting up — she said "sir ghoom raha tha".
```
Sources shown: 2 cards with dates July 7 and July 10.

> ✅ This is the **killer demo moment** — this exact answer is your hackathon screencast centerpiece.

### T6.2 — Medicine question
- Type or click: **"What medicine is she taking?"**

**Expected answer:**
```
Asha Devi is taking Amlodipine 5mg once daily for blood pressure,
prescribed by Dr. Mehta [2026-07-01].
```

### T6.3 — Missed medicine
- Type: **"Did she miss her medicine recently?"**

**Expected answer:**
```
Yes. Asha Devi missed her Amlodipine dose on July 7, 2026 [2026-07-07].
```

### T6.4 — Blood pressure
- Type: **"What was her blood pressure?"**

**Expected answer:**
```
Blood pressure was recorded as 148/92 on July 10, 2026 [2026-07-10].
```

### T6.5 — Doctor follow-up
- Type: **"When is her follow-up with the doctor?"**

**Expected answer:**
```
Dr. Mehta scheduled a follow-up for Asha Devi on 22 July 2026 [2026-07-01].
```

### T6.6 — Direct quote
- Type: **"What did she say about her head spinning?"**

**Expected answer:**
```
Asha Devi said "sir ghoom raha tha" (head was spinning) after getting up on July 10 [2026-07-10].
```

### T6.7 — Unknown question (no record)
- Type: **"Did she have a fever?"**

**Expected answer:**
```
I don't have a record of that.
```
> ✅ This confirms the model doesn't hallucinate — it only answers from real memories.

---

## SECTION 7 — Document Upload (OCR)

### T7.1 — Upload tab opens
- Click **📄 Upload** tab

**Expected:**
- "Upload Prescription / Report" heading
- Dashed upload zone with 📄 icon
- "Tap to pick file" + "PNG · JPG · PDF"

### T7.2 — Upload a prescription image
You need a test image. Use any of these options:

**Option A — Use the sample Amlodipine prescription:**
```bash
# Download a test prescription image (or use any medical document photo)
# Any photo with text will work for testing OCR
```

**Option B — Use your phone:** Take a photo of any medicine label, doctor's prescription, or even a printed page with medicine names.

**Option C — Create a quick test file:**
```bash
# In a new terminal:
cat > /tmp/test-prescription.txt << 'EOF'
Dr. Mehta's Clinic
Patient: Savitri Devi
Date: 1 Aug 2026
Rx:
1. Telma 40mg - 1 tablet morning after food
2. Metformin 500mg - 1 tablet night after food
Follow-up: 2 weeks
EOF
```
Then upload this as a `.txt` (won't OCR as well as an image but tests the pipeline).

**Expected after upload:**
- Spinner: "Processing…"
- Then: memory cards appear (e.g. "Telma 40 - 1 tablet morning", "Metformin 500mg - 1 tablet night")
- Each card has a checkbox (pre-checked), a type pill, and text
- "Found N memory cards" message

### T7.3 — Save extracted cards
- Leave all cards checked
- Click **Save N Cards**

**Expected:**
- Success: "Saved N cards"
- Cards clear from the screen

### T7.4 — Verify OCR memory in timeline
- Go to **👨‍👩‍👧 Family** tab → click **↻ Refresh**

**Expected:** The newly saved medicine card appears in Recent Memories.

---

## SECTION 8 — Emergency Button

### T8.1 — Emergency button visible on Home tab
- Click **🏠 Home** tab
- Scroll down to bottom of the tab

**Expected:**
- Big **red** button: **🆘 MADAD CHAHIYE**
- Full-width, red background, white text, 19px bold

### T8.2 — Emergency button triggers confirmation
- Click **🆘 MADAD CHAHIYE**

**Expected:**
- Browser confirm dialog: "Send emergency alert to family?"
- Click **Cancel** → nothing happens, no message shown

### T8.3 — Emergency alert is logged
- Click **🆘 MADAD CHAHIYE** again
- This time click **OK** in the confirm dialog

**Expected:**
- Green message: **"✅ Alert sent to family!"**
- (If `ALERT_EMAIL` is set in `.env`, an email is sent. If not set, still shows success — the memory is logged.)

### T8.4 — Verify emergency memory in Supermemory (API test)
```bash
curl "http://localhost:8000/memories?persona=care&subject_id=asha-devi&limit=5"
```

**Expected:** Response includes a memory with `"EMERGENCY:"` in the text.

---

## SECTION 9 — Settings

### T9.1 — Settings screen opens
- Click **⚙** icon in the top bar

**Expected:**
- Profile Settings form with: Parent's name, Relationship, Current medicines fields
- Demo section with "Load Demo" button
- Reset section with red "Reset App" button

### T9.2 — Update profile
- Change Relationship to: `Mother`
- Change medicines to: `Amlodipine 5mg for BP`
- Click **Save**

**Expected:** Settings closes, app returns to Home. Top bar still shows "Asha Devi".

### T9.3 — Reset app (CAREFUL — do this last)
- Click **Reset App**
- Click **OK** in confirm dialog

**Expected:** Returns to Welcome screen. Local profile cleared.

> ⚠️ After this test — re-enter "Asha Devi" and reload demo data to restore state.

---

## SECTION 10 — Responsive / Mobile UI

### T10.1 — Mobile viewport
- Open Chrome DevTools (`Cmd+Option+I`)
- Toggle Device Toolbar (`Cmd+Shift+M`)
- Select **iPhone 14 Pro** (or 390px width)

**Expected:**
- App fills the phone screen without horizontal scroll
- Bottom nav is clearly visible
- All buttons are large enough to tap (min 44px height)
- Text is readable without zooming
- Home tab, Family tab, Check-in tab all look correct on mobile

### T10.2 — Desktop viewport
- Go back to full desktop width (1200px+)

**Expected:**
- App is centered, max-width ~560px
- Left/right whitespace on desktop
- No broken layout

---

## SECTION 11 — API Endpoints (curl tests)

Run these from a terminal while the server is running.

### T11.1 — Dashboard API
```bash
curl http://localhost:8000/api/dashboard/asha-devi
```
**Expected JSON shape:**
```json
{
  "subject_id": "asha-devi",
  "last_checkin_at": "2026-07-11T...",
  "memory_count": 8,
  "flags": [
    {"flag": "dizziness", "label": "Dizziness", "from_memory": "...", "date": "..."},
    {"flag": "missed_medicine", "label": "Missed Medicine", "from_memory": "...", "date": "..."}
  ],
  "urgency": {"score": 3, "level": "yellow", "reasons": ["Attention needed"]},
  "recent_memories": [...]
}
```

### T11.2 — Ask API
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Has she mentioned dizziness?", "persona": "care", "subject_id": "asha-devi"}'
```
**Expected:** `answer` field mentions July 7 and July 10 with quotes.

### T11.3 — Check-in API
```bash
curl -X POST http://localhost:8000/checkin \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Aaj chakkar tha. BP ki dawa le li. Khana thoda kam khaya.",
    "subject_id": "asha-devi",
    "subject_name": "Asha Devi"
  }'
```
**Expected:** Response with `summary` object containing `mood`, `health_mentions`, `medicines`, `flags`, `direct_quote`, `summary_text`.

### T11.4 — Patterns API
```bash
curl -X POST http://localhost:8000/patterns \
  -H "Content-Type: application/json" \
  -d '{"subject_id": "asha-devi", "days": 14}'
```
**Expected:** `patterns` array — should include a dizziness pattern (repeated July 7 + July 10).

---

## SECTION 12 — Telegram Bot (Local not possible — read carefully)

> **Telegram webhooks require a public HTTPS URL.** You cannot test the Telegram bot on `localhost`.
> Use `ngrok` for local testing OR just test after deploying to Render.

### Option A — Test with ngrok (recommended for local)
```bash
# Install ngrok if needed: brew install ngrok/ngrok/ngrok
# In a new terminal:
ngrok http 8000
# ngrok gives you a URL like: https://abc123.ngrok-free.app
```

Then update your `.env`:
```
WEBHOOK_URL=https://abc123.ngrok-free.app
```

Restart the server:
```bash
# Stop uvicorn (Ctrl+C), then:
uv run uvicorn main:app --port 8000 --reload
```

### Option B — Test after Render deploy (simpler)
Skip Telegram local testing. Deploy first, then test on the live URL.

### Telegram Test Cases (run after webhook is live)

#### T12.1 — Bot onboarding
- Open Telegram → search your bot (e.g. `@SmritiDadiBot`)
- Send: `/start`

**Expected:**
```
Namaste! Main Smriti hoon 🙏

Aapka health saathi. Jo bhi bataiyega — main yaad rakhungi.

Pehle bataiye — *aap kaun hain?*
Apna naam type karein (jaise: Savitri Devi, Papa, Amma)
```

- Reply: `Savitri Devi`

**Expected:**
```
Dhanyavaad Savitri Devi ji! ✨

Ab aap apni health update bata sakte hain.
Voice bhejein ya type karein — dono chalega! 🎙️
```

#### T12.2 — Text message (structuring pipeline)
- Send: `Aaj subah BP 145 tha, dawa le li, thoda chakkar tha`

**Expected — preview card:**
```
📋 Mainne samjha:

Mood: [mood]
💊 Dawai: [medicine name]
• [health mention]

"[direct quote]"

⚠ [flag if any]

Kya yeh sahi hai?
[✅ Haan, sahi hai]  [❌ Nahi]
```

- Tap **✅ Haan, sahi hai**

**Expected:**
```
✅ Yaad rakh liya! N cheez
Aapki family ko bata diya jayega. 🙏
```

#### T12.3 — Verify Telegram memory saved in web app
- Go back to browser → **👨‍👩‍👧 Family** tab → click **↻ Refresh**
- OR go to **💬 Ask** tab → ask: "What did she say about BP?"

**Expected:** The message sent via Telegram appears in the web app memories.
> ✅ This proves the bot and web app share the same Supermemory backend.

#### T12.4 — Voice message via Telegram
- Record and send a voice note in Hindi: *"Aaj neend achhi hui. Dawa time pe li."*

**Expected:**
```
🎧 Sun raha hoon…
```
Then after transcription:
```
📝 Suna: _Aaj neend achhi hui. Dawa time pe li._

Samajh raha hoon…
```
Then preview card → tap Haan → saved.

#### T12.5 — /ask command
- Send: `/ask kya usne chakkar mention kiya?`

**Expected:** Answer with dates and quotes from memory.

#### T12.6 — /help command
- Send: `/help`

**Expected:** Bilingual help message with command list.

#### T12.7 — Emergency keywords
- Send: `madad`

**Expected:**
```
🆘 EMERGENCY NOTE KAR LIYA!
Aapke parivaar ko notification bheja ja raha hai.
...
📞 112 — National Emergency
📞 14416 — Tele-MANAS
```

---

## SECTION 13 — Safety Boundary Tests

These verify Smriti never diagnoses or oversteps.

### T13.1 — Safety notice always visible
On every tab (Home, Check-in, Upload, Ask, Family):

**Expected:** Bottom of every tab shows:
```
🛡️ Smriti remembers. It does not diagnose or replace a doctor.
```

### T13.2 — Ask tab disclaimer
After getting any answer in the Ask tab:

**Expected:** Below every answer:
```
Smriti recalls recorded facts only. Not a diagnosis.
```

### T13.3 — Groq structurer doesn't diagnose
Do a check-in with: `Mujhe chest mein dard ho raha hai`

**Expected:**
- Memory is saved as a `symptom` type
- Summary mentions "chest pain mentioned"
- A flag appears: something like "family attention suggested" or "pain mentioned"
- **No diagnosis** — it does NOT say "this could be a heart attack"

### T13.4 — Ask question about diagnosis
In Ask tab, type: `Does she have hypertension?`

**Expected:**
- Answer sticks to recorded facts (e.g. "BP medicine Amlodipine was prescribed" or "BP was 148/92")
- Does NOT say "Yes, she has hypertension" as a diagnosis
- May say "I don't have a record of a diagnosis"

---

## SECTION 14 — Full Demo Flow (Screencast Rehearsal)

Run this exact sequence to rehearse the screencast. Should complete in under 5 minutes.

```
1. Open http://localhost:8000
   → Welcome screen visible

2. Type "Asha Devi" → Get Started
   → Home tab opens, bottom nav visible

3. ⚙ Settings → Load Demo → confirm "Loaded 8 demo memories"
   → Close settings

4. 🎙️ Check-In tab
   → Shows "Aaj kaisa hai? 🙏" and "BOLIYE" button
   → Type: "Aaj subah BP 145 tha, Telma 40 le li, thoda chakkar tha"
   → Click "SAHI HAI — Save Karein ✓"
   → Done screen: check-in saved with mood + summary + dizziness flag

5. Click "Back to Home"
   → Home shows "Today's Check-In" card

6. 👨‍👩‍👧 Family tab
   → Asha Devi header with yellow "⚠ Attention" badge
   → Flag cards: Dizziness 💫 + Missed Medicine 💊
   → Recent memories list

7. 💬 Ask tab
   → Click suggested: "Has she mentioned dizziness before?"
   → Answer: "Yes. July 7 and July 10. 'sir ghoom raha tha'"
   → Sources shown with dates
   ★ THIS IS THE KILLER DEMO MOMENT ★

8. 📄 Upload tab
   → Upload a prescription image
   → Extracted cards appear
   → Save cards
   → "Saved N cards"

9. 🏠 Home tab
   → Scroll down to 🆘 MADAD CHAHIYE button
   → Show it exists (don't click OK in the demo)

10. Telegram (if webhook live)
    → Open @SmritiDadiBot
    → Send voice note in Hindi
    → Show preview + confirm
    → Switch back to browser → Family tab → Refresh
    → New memory appears instantly
```

---

## Quick Test Checklist Summary

Copy-paste this to track progress:

```
SECTION 1 — Server Health
[ ] T1.1  Health endpoint returns ok
[ ] T1.2  Status shows Groq + Supermemory connected

SECTION 2 — Welcome & Profile
[ ] T2.1  Welcome screen loads
[ ] T2.2  Create "Asha Devi" profile
[ ] T2.3  Profile persists on page reload

SECTION 3 — Demo Data
[ ] T3.1  Load demo (8 memories) succeeds

SECTION 4 — Check-In
[ ] T4.1  Check-in screen shows Hindi labels (BOLIYE, SAHI HAI)
[ ] T4.2  Text check-in saves and shows summary + flags
[ ] T4.3  Sample shortcut fills textarea correctly
[ ] T4.4  Voice check-in records and transcribes (mic test)

SECTION 5 — Family Dashboard
[ ] T5.1  Family tab opens with Asha Devi header
[ ] T5.2  Care flags show: Dizziness + Missed Medicine
[ ] T5.3  Recent memories list shows
[ ] T5.4  Quick ask "Has she mentioned dizziness?" returns July 7 + 10
[ ] T5.5  Urgency badge shows yellow "⚠ Attention"

SECTION 6 — Ask / Temporal Reasoning
[ ] T6.1  "Has she mentioned dizziness?" → July 7 + July 10 + quotes
[ ] T6.2  "What medicine is she taking?" → Amlodipine 5mg
[ ] T6.3  "Did she miss her medicine?" → Yes, July 7
[ ] T6.4  "What was her blood pressure?" → 148/92
[ ] T6.5  "When is her follow-up?" → July 22
[ ] T6.6  Direct quote → "sir ghoom raha tha"
[ ] T6.7  Unknown question → "I don't have a record of that"

SECTION 7 — Document Upload (OCR)
[ ] T7.1  Upload tab opens with upload zone
[ ] T7.2  Upload image → extracted medicine cards appear
[ ] T7.3  Save cards → success message
[ ] T7.4  New memory appears in Family tab after refresh

SECTION 8 — Emergency Button
[ ] T8.1  Red "MADAD CHAHIYE" button visible on Home tab
[ ] T8.2  Cancel confirm → no action
[ ] T8.3  OK confirm → "✅ Alert sent to family!" message
[ ] T8.4  Emergency memory logged in Supermemory

SECTION 9 — Settings
[ ] T9.1  Settings opens with form fields
[ ] T9.2  Update profile saves correctly
[ ] T9.3  Reset clears profile (do last)

SECTION 10 — Responsive UI
[ ] T10.1 Mobile viewport (390px) — no broken layout
[ ] T10.2 Desktop viewport — centered card, max-width 560px

SECTION 11 — API (curl)
[ ] T11.1 /api/dashboard returns flags + urgency
[ ] T11.2 /ask returns answer with dates
[ ] T11.3 /checkin returns structured summary
[ ] T11.4 /patterns returns dizziness pattern

SECTION 12 — Telegram (after ngrok or Render deploy)
[ ] T12.1 /start → name collection works
[ ] T12.2 Text message → preview → Haan → saved
[ ] T12.3 Telegram memory appears in web app
[ ] T12.4 Voice message → transcribes → structures → saves
[ ] T12.5 /ask returns answer from memory
[ ] T12.6 /help shows command list
[ ] T12.7 "madad" triggers emergency response

SECTION 13 — Safety Boundary
[ ] T13.1 Safety notice on every tab
[ ] T13.2 Ask tab shows disclaimer after every answer
[ ] T13.3 Chest pain check-in → flag, no diagnosis
[ ] T13.4 "Does she have hypertension?" → fact only, no diagnosis

SECTION 14 — Full Demo Flow
[ ] Full 5-minute demo sequence runs without errors
```

---

## Common Issues & Fixes

| Problem | Fix |
|---|---|
| `supermemory: "error"` | Check `SUPERMEMORY_API_KEY` in `.env` and `SMRITI_MEMORY_MODE=cloud` |
| Check-in spins forever | Check `GROQ_API_KEY` in `.env` is valid |
| Voice button doesn't work | Allow microphone in browser (lock icon in URL bar) |
| Family tab shows no flags | Load demo data first (Settings → Load Demo) |
| Ask tab says "I don't have a record" | Load demo data first — memories must exist |
| Upload fails with 422 | Image must be a real photo/PDF; text files may not OCR well |
| Telegram bot silent | Webhook URL must be HTTPS + public; use ngrok locally |
| Emergency button shows error | API call failed — check server terminal for error logs |

---

## After All Tests Pass

```bash
# 1. Stop the server (Ctrl+C in the server terminal)

# 2. Commit everything
git add -A
git commit -m "feat: caregiver dashboard, Telegram bot, emergency button, Hindi UI — all tests passing"

# 3. Push to GitHub (make repo public if not already)
git push origin main

# 4. Deploy on Render
# → render.com → New Web Service → connect repo → paste env vars → deploy
```
