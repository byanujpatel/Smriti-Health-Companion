# Supermemory Local: Phase 0 findings

Research date: 2026-07-11. Sources are Supermemory's official documentation plus the generated OpenAPI types in the installed Python SDK (`supermemory==3.50.0`).

## Decisions for Phase 1

### 1. Persona isolation

Use a distinct `container_tag` as the primary hard boundary:

- Care: `smriti_care`
- Self: `smriti_self`

Supermemory describes container tags as isolated spaces, scoped to a user/project. The v4 search API takes one `containerTag` string. This is safer and simpler than putting both personas in one container and relying only on metadata.

Still attach `persona` metadata for inspection and defense in depth:

```python
client.add(
    content="Papa had trouble sleeping last night.",
    container_tag="smriti_care",
    metadata={
        "persona": "care",
        "occurred_at": "2026-07-10T22:00:00+05:30",
        "occurred_at_epoch": 1783701000,
    },
)
```

The exact Python search syntax for a metadata equality filter is:

```python
results = client.search.memories(
    q="sleep problems",
    container_tag="smriti_care",
    search_mode="hybrid",
    limit=20,
    filters={
        "AND": [
            {"key": "persona", "value": "care"},
        ]
    },
)
```

Although the SDK's generated Python type internally names the field `and_`, its request transformer accepts API-shaped dictionaries, and the official examples use uppercase `AND`. Keep this behind `MemoryClient` so it can be verified once against Local.

Sources: [Organizing and filtering](https://supermemory.ai/docs/concepts/filtering), [Search](https://supermemory.ai/docs/search), [Search API](https://supermemory.ai/docs/api-reference/recall-search/search-memory-entries).

### 2. Date-range retrieval

Supermemory supports numeric metadata comparisons with `>`, `<`, `>=`, `<=`, and `=`. Its official example represents time as a Unix timestamp. Store both:

- `occurred_at`: ISO 8601 string, used for display/citations.
- `occurred_at_epoch`: Unix seconds as a number, used for filtering.

Exact Python request shape for an inclusive range:

```python
results = client.search.memories(
    q="health events",
    container_tag="smriti_care",
    search_mode="hybrid",
    limit=100,
    filters={
        "AND": [
            {"key": "persona", "value": "care"},
            {
                "filter_type": "numeric",
                "key": "occurred_at_epoch",
                "value": str(start_epoch),
                "numeric_operator": ">=",
            },
            {
                "filter_type": "numeric",
                "key": "occurred_at_epoch",
                "value": str(end_epoch),
                "numeric_operator": "<=",
            },
        ]
    },
)
```

The SDK serializes snake_case fields such as `filter_type` and `numeric_operator` to `filterType` and `numericOperator`. The filter `value` is typed as a string even for numeric comparisons, hence `str(epoch)`.

Important Phase 1 limitation: search remains semantic and requires a non-empty `q`; it is not a guaranteed exhaustive database listing. Date filtering is appropriate for summary retrieval, but we should test Local explicitly. For exact/exhaustive summaries later, consider the document-list endpoint or maintain an application index if Local's semantic search omits low-relevance items.

Sources: [Organizing and filtering](https://supermemory.ai/docs/concepts/filtering), [Search API](https://supermemory.ai/docs/api-reference/recall-search/search-memory-entries), [Document operations](https://supermemory.ai/docs/document-operations).

### 3. Docker requirement

Self-hosted Supermemory is officially distributed as a Docker-hosted stack. However, once `supermemory-server` is already reachable at `http://localhost:6767`, the Smriti application only needs the HTTP endpoint; it does not need to run Docker commands or include Docker in Phase 1 application code.

Docker is therefore an infrastructure concern for starting/persisting the local Supermemory service, not an additional runtime dependency of the FastAPI application. Keep the backend configurable with `SUPERMEMORY_BASE_URL=http://localhost:6767`.

Source: [Supermemory changelog: self-hostable stack](https://supermemory.ai/docs/changelog/overview).

### 4. Supermemory key vs Groq key

These are separate credentials:

- `SUPERMEMORY_API_KEY`: authenticates the Supermemory SDK/API. With `base_url=http://localhost:6767`, it is sent to the local Supermemory server. Whether Local validates it depends on that server's auth configuration; the Python SDK constructor still requires a non-empty key.
- `GROQ_API_KEY`: authenticates requests to Groq and pays/limits LLM usage. It is used by the Groq client for structuring and answering, never as the Supermemory SDK key.

Recommended configuration:

```text
SUPERMEMORY_BASE_URL=http://localhost:6767
SUPERMEMORY_API_KEY=<local server/API credential>
GROQ_API_KEY=<Groq credential>
GROQ_MODEL=llama-3.3-70b-versatile
```

Never commit either key. Load them from environment variables. The distinction between a memory-provider key and an LLM-provider key is also explicit in Supermemory's Memory Router prerequisites.

Sources: [Supermemory quickstart](https://supermemory.ai/docs/quickstart), [Memory Router usage](https://supermemory.ai/docs/memory-router/usage).

## Phase 0 verification gate

Before implementing `/ingest/preview`, run an automated add/search check against Local that proves all four behaviors:

1. Add a Care record and a Self record with the same searchable phrase.
2. Searching `smriti_care` returns Care only; searching `smriti_self` returns Self only.
3. A redundant `persona` metadata filter succeeds.
4. An `occurred_at_epoch` range includes the in-range record and excludes the out-of-range record.

If metadata filters fail in Local while container tags work, retain container tags as the Phase 1 isolation boundary and post-filter returned metadata temporarily. Do not allow an unfiltered cross-persona fallback.
