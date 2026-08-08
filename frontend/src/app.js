import { createRoot } from "react-dom/client";
import { VoiceButton } from "./voice.js";
import { api, friendlyError } from "./api.js";

const h = React.createElement;
const { useState, useEffect, useRef } = React;

const PROFILE_KEY = "smriti.profile.v2";

// ── Persistence ───────────────────────────────────────────────────────────────

function loadProfile() {
  try { return JSON.parse(localStorage.getItem(PROFILE_KEY) || "null"); }
  catch { return null; }
}
function saveProfile(p) { localStorage.setItem(PROFILE_KEY, JSON.stringify(p)); }

function slugify(name) {
  return name.toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9-]/g, "").slice(0, 40) || "parent";
}

function nowIso() { return new Date().toISOString().slice(0, 16); }

function fmtDate(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
}
function fmtTime(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
}
function fmtDateTime(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short" }) +
    " at " + new Date(iso).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
}
function moodEmoji(mood) {
  const m = (mood || "").toLowerCase();
  if (m.includes("cheer") || m.includes("happy") || m.includes("good") || m.includes("well")) return "😊";
  if (m.includes("tired") || m.includes("low") || m.includes("sad")) return "😔";
  if (m.includes("pain") || m.includes("unwell") || m.includes("sick")) return "😟";
  return "🙂";
}
function groupByDate(memories) {
  const g = {};
  for (const m of memories) {
    const k = fmtDate(m.occurred_at);
    if (!g[k]) g[k] = [];
    g[k].push(m);
  }
  return g;
}
function typeColor(t) {
  return { symptom: "pill-red", medication: "pill-green", vital: "pill-yellow", visit: "pill-blue", document: "pill-gray", remark: "pill-gray" }[t] || "pill-gray";
}

// ── Safety notice (always visible) ───────────────────────────────────────────

function SafetyNotice() {
  return h("p", { className: "safety-notice" },
    "🛡️ Smriti remembers. It does not diagnose or replace a doctor."
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// SCREEN 1 — Welcome (just the parent's name)
// ─────────────────────────────────────────────────────────────────────────────

function WelcomeScreen({ onStart }) {
  const [name, setName] = useState("");

  function go(e) {
    e.preventDefault();
    const n = name.trim();
    if (!n) return;
    const profile = { id: slugify(n), name: n, createdAt: new Date().toISOString() };
    saveProfile(profile);
    onStart(profile);
  }

  return h("div", { className: "welcome-screen" },
    h("div", { className: "welcome-card" },
      h("div", { className: "brand-mark large" }, "स"),
      h("h2", null, "Smriti Saathi"),
      h("p", { className: "welcome-sub" }, "Family care memory for your parents"),
      h("form", { onSubmit: go, className: "welcome-form" },
        h("input", {
          value: name,
          onChange: e => setName(e.target.value),
          placeholder: "Parent's name — Asha Devi, Papa, Mummy…",
          autoFocus: true,
          className: "big-input",
        }),
        h("button", { className: "button big-btn", type: "submit", disabled: !name.trim() },
          "Get Started →"
        )
      ),
      h(SafetyNotice)
    )
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// MAIN APP — single page, tab-based
// ─────────────────────────────────────────────────────────────────────────────

function App() {
  const [profile, setProfile] = useState(loadProfile);
  const [tab, setTab] = useState("home");
  const [lastCheckin, setLastCheckin] = useState(null);

  if (!profile) {
    return h(WelcomeScreen, { onStart: p => { setProfile(p); setTab("home"); } });
  }

  const tabs = [
    ["home",      "🏠",  "Home"],
    ["checkin",   "🎙️", "Check-In"],
    ["upload",    "📄",  "Upload"],
    ["ask",       "💬",  "Ask"],
    ["family",    "👨‍👩‍👧", "Family"],
  ];

  return h("div", { className: "app" },
    // Top bar
    h("header", { className: "topbar" },
      h("div", { className: "topbar-brand" },
        h("span", { className: "brand-mark small" }, "स"),
        h("span", { className: "topbar-name" }, profile.name)
      ),
      h("button", {
        className: "topbar-settings",
        onClick: () => setTab(tab === "settings" ? "home" : "settings"),
        title: "Settings"
      }, "⚙")
    ),
    // Content
    h("main", { className: "main-content" },
      tab === "home"     && h(HomeTab,              { profile, onCheckin: () => setTab("checkin"), onUpload: () => setTab("upload"), onAsk: () => setTab("ask"), lastCheckin }),
      tab === "checkin"  && h(CheckinTab,           { profile, onDone: r => { setLastCheckin(r); setTab("home"); } }),
      tab === "upload"   && h(UploadTab,            { profile }),
      tab === "ask"      && h(AskTab,               { profile }),
      tab === "family"   && h(CaregiverDashboard,   { profile }),
      tab === "settings" && h(SettingsTab,          { profile, onSave: p => { setProfile(p); saveProfile(p); setTab("home"); }, onReset: () => { localStorage.removeItem(PROFILE_KEY); setProfile(null); } })
    ),
    // Bottom nav
    h("nav", { className: "bottom-nav" },
      tabs.map(([id, icon, label]) =>
        h("button", { key: id, className: `nav-btn ${tab === id ? "active" : ""}`, onClick: () => setTab(id) },
          h("span", { className: "nav-icon" }, icon),
          h("span", { className: "nav-label" }, label)
        )
      )
    )
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// HOME TAB — dashboard
// ─────────────────────────────────────────────────────────────────────────────

function HomeTab({ profile, onCheckin, onUpload, onAsk, lastCheckin }) {
  const [patterns, setPatterns] = useState(null);
  const [pBusy, setPBusy] = useState(false);
  const [emergencyBusy, setEmergencyBusy] = useState(false);
  const [emergencyMsg, setEmergencyMsg] = useState("");

  useEffect(() => { fetchPatterns(); }, [profile.id]);

  async function fetchPatterns() {
    setPBusy(true);
    try {
      const d = await api.patterns({ subject_id: profile.id, days: 14 });
      setPatterns(d);
    } catch { setPatterns({ patterns: [] }); }
    finally { setPBusy(false); }
  }

  async function triggerEmergency() {
    if (!confirm("Send emergency alert to family?")) return;
    setEmergencyBusy(true);
    setEmergencyMsg("");
    try {
      await api.emergency(profile.id, profile.name, "Help needed — emergency alert");
      setEmergencyMsg("✅ Alert sent to family!");
    } catch { setEmergencyMsg("Could not send alert. Call 112."); }
    finally { setEmergencyBusy(false); }
  }

  return h("div", { className: "tab-content" },
    // Parent banner
    h("div", { className: "parent-banner" },
      h("div", { className: "parent-avatar" }, profile.name[0].toUpperCase()),
      h("div", null,
        h("div", { className: "parent-name" }, profile.name),
        h("div", { className: "parent-sub" }, profile.relation || "Family member")
      ),
      h("button", { className: "button checkin-cta", onClick: onCheckin }, "🎙️ Check-In")
    ),

    // Latest check-in card
    lastCheckin
      ? h("div", { className: "card green-card" },
          h("div", { className: "card-row" },
            h("span", { className: "card-title" }, "Today's Check-In"),
            h("span", { className: "mood-tag" }, `${moodEmoji(lastCheckin.summary.mood)} ${lastCheckin.summary.mood}`)
          ),
          h("p", { className: "card-body" }, lastCheckin.summary.summary_text),
          lastCheckin.summary.direct_quote
            ? h("div", { className: "quote-block" }, `"${lastCheckin.summary.direct_quote}"`)
            : null,
          lastCheckin.summary.flags && lastCheckin.summary.flags.length
            ? h("div", { className: "flag-row" },
                lastCheckin.summary.flags.map((f, i) => h("span", { key: i, className: "flag-pill" }, `⚠ ${f}`))
              )
            : null
        )
      : h("div", { className: "card empty-card", onClick: onCheckin },
          h("p", null, "No check-in today yet"),
          h("span", { className: "empty-cta" }, "Tap to start →")
        ),

    // Patterns
    h("div", { className: "section-title" }, "Noticed recently"),
    pBusy
      ? h(Spinner)
      : patterns && patterns.patterns && patterns.patterns.length
        ? h("div", null,
            patterns.patterns.map((p, i) =>
              h("div", { key: i, className: "card warn-card" },
                h("span", { className: "warn-tag" }, p.pattern_type),
                h("p", { className: "card-body" }, p.summary),
                p.evidence_quotes && p.evidence_quotes.length
                  ? h("div", { className: "evidence" }, p.evidence_quotes.slice(0, 2).map((q, j) => h("div", { key: j, className: "evidence-item" }, q)))
                  : null
              )
            )
          )
        : h("div", { className: "card empty-card" }, h("p", null, "Nothing repeated in the last 14 days")),

    // Quick actions
    h("div", { className: "quick-actions" },
      h("button", { className: "action-btn", onClick: onUpload }, h("span", null, "📄"), "Upload prescription"),
      h("button", { className: "action-btn", onClick: onAsk }, h("span", null, "💬"), "Ask about history")
    ),

    // Emergency button
    emergencyMsg
      ? h("div", { className: emergencyMsg.startsWith("✅") ? "success-msg" : "error-msg" }, emergencyMsg)
      : null,
    h(BusyBtn, {
      onClick: triggerEmergency,
      busy: emergencyBusy,
      label: "🆘 MADAD CHAHIYE",
      busyLabel: "Sending alert…",
      className: "button emergency-btn",
    }),

    h(SafetyNotice)
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// CHECK-IN TAB
// ─────────────────────────────────────────────────────────────────────────────

const PROMPTS = [
  "Aaj kaisa feel ho raha hai? (How are you feeling today?)",
  "Koi takleef? (Any pain or discomfort?)",
  "Dawai li? (Did you take your medicine?)",
  "Kuch aur batana chahenge? (Anything else to tell the family?)",
];

const SAMPLES = [
  "Aaj subah chakkar aaya. BP ki dawa le li. Chai paratha khaya.",
  "Neend achhi hui. Subah walk ki. Dawa time pe li.",
  "Pet mein dard hai kal se. Dawa nahi li thi. Aaj le li.",
];

function CheckinTab({ profile, onDone }) {
  const [transcript, setTranscript] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  async function submit() {
    if (!transcript.trim()) return;
    setBusy(true);
    setError("");
    try {
      const tz = (() => {
        const off = new Date().getTimezoneOffset();
        const s = off <= 0 ? "+" : "-";
        const h = String(Math.floor(Math.abs(off) / 60)).padStart(2, "0");
        const m = String(Math.abs(off) % 60).padStart(2, "0");
        return `${s}${h}:${m}`;
      })();
      const data = await api.checkin({
        transcript,
        subject_id: profile.id,
        subject_name: profile.name,
        current_datetime: `${nowIso()}:00${tz}`,
      });
      setResult(data);
    } catch (e) { setError(friendlyError(e)); }
    finally { setBusy(false); }
  }

  // Done screen
  if (result) {
    return h("div", { className: "tab-content center-content" },
      h("div", { className: "done-circle" }, "✓"),
      h("h3", { style: { marginTop: 12 } }, "Check-In Saved"),
      h("div", { className: "card green-card", style: { marginTop: 16, textAlign: "left" } },
        h("div", { className: "card-row" },
          h("span", { className: "mood-tag" }, `${moodEmoji(result.summary.mood)} ${result.summary.mood}`)
        ),
        h("p", { className: "card-body" }, result.summary.summary_text),
        result.summary.direct_quote ? h("div", { className: "quote-block" }, `"${result.summary.direct_quote}"`) : null,
        result.summary.flags && result.summary.flags.length
          ? h("div", { className: "flag-row" }, result.summary.flags.map((f, i) => h("span", { key: i, className: "flag-pill" }, `⚠ ${f}`)))
          : null,
        result.summary.medicines && result.summary.medicines.length
          ? h("div", { className: "pill-row", style: { marginTop: 8 } },
              h("span", { className: "sub-label" }, "Medicines: "),
              result.summary.medicines.map((m, i) => h("span", { key: i, className: "pill pill-green" }, m))
            )
          : null
      ),
      h("button", { className: "button big-btn", onClick: () => onDone(result), style: { marginTop: 16 } }, "Back to Home"),
      h("button", { className: "button secondary-btn", onClick: () => { setResult(null); setTranscript(""); }, style: { marginTop: 8 } }, "New Check-In")
    );
  }

  return h("div", { className: "tab-content" },
    h("div", { className: "section-title" }, "Aaj kaisa hai? 🙏"),
    h("div", { className: "prompts" },
      PROMPTS.map((p, i) => h("div", { key: i, className: "prompt" }, p))
    ),
    h("div", { className: "section-title", style: { marginTop: 20 } }, "Boliye ya type karein"),
    h(VoiceButton, {
      label: "🎙️ BOLIYE",
      onTranscript: t => setTranscript(prev => prev ? prev + " " + t : t),
    }),
    h("textarea", {
      value: transcript,
      onChange: e => setTranscript(e.target.value),
      placeholder: "Aaj subah chakkar aaya. BP ki dawa le li…",
      className: "checkin-textarea",
    }),
    h("details", { className: "sample-details" },
      h("summary", null, "Try a sample"),
      h("div", { className: "samples" },
        SAMPLES.map((s, i) => h("div", { key: i, className: "sample-item", onClick: () => setTranscript(s) }, s))
      )
    ),
    error ? h("div", { className: "error-msg" }, error) : null,
    h(BusyBtn, { onClick: submit, busy, disabled: !transcript.trim(), label: "SAHI HAI — Save Karein ✓", busyLabel: "Yaad kar raha hoon…", className: "button big-btn", style: { marginTop: 16 } })
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// UPLOAD TAB
// ─────────────────────────────────────────────────────────────────────────────

function UploadTab({ profile }) {
  const fileRef = useRef();
  const [cards, setCards] = useState([]);
  const [selected, setSelected] = useState([]);
  const [busy, setBusy] = useState(false);
  const [savebusy, setSaveBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");

  async function pick(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setBusy(true); setCards([]); setMsg(""); setError("");
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("persona", "care");
      fd.append("subject_id", profile.id);
      fd.append("subject_name", profile.name);
      const d = await api.previewDocument(fd);
      setCards(d.memories);
      setSelected(d.memories.map(() => true));
      setMsg(`Found ${d.memories.length} memory card${d.memories.length !== 1 ? "s" : ""}`);
    } catch (e) { setError(friendlyError(e)); }
    finally { setBusy(false); if (fileRef.current) fileRef.current.value = ""; }
  }

  async function save() {
    const toSave = cards.filter((_, i) => selected[i]);
    if (!toSave.length) return;
    setSaveBusy(true); setError("");
    try {
      const d = await api.saveMemories(toSave);
      setMsg(`Saved ${d.ids.length} card${d.ids.length !== 1 ? "s" : ""}${d.skipped_duplicates ? ` (${d.skipped_duplicates} already saved)` : ""}`);
      setCards([]); setSelected([]);
    } catch (e) { setError(friendlyError(e)); }
    finally { setSaveBusy(false); }
  }

  return h("div", { className: "tab-content" },
    h("div", { className: "section-title" }, "Upload Prescription / Report"),
    h("p", { className: "sub-text" }, "Photo or PDF of a prescription, lab report, or medicine label."),
    h("div", {
      className: "upload-zone",
      onClick: () => !busy && fileRef.current?.click()
    },
      busy
        ? h(Spinner)
        : h("div", null,
            h("div", { className: "upload-icon" }, "📄"),
            h("p", null, "Tap to pick file"),
            h("p", { className: "upload-hint" }, "PNG · JPG · PDF")
          )
    ),
    h("input", { ref: fileRef, type: "file", accept: "application/pdf,image/*", className: "hidden-input", onChange: pick }),
    msg ? h("div", { className: "success-msg" }, msg) : null,
    error ? h("div", { className: "error-msg" }, error) : null,
    cards.length ? h("div", null,
      h("div", { className: "section-title", style: { marginTop: 16 } }, `${cards.length} Memory Cards`),
      cards.map((c, i) =>
        h("div", { key: i, className: `card ${selected[i] ? "" : "card-dimmed"}`, onClick: () => setSelected(p => { const n = [...p]; n[i] = !n[i]; return n; }), style: { cursor: "pointer" } },
          h("div", { className: "card-row" },
            h("input", { type: "checkbox", checked: selected[i], onChange: () => {}, style: { marginRight: 8 } }),
            h("span", { className: `pill ${typeColor(c.type)}` }, c.type)
          ),
          h("p", { className: "card-body" }, c.text)
        )
      ),
      h(BusyBtn, { onClick: save, busy: savebusy, disabled: !selected.some(Boolean), label: `Save ${selected.filter(Boolean).length} Card${selected.filter(Boolean).length !== 1 ? "s" : ""}`, busyLabel: "Saving…", className: "button big-btn", style: { marginTop: 12 } })
    ) : null
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// ASK TAB
// ─────────────────────────────────────────────────────────────────────────────

const SUGGESTED = [
  "Has she mentioned dizziness before?",
  "What medicine is she taking?",
  "When was her last doctor visit?",
  "Did she miss any medicine recently?",
];

function AskTab({ profile }) {
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);
  const [answer, setAnswer] = useState(null);
  const [error, setError] = useState("");

  async function ask(question) {
    const query = question || q;
    if (!query.trim()) return;
    setBusy(true); setAnswer(null); setError("");
    try {
      const d = await api.ask({ question: query, persona: "care", subject_id: profile.id });
      setAnswer(d);
    } catch (e) { setError(friendlyError(e)); }
    finally { setBusy(false); }
  }

  return h("div", { className: "tab-content" },
    h("div", { className: "section-title" }, "Ask about " + profile.name),
    h("div", { className: "suggestions" },
      SUGGESTED.map(s =>
        h("button", { key: s, className: "suggestion-btn", onClick: () => { setQ(s); ask(s); } }, s)
      )
    ),
    h("div", { className: "ask-row" },
      h("input", {
        value: q,
        onChange: e => setQ(e.target.value),
        onKeyDown: e => e.key === "Enter" && ask(),
        placeholder: "Ask anything about their health history…",
        className: "ask-input",
      }),
      h(BusyBtn, { onClick: () => ask(), busy, disabled: !q.trim(), label: "Ask", busyLabel: "…", className: "button ask-btn" })
    ),
    error ? h("div", { className: "error-msg" }, error) : null,
    busy ? h(Spinner) : null,
    answer ? h("div", null,
      h("div", { className: "card answer-card" },
        h("p", { className: "answer-text" }, answer.answer)
      ),
      answer.sources && answer.sources.length
        ? h("div", null,
            h("div", { className: "section-title", style: { marginTop: 16 } }, "Sources"),
            answer.sources.map((s, i) =>
              h("div", { key: i, className: "source-item" },
                h("span", { className: "source-date" }, fmtDate(s.occurred_at)),
                h("p", { className: "source-text" }, s.text)
              )
            )
          )
        : null,
      h("p", { className: "disclaimer" }, "Smriti recalls recorded facts only. Not a diagnosis.")
    ) : null
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// TIMELINE TAB
// ─────────────────────────────────────────────────────────────────────────────

function TimelineTab({ profile }) {
  const [memories, setMemories] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => { load(); }, [profile.id]);

  async function load() {
    setBusy(true); setError("");
    try {
      const d = await api.listMemories("care", profile.id, 100);
      setMemories([...d].sort((a, b) => new Date(b.occurred_at) - new Date(a.occurred_at)));
    } catch (e) { setError(friendlyError(e)); }
    finally { setBusy(false); }
  }

  async function del(id) {
    if (!confirm("Delete this memory?")) return;
    await api.deleteMemory(id);
    setMemories(p => p.filter(m => m.id !== id));
  }

  const grouped = groupByDate(memories);

  return h("div", { className: "tab-content" },
    h("div", { className: "section-row" },
      h("div", { className: "section-title" }, "Memory Timeline"),
      h("button", { className: "refresh-btn", onClick: load }, "↻ Refresh")
    ),
    error ? h("div", { className: "error-msg" }, error) : null,
    busy ? h(Spinner) : null,
    !busy && memories.length === 0 ? h("div", { className: "card empty-card" }, h("p", null, "No memories yet")) : null,
    Object.entries(grouped).map(([date, items]) =>
      h("div", { key: date },
        h("div", { className: "date-group-label" }, date),
        items.map(m =>
          h("div", { key: m.id, className: "timeline-card" },
            h("div", { className: "timeline-row" },
              h("span", { className: `pill ${typeColor(m.type)}` }, m.type),
              h("span", { className: "time-label" }, fmtTime(m.occurred_at)),
              h("button", { className: "del-btn", onClick: () => del(m.id) }, "✕")
            ),
            h("p", { className: "timeline-text" }, m.text)
          )
        )
      )
    )
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// SETTINGS TAB
// ─────────────────────────────────────────────────────────────────────────────

function SettingsTab({ profile, onSave, onReset }) {
  const [name, setName] = useState(profile.name);
  const [relation, setRelation] = useState(profile.relation || "");
  const [medicines, setMedicines] = useState(profile.medicines || "");

  function save(e) {
    e.preventDefault();
    onSave({ ...profile, name: name.trim() || profile.name, relation, medicines });
  }

  return h("div", { className: "tab-content" },
    h("div", { className: "section-title" }, "Profile Settings"),
    h("form", { onSubmit: save },
      h("label", { className: "field-label" }, "Parent's name"),
      h("input", { value: name, onChange: e => setName(e.target.value), placeholder: "Asha Devi" }),
      h("label", { className: "field-label" }, "Relationship"),
      h("input", { value: relation, onChange: e => setRelation(e.target.value), placeholder: "Mother, Father, Grandma…" }),
      h("label", { className: "field-label" }, "Current medicines (optional)"),
      h("textarea", { value: medicines, onChange: e => setMedicines(e.target.value), placeholder: "Amlodipine 5mg for BP…", style: { minHeight: 72 } }),
      h("button", { className: "button big-btn", type: "submit", style: { marginTop: 16 } }, "Save"),
    ),
    h("div", { className: "section-title danger-title", style: { marginTop: 32 } }, "Demo"),
    h(DemoLoader, { profile }),
    h("div", { className: "section-title danger-title", style: { marginTop: 32 } }, "Reset"),
    h("button", {
      className: "button danger-btn",
      onClick: () => { if (confirm("Reset app? This clears your local profile.")) onReset(); }
    }, "Reset App")
  );
}

function DemoLoader({ profile }) {
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  async function load() {
    setBusy(true); setMsg("");
    try {
      const d = await api.loadDemo();
      setMsg(`✓ Loaded ${d.ids.length} demo memories (Asha Devi scenario). Go to Ask → "Has she mentioned dizziness before?"`);
    } catch (e) { setMsg(friendlyError(e)); }
    finally { setBusy(false); }
  }
  return h("div", null,
    h("p", { className: "sub-text" }, "Loads the Asha Devi demo: dizziness, missed BP medicine, Dr. Mehta follow-up."),
    h(BusyBtn, { onClick: load, busy, label: "Load Demo", busyLabel: "Loading…", className: "button secondary-btn" }),
    msg ? h("p", { className: "success-msg", style: { marginTop: 8 } }, msg) : null
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// CAREGIVER DASHBOARD TAB — "Family" view
// ─────────────────────────────────────────────────────────────────────────────

const URGENCY_COLORS = { green: "#2d7a4f", blue: "#1a5c8c", yellow: "#92610a", orange: "#c25a00", red: "#c0392b" };
const URGENCY_BG    = { green: "#e8f5ed", blue: "#e6f0fa", yellow: "#fef5e0", orange: "#fff0e0", red: "#fdecea" };
const FLAG_ICONS    = { dizziness: "💫", missed_medicine: "💊", pain: "🩹", fall: "⚠️", poor_sleep: "😴", bp_elevated: "🩸" };

function CaregiverDashboard({ profile }) {
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [askQ, setAskQ] = useState("");
  const [askBusy, setAskBusy] = useState(false);
  const [askAnswer, setAskAnswer] = useState(null);

  useEffect(() => { load(); }, [profile.id]);

  async function load() {
    setBusy(true); setError("");
    try {
      const d = await api.dashboard(profile.id);
      setData(d);
    } catch (e) { setError(friendlyError(e)); }
    finally { setBusy(false); }
  }

  async function askQuestion(q) {
    const query = q || askQ;
    if (!query.trim()) return;
    setAskBusy(true); setAskAnswer(null);
    try {
      const d = await api.ask({ question: query, persona: "care", subject_id: profile.id });
      setAskAnswer(d);
    } catch (e) { setAskAnswer({ answer: friendlyError(e), sources: [] }); }
    finally { setAskBusy(false); }
  }

  const urgency = data?.urgency || { score: 1, level: "green", reasons: [] };
  const uColor = URGENCY_COLORS[urgency.level] || URGENCY_COLORS.green;
  const uBg    = URGENCY_BG[urgency.level]    || URGENCY_BG.green;

  return h("div", { className: "tab-content" },
    // Header card
    h("div", { className: "caregiver-header", style: { background: uBg, borderColor: uColor } },
      h("div", { className: "caregiver-header-row" },
        h("div", null,
          h("div", { className: "caregiver-name" }, profile.name),
          h("div", { className: "caregiver-sub" }, profile.relation || "Family member"),
        ),
        h("div", { className: "urgency-badge", style: { background: uColor } },
          urgency.level === "green" ? "✓ All OK" :
          urgency.level === "blue"  ? "ℹ Note" :
          urgency.level === "yellow"? "⚠ Attention" :
          urgency.level === "orange"? "⚠ Follow Up" : "🆘 Urgent"
        )
      ),
      data?.last_checkin_at
        ? h("div", { className: "caregiver-meta" }, `Last check-in: ${fmtDateTime(data.last_checkin_at)} · ${data.memory_count || 0} memories`)
        : h("div", { className: "caregiver-meta" }, "No check-ins recorded yet"),
      urgency.reasons && urgency.reasons.length
        ? h("div", { className: "caregiver-reasons" }, urgency.reasons.join(" · "))
        : null
    ),

    // Refresh button
    h("button", { className: "refresh-btn", onClick: load, style: { alignSelf: "flex-end" } }, "↻ Refresh"),

    error ? h("div", { className: "error-msg" }, error) : null,
    busy ? h(Spinner) : null,

    // Care flags
    data?.flags && data.flags.length
      ? h("div", null,
          h("div", { className: "section-title" }, "⚠ Care Flags"),
          h("div", { className: "flag-grid" },
            data.flags.map((f, i) =>
              h("div", { key: i, className: "flag-card", style: { borderColor: uColor, background: uBg } },
                h("div", { className: "flag-icon" }, FLAG_ICONS[f.flag] || "⚠"),
                h("div", { className: "flag-label" }, f.label),
                h("div", { className: "flag-memory" }, `"${f.from_memory}"`),
                h("div", { className: "flag-date" }, fmtDate(f.date))
              )
            )
          )
        )
      : !busy && data
        ? h("div", { className: "card green-card" }, h("p", { style: { color: "#2d7a4f", fontWeight: 700 } }, "✓ No flags in recent check-ins"))
        : null,

    // Recent memories
    data?.recent_memories && data.recent_memories.length
      ? h("div", null,
          h("div", { className: "section-title" }, "Recent Memories"),
          data.recent_memories.map((m, i) =>
            h("div", { key: i, className: "timeline-card" },
              h("div", { className: "timeline-row" },
                h("span", { className: `pill ${typeColor(m.type)}` }, m.type),
                h("span", { className: "time-label" }, fmtDateTime(m.occurred_at))
              ),
              h("p", { className: "timeline-text" }, m.text)
            )
          )
        )
      : null,

    // Quick ask
    h("div", { className: "section-title" }, "Ask about " + profile.name),
    h("div", { className: "suggestion-row" },
      ["Has she mentioned dizziness?", "What medicine is she taking?", "How has her BP been?"].map(s =>
        h("button", { key: s, className: "suggestion-btn", onClick: () => { setAskQ(s); askQuestion(s); } }, s)
      )
    ),
    h("div", { className: "ask-row" },
      h("input", {
        value: askQ,
        onChange: e => setAskQ(e.target.value),
        onKeyDown: e => e.key === "Enter" && askQuestion(),
        placeholder: "Ask anything about their health history…",
        className: "ask-input",
      }),
      h(BusyBtn, { onClick: () => askQuestion(), busy: askBusy, disabled: !askQ.trim(), label: "Ask", busyLabel: "…", className: "button ask-btn" })
    ),
    askBusy ? h(Spinner) : null,
    askAnswer
      ? h("div", null,
          h("div", { className: "card answer-card" }, h("p", { className: "answer-text" }, askAnswer.answer)),
          askAnswer.sources && askAnswer.sources.length
            ? h("div", null,
                h("div", { className: "section-title", style: { marginTop: 12 } }, "Sources"),
                askAnswer.sources.map((s, i) =>
                  h("div", { key: i, className: "source-item" },
                    h("span", { className: "source-date" }, fmtDate(s.occurred_at)),
                    h("p", { className: "source-text" }, s.text)
                  )
                )
              )
            : null,
          h("p", { className: "disclaimer" }, "Smriti recalls recorded facts only. Not a diagnosis.")
        )
      : null,

    h(SafetyNotice)
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Shared tiny components
// ─────────────────────────────────────────────────────────────────────────────

function BusyBtn({ onClick, busy, disabled, label, busyLabel, className, style }) {
  return h("button", { className: `${className}${busy ? " busy" : ""}`, onClick, disabled: busy || disabled, style },
    busy ? h("span", { className: "spinner" }) : null,
    busy ? (busyLabel || label) : label
  );
}

function Spinner() {
  return h("div", { className: "spinner-wrap" }, h("span", { className: "spinner" }));
}

// ─────────────────────────────────────────────────────────────────────────────
// Mount
// ─────────────────────────────────────────────────────────────────────────────

const root = createRoot(document.getElementById("root"));
root.render(h(App));
