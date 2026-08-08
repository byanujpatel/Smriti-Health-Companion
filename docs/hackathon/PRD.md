# PRD: Smriti Saathi

## 1. Product Summary

**Smriti Saathi** is a voice-first family care memory layer for ageing parents and their families.

It helps an ageing parent share daily updates naturally through voice, extracts important care context from conversations and documents, stores those memories over time, and gives family members a simple dashboard to understand what changed.

## 2. Hackathon Context

BestPossible.AI Hackathon rewards real, deployed, AI-driven apps with clear purpose, usable UI, responsive design, user login, real backend, open source repo, and positive impact with an India focus.

Smriti Saathi targets:

- Health and wellbeing
- Accessibility
- Elder care
- Family caregiving
- India-first multilingual usage

## 3. Core Problem

Ageing parents often under-report health issues, forget details, avoid worrying children, or struggle with apps. Families depend on scattered phone calls, WhatsApp messages, prescriptions, and memory.

This causes:

- Missed medicine details
- Forgotten symptoms or discomfort
- Lost doctor instructions
- Late discovery of changes
- Caregiver guilt for children living away
- Sibling coordination stress

## 4. Target Users

### Primary Payer

Adult child or family caregiver.

Examples:

- NRI son or daughter abroad
- Child living in another Indian city
- Busy caregiver coordinating with siblings
- Family member managing doctor visits and medicine reminders

### Primary End User

Ageing parent.

Needs:

- Voice-first flow
- Minimal typing
- Familiar language
- Dignity-first tone
- No scary medical wording
- Clear consent and trust

## 5. Product Thesis

Families do not need another medical app. They need a trusted memory layer that helps them notice what changed, without diagnosing or replacing doctors.

Smriti Saathi should report what was said, preserve exact quotes, connect memories across time, and gently surface repeated patterns.

## 6. MVP Scope

### Must Have

- Family login
- Parent profile
- Consent and safety screen
- Voice check-in flow
- Groq Whisper transcription
- Structured check-in summary
- Memory timeline
- Ask Smriti query box
- Temporal recall: “Has she mentioned X before?”
- Weekly noticed changes
- OCR document upload for prescriptions or reports
- Family dashboard
- Responsive mobile-first UI
- Deployment-ready open source repo

### Should Have

- Hindi + English UX copy
- Simple alert cards based on repeated mentions
- Document-to-memory cross-reference
- Demo seed data
- README mission section
- Hackathon screencast script

### Not In MVP

- Real phone calls through Twilio, Vapi, or Retell
- WhatsApp Business API integration
- Payments
- Voice emotion detection
- Medical diagnosis
- Treatment recommendations
- Insurance claim automation
- Hospital, insurer, or government dashboard
- Full multilingual coverage beyond Hindi/English demo

## 7. Existing Technical Edge

Current project already uses:

- Groq Whisper for speech-to-text
- Groq Llama vision/OCR for image/document understanding
- Groq GPT-OSS-120B for reasoning and summarization
- Supermemory for memory persistence and retrieval

This enables a low-cost multimodal care loop:

1. Parent speaks
2. Voice is transcribed
3. AI extracts structured care memory
4. Important facts are stored
5. Family asks temporal questions later
6. Documents can be linked to conversations

## 8. Core User Flows

### Flow A: Family Onboarding

1. Family member opens app
2. Signs in
3. Creates family space
4. Adds parent profile
5. Chooses language and relationship
6. Adds medicines and important context
7. Reviews consent and safety boundary
8. Lands on dashboard

### Flow B: Parent Check-In

1. Parent opens simple check-in page
2. Sees one large button: “Start Check-In”
3. Smriti asks warm questions
4. Parent answers by voice
5. App transcribes response
6. AI creates structured summary
7. Parent sees simple confirmation
8. Family dashboard updates

### Flow C: Document Upload

1. Family uploads prescription, lab report, bill, or medicine photo
2. OCR extracts readable text
3. AI structures key fields
4. Uncertain fields are marked clearly
5. Document is stored in parent memory
6. Related medicines and dates become searchable

### Flow D: Family Dashboard

1. Family opens dashboard
2. Sees today’s status
3. Reads latest check-in summary
4. Views care flags
5. Opens memory timeline
6. Asks Smriti a question
7. Gets evidence-based answer with dates and quotes

### Flow E: Temporal Reasoning

User asks:

> Has Mom mentioned dizziness before?

Smriti answers:

- Yes/no based on memory
- Chronological dates
- Exact quotes
- Related context
- Safety boundary
- Suggested family follow-up without diagnosis

## 9. AI Behaviors

### Voice Check-In Conductor

Rules:

- Warm, relative-like tone
- Use simple Hindi/English
- Avoid clinical language
- Ask one question at a time
- Let parent go off-topic
- End with: “Is there anything else you want your family to know?”

### Structured Summary Extractor

Every check-in produces:

- Overall mood
- Medicines
- Health mentions
- Daily wellbeing
- Direct quote
- Source transcript
- Date and time

### Temporal Pattern Detector

Runs on last 7-14 days of summaries.

Finds:

- Same symptom mentioned 2+ times
- Missed medicine repeated
- Mood shift from usual baseline
- Eating or sleeping change
- Fewer activities or social mentions
- Medicine mention near symptom mention

Language:

- “We noticed…”
- “Here is what was said…”
- “You decide if it matters.”
- Never “detected disease” or “medical risk.”

### Ask Smriti Handler

Handles emotional caregiver questions.

Example:

> Is Mom okay?

Response should:

- Summarize recent wellbeing
- Mention notable changes
- Preserve reassurance when supported
- Show exact dates and quotes
- Avoid diagnosis
- Offer next family action

## 10. Safety and Compliance Boundary

Permanent product language:

> Smriti remembers and organizes. It does not diagnose, prescribe, or replace a doctor.

Rules:

- Never diagnose
- Never prescribe
- Never recommend treatment
- Never infer disease from symptoms
- Never say a parent is safe or unsafe
- Always cite memory or document source
- Mark OCR uncertainty instead of guessing
- Use “family attention suggested” instead of “medical alert”

## 11. Data Model Guidance

### Parent Profile

- Parent ID
- Name
- Preferred language
- City
- Relationship
- Medicines
- Important context
- Consent status
- Family members

### Check-In Memory

- Check-in ID
- Parent ID
- Date/time
- Raw transcript
- Language
- Mood summary
- Medicines taken/missed/unclear
- Health mentions with exact quotes
- Food/sleep/activity/social notes
- Direct quote
- Flags
- Stored memory ID

### Document Memory

- Document ID
- Parent ID
- Type
- Uploaded date
- OCR text
- Extracted medicines
- Doctor name
- Dates
- Instructions
- Uncertain fields
- Stored memory ID

### Temporal Insight

- Insight ID
- Parent ID
- Date range
- Pattern type
- Evidence dates
- Evidence quotes
- User-facing summary
- Safety disclaimer

## 12. Success Criteria

By submission, the product should demonstrate:

- Login works
- Parent profile persists
- Voice check-in creates memory
- OCR document upload creates memory
- Dashboard shows latest care state
- Ask Smriti answers temporal question
- Weekly noticed changes works on demo data
- UI works on phone and laptop
- Safety boundary is visible
- App is deployed
- Repo is public and documented

## 13. Demo Script

1. Son logs in from another city/country
2. Adds mother profile: Asha Devi, Hindi, BP medicine
3. Uploads prescription photo
4. OCR extracts medicine and follow-up date
5. Mother completes Hindi voice check-in
6. She says she felt dizzy and missed BP medicine
7. Smriti summarizes and stores memory
8. Dashboard shows “dizziness + missed medicine mentioned”
9. Son asks: “Has she mentioned dizziness before?”
10. Smriti shows previous dated quote
11. Safety banner remains visible
12. Pitch ends with: “Smriti helps families remember what ageing parents forget to mention.”
