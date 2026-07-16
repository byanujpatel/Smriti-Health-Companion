# Smriti Architecture

Smriti is one FastAPI app that serves both the browser UI and the API. Memory can
run locally with Supermemory Local or in deployment with Supermemory Cloud. Groq
handles AI text, voice transcription, summaries, and report/photo reading.

## Big Picture

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

## Person Model

```text
Person in UI
  id: grandad
  name: Grandad
  persona: care

Saved Memory
  persona: care
  subject_id: grandad
  subject_name: Grandad
  type: vital
  text: Blood pressure was 150 over 95.
```

`persona` is still useful as the broad container:

- `care`: family and caregiving memories
- `self`: your own memories

`subject_id` is the exact person inside that container:

- `papa`
- `mummy`
- `myself`
- `grandad`
- any custom person added in the sidebar

## Local vs Deployed

```text
Local testing
  Browser -> FastAPI -> Supermemory Local
                    -> Groq

Deployment
  Browser -> Render/FastAPI -> Supermemory Cloud
                         -> Groq
```

Only the memory backend changes between local and cloud. The app code and UI stay
the same.
