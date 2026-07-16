# Smriti Health Companion

Local-first health memory companion. Phase 1 supports typed health logs,
editable previews, confirmed saving to Supermemory Local, and dated recall.
Phase 2 adds persona-safe recall, optional date windows, and a small browser UI.
Phase 3 adds a cleaner single-page frontend for day-to-day testing.
Phase 4 adds React UI, memory history, edit/delete, better date controls, and
service status checks.
Phase 5A adds threshold-based retrieval fallback with visible debug scoring.
Phase 5B adds deterministic query rewrite, stronger health/Hinglish synonyms,
and warnings when date filters hide likely matches.
Phase 6 adds doctor visit summaries from recorded memories.
Phase 7A adds Groq STT voice input for low-friction memory logging.
Phase 8 adds retrieval evaluation, safer dynamic matching, memory quality
signals, duplicate skipping, and one-click demo data.
Phase 9 splits the frontend into a deployable React static app served by
FastAPI, with a public-ready responsive UI. Phase 10 adds local/cloud
Supermemory modes, deployment checks, and report/prescription upload previews.
Phase 12 adds person-scoped household memory with Papa, Mummy, Myself, and any
custom person/relative you add in the sidebar.

## Run

1. Start Supermemory from this project folder so it uses this folder's
   `.supermemory` database:

```bash
cd /Users/anujpatel/Documents/Memory/supermemory-hackathon-local
supermemory-server
```

2. Copy `.env.example` to `.env` and add your credentials.
3. Start the API:

```bash
UV_CACHE_DIR=/private/tmp/uv-cache uv run uvicorn main:app --reload
```

Open the browser UI at [http://127.0.0.1:8000](http://127.0.0.1:8000).

You can also open [the interactive API](http://127.0.0.1:8000/docs).

## Test Flow

1. Select `Papa`, `Mummy`, `Myself`, or add a custom person in the sidebar.
2. Add a log, for example: `Doctor said Papa should reduce salt from today.`
2. Click `Preview`.
3. Edit the card if needed, then click `Save selected`.
4. Wait 2-5 seconds.
5. Ask: `What did the doctor say about salt?`
6. Optional: use `Today`, `Yesterday`, `Last 7 days`, or custom dates to test
   date-limited recall.

## Frontend Features

- Real React frontend lives in `frontend/` and is served by FastAPI.
- Person picker with defaults for `Papa`, `Mummy`, `Myself`, plus `+ Add person`
  for relatives like Grandad, Mother, Wife, Rahul, etc.
- Add memory with better date-time input.
- Preview cards with editable text, type, and occurred-at date.
- Confirmed save only after preview.
- Ask with quick date filters and source cards.
- Memory history list for the selected persona.
- Edit or delete saved memories.
- Status panel for API, Supermemory, and Groq configuration.
- Retrieval debug panel showing Supermemory hits, history fallback hits, scores,
  thresholds, and accepted/maybe/rejected candidates.
- Rewritten search query display.
- Outside-date match warning when relevant memories exist outside the selected
  date range.
- Visit summary panel with date range, source memories, and copy support.
- Voice recording for Health Log input using Groq STT. Transcript fills the text
  box, then the normal preview and confirm flow continues.
- One-click demo mode loads sample care memories and prefilled retrieval checks.
- Person-scoped memories store `subject_id` and `subject_name`; custom people
  are saved in browser localStorage and every confirmed memory stores the
  selected person. Old Care memories default to Papa so existing local data
  still appears.

## Code Layout

- `main.py`: FastAPI app, route wiring, static frontend serving.
- `smriti/models.py`: shared API request/response schemas.
- `smriti/clients/`: external service clients for Groq and Supermemory.
- `smriti/services/`: backend business logic for retrieval, demo data, memory
  quality, and duplicate-safe saves.
- `smriti/retrieval.py`: deterministic local retrieval guardrails.
- `frontend/`: deployable React frontend served at `/`.
- `frontend/src/api.js`: browser API client.
- `frontend/src/app.js`: app screens and interaction state.
- `frontend/src/voice.js`: voice recording/transcription UI.
- `frontend/src/time.js`: date/time helpers.
- `frontend/src/styles.css`: responsive visual system.

## Deploy

This repo can deploy as one FastAPI service that serves both API and frontend.
For Render, use the included `Dockerfile` or `render.yaml` blueprint. You do not
need separate frontend hosting because FastAPI serves `frontend/` at `/`.

Required runtime services:

- Supermemory Local or Supermemory Cloud.
- Groq API key and model credentials for text, voice STT, and report/photo
  vision.

Required environment:

```env
SMRITI_MEMORY_MODE=local
SUPERMEMORY_BASE_URL=http://localhost:6767
SUPERMEMORY_API_KEY=your-local-supermemory-key
GROQ_API_KEY=...
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_STT_MODEL=whisper-large-v3-turbo
GROQ_VISION_MODEL=meta-llama/llama-4-scout-17b-16e-instruct
```

For Supermemory Cloud deployment, paste your cloud key here:

```env
SMRITI_MEMORY_MODE=cloud
SUPERMEMORY_API_KEY=your-supermemory-cloud-api-key
GROQ_API_KEY=your-groq-key
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_STT_MODEL=whisper-large-v3-turbo
GROQ_VISION_MODEL=meta-llama/llama-4-scout-17b-16e-instruct
```

In cloud mode you usually do not need `SUPERMEMORY_BASE_URL`; the SDK uses
Supermemory Cloud by default. If an old localhost `SUPERMEMORY_BASE_URL` is
still present, Smriti ignores it in cloud mode. Keep `SUPERMEMORY_BASE_URL` only
if Supermemory gives you a custom hosted endpoint.

Local mode means only the memory database runs locally. Groq is still used for
text structuring, voice transcription, answers, summaries, and report/photo
vision.

Render environment variables:

```env
SMRITI_MEMORY_MODE=cloud
SUPERMEMORY_API_KEY=your-supermemory-cloud-api-key
GROQ_API_KEY=your-groq-key
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_STT_MODEL=whisper-large-v3-turbo
GROQ_VISION_MODEL=meta-llama/llama-4-scout-17b-16e-instruct
```

Do not add `.env` to Render or GitHub. Add the values in Render:

```text
Render Dashboard -> your service -> Environment -> Add Environment Variables
```

Deploy checklist:

1. Rotate any keys that were pasted into chats or screenshots.
2. Confirm `.env` is local only and not committed.
3. Push the repo to GitHub.
4. Create a Render Web Service from the repo.
5. Choose Docker runtime, or use the included `render.yaml` blueprint.
6. Add the environment variables above in Render.
7. Deploy and open the Render URL.
8. Click `Refresh`, then `Test memory`.
9. Confirm `Save: ok`, `Search: ok`, and `Cleanup: ok`.

After switching modes, open the app status card and click `Test memory`. It
runs a safe save → search → delete check against the selected memory target, so
you can verify local or cloud mode before trusting a deployment.

Quick local smoke test:

```bash
supermemory-server
```

```bash
UV_CACHE_DIR=/private/tmp/uv-cache uv run uvicorn main:app --reload --port 8000
```

Open `http://127.0.0.1:8000`, click `Refresh`, then `Test memory`. Add a Papa
memory, save it, switch to Mummy, and confirm Papa's memory does not appear.

Add any person:

1. In the sidebar, type a name in `Add anyone...`.
2. Choose `Care` for family/relative, or `Self` for yourself.
3. Click `+ Add person`.
4. Save memories as that person; Ask, Timeline, and Summary will filter to that
   person.

See [Architecture](docs/architecture.md) for the simple system diagram.

Report and prescription uploads:

- Click `Upload report` in the Remember tab.
- Supports PDF, JPG, PNG, and WEBP.
- Digital PDFs use `pypdf` text extraction.
- Photos and scanned PDFs use Groq Vision.
- Smriti creates editable preview cards; nothing saves until you click
  `Save selected`.

Docker:

```bash
docker build -t smriti .
docker run --env-file .env -p 8000:8000 smriti
```

Non-Docker:

```bash
uv sync
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

## Voice Input

Use `Speak memory` in the Add Memory panel, speak a short health log, then stop
the recording. The transcript replaces the memory text box. Review it, click
`Preview`, edit if needed, then `Save selected`.

Voice input requires:

```env
GROQ_STT_MODEL=whisper-large-v3-turbo
```

The browser must allow microphone access. Voice logs are never auto-saved.

## Retrieval Tuning

The Ask panel uses Supermemory's dynamic search controls plus a local confidence
gate:

- `Supermemory threshold`: passed directly to Supermemory search. Lower means
  broader retrieval; higher means fewer, more similar results.
- `Search limit`: passed directly to Supermemory and history fallback.
- `Rerank`: passed directly to Supermemory for better relevance.
- `Local accept threshold`: memories at or above this score are used for the
  answer.
- `Local maybe threshold`: memories below accept but above maybe are shown as possible
  matches, but not used for the answer.

Default values are `0.30` Supermemory threshold, `50` limit, rerank on, `0.45`
local accept, and `0.30` local maybe. Lower Supermemory threshold if the app is
missing relevant memories. Raise local accept if answers feel too loose.

Smriti rewrites short health questions with a deterministic synonym map before
searching Supermemory. Examples: `pressure` expands toward `BP/blood pressure`,
`namak` toward `salt/sodium`, `neend` toward `sleep`, and `saans` toward
`breathlessness/breathing`.

## Visit Summary

Use the `Visit Summary` panel after saving memories. Pick a date range and click
`Generate Summary`. The summary is limited to recorded facts and includes source
memories. It must not diagnose, interpret values, recommend medication changes,
or make urgency judgments.

Example API preview request:

```json
{
  "text": "Papa ko kal raat neend nahi aayi",
  "persona": "care",
  "current_datetime": "2026-07-11T12:00:00+05:30"
}
```

Example API ask request with a date window:

```json
{
  "question": "What did the doctor say about salt?",
  "persona": "care",
  "from_date": "2026-07-11",
  "to_date": "2026-07-11"
}
```

Care and Self memories use separate Supermemory containers. The API also
applies a redundant persona metadata check and filters by date before sending
memories to the LLM. Smriti recalls recorded facts but does not diagnose,
recommend doses, or provide medical advice.

## Tests

```bash
UV_CACHE_DIR=/private/tmp/uv-cache uv run pytest -q
```
