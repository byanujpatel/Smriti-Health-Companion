# In Progress Tracker

## Current Goal

Win BestPossible.AI Hackathon (Gold or Silver) by Aug 10, 2026.
Ship a deployed, open-source, AI-driven elder-care memory product that scores 3/3 on the judge's signals:
1. **AI workflow you can show** — Groq Whisper + Llama + Supermemory pipeline, shown explicitly in screencast
2. **Project someone can actually use** — Render deployed, live URL, real auth (Supabase), public repo
3. **Social/impact angle** — Ageing parents in India who can't type. Children in other cities who worry.

## Status Legend

- `[ ]` Not started
- `[~]` In progress
- `[x]` Done
- `[!]` Blocked or needs decision

---

## ✅ PHASE 1-8: MVP (DONE)

All original Smriti Saathi features are complete:

- [x] Parent profile + onboarding
- [x] Voice check-in → Groq Whisper → structured summary
- [x] OCR document upload → Groq Vision → medicine extraction
- [x] Temporal reasoning ("Has she mentioned X?") → Supermemory search
- [x] Weekly noticed changes → pattern detection
- [x] Memory timeline dashboard
- [x] Senior-friendly UI (large buttons, bilingual prompts, 44px+ targets)
- [x] Safety banner on every screen
- [x] Demo data — Asha Devi, 9 memories, dizziness pattern, Amlodipine prescription
- [x] Mobile-first responsive layout

---

## 🔴 PHASE 9: DEPLOY + AUTH (Aug 6 — TODAY, CRITICAL)

**This unblocks everything. Do this before any new features.**

- [ ] `git push` → Render deploy — verify live URL returns HTML
- [ ] Set all env vars in Render dashboard (GROQ_API_KEY, SUPERMEMORY_API_KEY, etc.)
- [ ] Verify `/health` → `{"status": "ok"}` on live URL
- [ ] Test voice check-in end-to-end on live URL
- [ ] Test OCR upload on live URL
- [ ] Test "Ask" temporal query on live URL
- [ ] Add Supabase Auth (replace localStorage) — 2 hours
  - [ ] Create Supabase project (free tier, 5 min)
  - [ ] Add supabase-js to frontend/src/vendor/ or CDN import
  - [ ] Replace `loadProfile/saveProfile` in app.js with Supabase sign-in/sign-up
  - [ ] User ID from Supabase auth → used as subject_id prefix
  - [ ] Login screen: email + password, Sign Up / Sign In
- [ ] Update README with live URL
- [ ] Make GitHub repo public

---

## 🟡 PHASE 10: CAREGIVER DASHBOARD (Aug 7 — HIGH PRIORITY)

**Most visually impressive addition. Uses existing backend data.**

- [ ] Add `GET /api/dashboard/{subject_id}` endpoint in main.py
  - Returns: last_checkin, active_flags, recent_memories (last 7 days), urgency_level
  - All data comes from existing `retrieve_memories()` calls
- [ ] Add CaregiverDashboard view in app.js
  - Family member card (name, last seen, latest BP/mood)
  - Active care flags with colors (yellow/orange/red)
  - Memory timeline filtered by person
  - "Ask Smriti" section
- [ ] Style caregiver view in styles.css (desktop-friendly, wider layout)
- [ ] Add urgency scoring after every check-in
  - Simple rule-based: dizziness/pain/missed medicine → yellow; emergency → red
  - Show urgency badge on caregiver dashboard

---

## 🟡 PHASE 11: TELEGRAM BOT MVP (Aug 7-8 — HIGH IMPACT)

**Closes the "real usage" and "social/impact" story. Meets elderly users where they are.**
**Build MVP ONLY. No reminders, no Twilio, no complex flows.**

- [ ] Register @SmritiDadiBot with @BotFather → get TELEGRAM_BOT_TOKEN
- [ ] Add `python-telegram-bot` to requirements.txt
- [ ] Create `telegram_bot.py` — 4 core handlers only:
  - [ ] `/start` → ask for name → create elder profile
  - [ ] Voice message → Groq Whisper → structure → preview → [Haan/Nahi] → save to Supermemory
  - [ ] Text message → same structuring pipeline (fallback)
  - [ ] `/ask {question}` → retrieve_memories → Groq answer → reply
- [ ] Add `POST /telegram` webhook endpoint in main.py
- [ ] Set TELEGRAM_BOT_TOKEN + WEBHOOK_URL in Render env vars
- [ ] Set webhook: `curl -F "url=https://YOUR-URL/telegram" https://api.telegram.org/bot<TOKEN>/setWebhook`
- [ ] Test: send voice note in Hindi → verify memory saved in Supermemory
- [ ] Test: `/ask` query → verify answer comes back with dates + quotes

---

## 🟢 PHASE 12: POLISH + EMERGENCY (Aug 8 — MEDIUM PRIORITY)

**Nice-to-have additions. Only if Phase 9-11 are solid.**

- [ ] Emergency button on elder home screen ("MADAD CHAHIYE")
  - On click: log memory with type="emergency", urgency_score=5
  - Send email to caregiver using Python smtplib (no Twilio needed)
  - Show confirmation: "Alert sent to family"
- [ ] Hindi button labels on elder check-in screen
  - "BOLIYE" (Tap to Speak)
  - "SAHI HAI ✓" (Confirm)
  - "DOBARA" (Redo)
- [ ] Add `POST /api/emergency` endpoint in main.py
- [ ] Add ALERT_EMAIL + SMTP env vars

---

## 🎬 PHASE 13: SCREENCAST + SUBMISSION (Aug 9-10)

- [ ] Write final screencast script (based on 3-signal structure below)
- [ ] Record 4-5 minute screencast (Loom or OBS)
  - 0:00-0:20 Personal problem hook
  - 0:20-0:55 Telegram bot demo (Dadi's phone)
  - 0:55-1:30 Caregiver dashboard (Beti's laptop)
  - 1:30-2:00 **AI WORKFLOW SHOWN EXPLICITLY** (tools, order, prompts)
  - 2:00-2:30 Temporal reasoning killer moment
  - 2:30-3:00 Document OCR
  - 3:00-3:30 Architecture + tool choices explained
  - 3:30-4:00 Impact close
- [ ] Submit early on Aug 10 (earlier = more feedback)
- [ ] Submit: product URL + repo URL + build summary
- [ ] Post build-in-public Discord update

---

## 🎯 3-Signal Readiness Tracker

| Signal | Target | Status |
|---|---|---|
| AI workflow you can show | Groq Whisper→Llama→Supermemory pipeline with prompts shown | ⚠️ Not shown explicitly yet in screencast |
| Project someone can use | Deployed live URL + real auth | ❌ Not deployed |
| Social/impact angle | "Dadi in Varanasi / Beti in Mumbai" story | ✅ Strong |

---

## What Remains (Strict Priority Order)

1. **DEPLOY** ← do right now, blocks everything
2. **Supabase auth** ← 2 hours, unblocks Silver eligibility
3. **Caregiver dashboard** ← 3-4 hours, huge visual impact
4. **Telegram bot MVP** ← 4-5 hours, closes impact story
5. **Screencast** ← record on Aug 9
6. **Submit** ← Aug 10 morning

---

## Risk Register

| Risk | Impact | Status | Mitigation |
|---|---|---|---|
| Render deploy fails | Critical | ⚠️ Active | Have Dockerfile + Procfile ready, check build logs |
| Supabase auth breaks existing flows | High | Mitigated | Keep subject_id logic unchanged, just prefix with user.id |
| Telegram bot voice STT fails under load | Medium | Mitigated | Text fallback always works, demo with pre-recorded voice |
| Voice recording unreliable in browser | High | ✅ Mitigated | Text fallback textarea always visible |
| OCR misreads medicine | Medium | ✅ Mitigated | Uncertain fields flagged, not guessed |
| LLM oversteps medical advice | High | ✅ Mitigated | SAFETY_RULES in every prompt, permanent UI disclaimer |
| Demo crashes live | High | Mitigated | Use seeded Asha Devi demo data, not live recording |
