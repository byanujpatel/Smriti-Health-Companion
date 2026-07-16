# Smriti

Smriti is a family health memory app. You can speak or type health notes, review
what will be saved, and later ask questions by person.

- Demo: `PASTE_DEMO_LINK_HERE`
- Loom: `PASTE_LOOM_LINK_HERE`

## What It Does

- Saves health memories only after preview and confirmation.
- Supports voice input with Groq STT.
- Uploads reports or prescriptions as PDF/photo and extracts editable memory cards.
- Lets you add any person: Papa, Mummy, Grandad, Mother, Wife, Rahul, Myself, etc.
- Keeps each person's memories separate with `subject_id` and `subject_name`.
- Answers from saved memories with source cards and retrieval debug.
- Generates visit summaries from recorded facts.
- Runs with Supermemory Local for local testing or Supermemory Cloud for deployment.

## Architecture

```text
User
  |
  v
Browser UI
  - Person picker: Papa, Mummy, Myself, custom relatives
  - Remember, Ask, Timeline, Summary
  |
  v
FastAPI App
  - Preview before save
  - Adds subject_id + subject_name
  - Date filters
  - Retrieval guardrails
  |
  +--------------------+
  |                    |
  v                    v
Groq AI             Supermemory
- structure text    - local mode: localhost:6767
- voice STT         - cloud mode: Supermemory Cloud
- report vision     - stores memory + metadata
- answers/summary   - searches by persona + subject_id
```

## Memory Flow

```text
1. Select person
   Example: Grandad

2. Add note
   "Grandad had BP 150 over 95 today"

3. Preview
   Groq turns the note into editable memory cards.

4. Confirm save
   Smriti saves:
   - text
   - type
   - occurred_at
   - persona: care/self
   - subject_id: grandad
   - subject_name: Grandad

5. Ask later
   Smriti searches only the selected person's memories.
```

## Local Setup

Create `.env`:

```env
SMRITI_MEMORY_MODE=local
SUPERMEMORY_BASE_URL=http://localhost:6767
SUPERMEMORY_API_KEY=your-local-supermemory-key

GROQ_API_KEY=your-groq-key
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_STT_MODEL=whisper-large-v3-turbo
GROQ_VISION_MODEL=meta-llama/llama-4-scout-17b-16e-instruct
```

Start Supermemory Local:

```bash
supermemory-server
```

Start Smriti:

```bash
UV_CACHE_DIR=/private/tmp/uv-cache uv run uvicorn main:app --reload --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

## Quick Test

1. Click `Refresh`.
2. Click `Test memory`.
3. Add a person like `Grandad`.
4. Save: `Grandad had BP 150 over 95 today`.
5. Switch to `Papa` and ask about BP. It should not show Grandad.
6. Switch back to `Grandad` and ask again. It should show the memory.

## Cloud Deploy

Use Supermemory Cloud in production:

```env
SMRITI_MEMORY_MODE=cloud
SUPERMEMORY_API_KEY=your-supermemory-cloud-api-key

GROQ_API_KEY=your-groq-key
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_STT_MODEL=whisper-large-v3-turbo
GROQ_VISION_MODEL=meta-llama/llama-4-scout-17b-16e-instruct
```

On Render:

1. Push this repo to GitHub.
2. Create a Render Web Service.
3. Use Docker or the included `render.yaml`.
4. Add the environment variables in Render.
5. Deploy.
6. Open the Render URL and click `Test memory`.

Do not commit `.env`.

## Code Layout

```text
main.py                    FastAPI routes and frontend serving
smriti/models.py           API schemas and memory models
smriti/clients/            Groq and Supermemory clients
smriti/services/           retrieval, duplicate checks, upload processing
smriti/retrieval.py        local retrieval scoring guardrails
frontend/index.html        browser entrypoint
frontend/src/app.js        React UI
frontend/src/voice.js      microphone recording
frontend/src/styles.css    UI styling
docs/architecture.md       standalone architecture notes
```

## Tests

```bash
UV_CACHE_DIR=/private/tmp/uv-cache uv run pytest -q
```

## Safety

Smriti recalls recorded facts. It does not diagnose, recommend medication doses,
interpret lab values, or make urgency judgments.
