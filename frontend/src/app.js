import React, { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { api, friendlyError } from "./api.js";
import { defaultSubjects, memoryTypes, samples } from "./constants.js";
import { displayDateTime, isoDate, localDateTimeInputValue, toApiDateTime } from "./time.js";
import { VoiceButton } from "./voice.js";

const h = React.createElement;
const SUBJECTS_STORAGE_KEY = "smriti.subjects";

function App() {
  const [subjects, setSubjects] = useState(loadSubjects);
  const [subject, setSubject] = useState(() => loadSubjects()[0]);
  const [newSubjectName, setNewSubjectName] = useState("");
  const [newSubjectPersona, setNewSubjectPersona] = useState("care");
  const persona = subject.persona;
  const [status, setStatus] = useState(null);
  const [memoryCheck, setMemoryCheck] = useState(null);
  const [notice, setNotice] = useState("Ready");
  const [busyAction, setBusyAction] = useState(null);
  const [activeView, setActiveView] = useState("remember");
  const [log, setLog] = useState(samples.care[0]);
  const [currentDatetime, setCurrentDatetime] = useState(localDateTimeInputValue());
  const [showMemoryDate, setShowMemoryDate] = useState(false);
  const [preview, setPreview] = useState([]);
  const [previewSelected, setPreviewSelected] = useState([]);
  const [previewQuality, setPreviewQuality] = useState([]);
  const [question, setQuestion] = useState("What was Papa's BP?");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [answer, setAnswer] = useState(null);
  const [history, setHistory] = useState([]);
  const [editingId, setEditingId] = useState(null);
  const [editDraft, setEditDraft] = useState(null);
  const [summary, setSummary] = useState(null);
  const [summaryFromDate, setSummaryFromDate] = useState("");
  const [summaryToDate, setSummaryToDate] = useState("");
  const [evalText, setEvalText] = useState("What was Papa's BP? => 150\nWhen did Papa sleep badly? => poor sleep");
  const [evalResult, setEvalResult] = useState(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [searchThreshold, setSearchThreshold] = useState(0.30);
  const [searchLimit, setSearchLimit] = useState(50);
  const [rerank, setRerank] = useState(true);
  const [acceptThreshold, setAcceptThreshold] = useState(0.45);
  const [maybeThreshold, setMaybeThreshold] = useState(0.30);

  const statusOk = status?.api === "ok" && status?.supermemory === "ok" && status?.groq === "configured";
  const activeTitle = `${subject.name} memory`;

  useEffect(() => {
    refreshStatus();
  }, []);

  useEffect(() => {
    localStorage.setItem(SUBJECTS_STORAGE_KEY, JSON.stringify(subjects));
  }, [subjects]);

  useEffect(() => {
    setLog(samples[subject.persona][0]);
    setPreview([]);
    setPreviewSelected([]);
    setPreviewQuality([]);
    setAnswer(null);
    setSummary(null);
    setEditingId(null);
    setEditDraft(null);
    loadHistory(subject.persona, subject.id);
  }, [subject]);

  async function refreshStatus() {
    try {
      setStatus(await api.status());
    } catch (error) {
      setStatus({ api: "error", supermemory: "unknown", groq: "unknown" });
      setNotice(friendlyError(error));
    }
  }

  async function runMemoryCheck() {
    setNotice("Testing memory save, search, cleanup...");
    setBusyAction("memory-check");
    setMemoryCheck(null);
    try {
      const data = await api.memoryCheck();
      setMemoryCheck(data);
      const ok = data.save_ok && data.search_ok && data.cleanup_ok;
      setNotice(ok ? "Memory round-trip passed" : "Memory round-trip needs attention");
    } catch (error) {
      setMemoryCheck({ save_ok: false, search_ok: false, cleanup_ok: false, detail: friendlyError(error) });
      setNotice(friendlyError(error));
    } finally {
      setBusyAction(null);
    }
  }

  async function loadHistory(nextPersona = persona, nextSubjectId = subject.id) {
    setNotice("Loading memories...");
    setBusyAction("history");
    try {
      const data = await api.listMemories(nextPersona, nextSubjectId);
      setHistory(data);
      setNotice(`Loaded ${data.length} memories`);
    } catch (error) {
      setHistory([]);
      setNotice(friendlyError(error));
    } finally {
      setBusyAction(null);
    }
  }

  async function previewLog() {
    setNotice("Structuring memory...");
    setBusyAction("preview");
    const memoryDatetime = showMemoryDate ? currentDatetime : localDateTimeInputValue();
    if (!showMemoryDate) setCurrentDatetime(memoryDatetime);
    try {
      const data = await api.preview({
        text: log,
        persona,
        subject_id: subject.id,
        subject_name: subject.name,
        current_datetime: toApiDateTime(memoryDatetime),
      });
      setPreview(data.memories);
      setPreviewSelected(data.memories.map(() => true));
      setPreviewQuality(data.quality || []);
      setNotice(data.memories.length ? `Preview ready: ${data.memories.length} card(s)` : "No health memory found");
    } catch (error) {
      setNotice(friendlyError(error));
    } finally {
      setBusyAction(null);
    }
  }

  async function savePreview() {
    const selectedMemories = preview.filter((_, index) => previewSelected[index] !== false);
    if (!selectedMemories.length) {
      setNotice("Select at least one card to save.");
      return;
    }
    setNotice("Saving memory...");
    setBusyAction("save");
    try {
      const data = await api.saveMemories(selectedMemories);
      setNotice(`Saved ${data.ids.length} memory${data.skipped_duplicates ? `, skipped ${data.skipped_duplicates} duplicate` : ""}`);
      setPreview([]);
      setPreviewSelected([]);
      setPreviewQuality([]);
      setTimeout(() => loadHistory(persona, subject.id), 1000);
    } catch (error) {
      setNotice(friendlyError(error));
    } finally {
      setBusyAction(null);
    }
  }

  async function askMemory() {
    setNotice("Searching memory...");
    setBusyAction("ask");
    try {
      const data = await api.ask(retrievalBody({ question, persona, subject_id: subject.id }));
      setAnswer(data);
      setNotice("Answer ready");
    } catch (error) {
      setNotice(friendlyError(error));
    } finally {
      setBusyAction(null);
    }
  }

  async function runRetrievalEval() {
    setNotice("Checking retrieval...");
    const cases = evalText
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => {
        const [q, expected] = line.split("=>").map((part) => part.trim());
        return { question: q, expected_contains: expected || null };
      })
      .filter((item) => item.question);
    if (!cases.length) {
      setNotice("Add at least one eval question.");
      return;
    }
    try {
      setBusyAction("eval");
      const data = await api.evalRetrieval(retrievalBody({ persona, subject_id: subject.id, cases }));
      setEvalResult(data);
      setNotice(`Retrieval check: ${data.pass_count} pass, ${data.fail_count} fail`);
    } catch (error) {
      setNotice(friendlyError(error));
    } finally {
      setBusyAction(null);
    }
  }

  function retrievalBody(base) {
    const accepted = Number(acceptThreshold);
    const maybe = Math.min(Number(maybeThreshold), accepted);
    const body = {
      ...base,
      search_threshold: Number(searchThreshold),
      search_limit: Number(searchLimit),
      rerank,
      accept_threshold: accepted,
      maybe_threshold: maybe,
    };
    if (fromDate) body.from_date = fromDate;
    if (toDate) body.to_date = toDate;
    return body;
  }

  async function generateSummary() {
    setNotice("Generating visit summary...");
    setBusyAction("summary");
    const body = { persona, subject_id: subject.id };
    if (summaryFromDate) body.from_date = summaryFromDate;
    if (summaryToDate) body.to_date = summaryToDate;
    try {
      setSummary(await api.summary(body));
      setNotice("Visit summary ready");
    } catch (error) {
      setNotice(friendlyError(error));
    } finally {
      setBusyAction(null);
    }
  }

  async function copySummary() {
    if (!summary) return;
    await navigator.clipboard.writeText(summary.summary);
    setNotice("Summary copied");
  }

  async function loadDemo() {
    setNotice("Loading demo memories...");
    setBusyAction("demo");
    try {
      const data = await api.loadDemo();
      setFromDate("");
      setToDate("");
      setQuestion("What was Papa's BP?");
      setEvalText(data.eval_questions);
      setActiveView("ask");
      setAnswer(null);
      setEvalResult(null);
      setNotice(`Demo ready: saved ${data.ids.length}, skipped ${data.skipped_duplicates} duplicate${data.skipped_duplicates === 1 ? "" : "s"}`);
      setSubject(subjects.find((item) => item.id === "papa") || subjects[0]);
      setTimeout(() => loadHistory("care", "papa"), 1000);
    } catch (error) {
      setNotice(friendlyError(error));
    } finally {
      setBusyAction(null);
    }
  }

  async function deleteMemory(id) {
    if (!confirm("Delete this saved memory?")) return;
    await api.deleteMemory(id);
    setHistory((items) => items.filter((item) => item.id !== id));
    setNotice("Memory deleted");
  }

  async function saveEdit() {
    const body = {
      text: editDraft.text,
      type: editDraft.type,
      persona: editDraft.persona,
      subject_id: editDraft.subject_id,
      subject_name: editDraft.subject_name,
      occurred_at: editDraft.occurred_at,
      entities: editDraft.entities || {},
      raw: editDraft.raw || editDraft.text,
    };
    const updated = await api.updateMemory(editingId, body);
    setHistory((items) => items.map((item) => item.id === editingId ? updated : item));
    setEditingId(null);
    setEditDraft(null);
    setNotice("Memory updated");
  }

  function setRange(kind) {
    const today = new Date();
    const start = new Date(today);
    if (kind === "today") {
      setFromDate(isoDate(today));
      setToDate(isoDate(today));
    }
    if (kind === "yesterday") {
      start.setDate(today.getDate() - 1);
      setFromDate(isoDate(start));
      setToDate(isoDate(start));
    }
    if (kind === "last7") {
      start.setDate(today.getDate() - 6);
      setFromDate(isoDate(start));
      setToDate(isoDate(today));
    }
    if (kind === "clear") {
      setFromDate("");
      setToDate("");
    }
  }

  function updatePreview(index, key, value) {
    setPreview((items) => items.map((item, current) => current === index ? { ...item, [key]: value } : item));
  }

  function setPreviewFromUpload(data) {
    setPreview(data.memories);
    setPreviewSelected(data.memories.map(() => true));
    setPreviewQuality(data.quality || []);
    setNotice(data.memories.length ? `Upload preview ready: ${data.memories.length} card(s)` : "No readable health facts found");
  }

  function togglePreview(index) {
    setPreviewSelected((items) => items.map((item, current) => current === index ? !item : item));
  }

  function addSubject() {
    const name = newSubjectName.trim();
    if (!name) {
      setNotice("Enter a person name.");
      return;
    }
    const id = uniqueSubjectId(slugify(name), subjects);
    const nextSubject = { id, name, persona: newSubjectPersona };
    setSubjects((items) => [...items, nextSubject]);
    setSubject(nextSubject);
    setNewSubjectName("");
    setNotice(`Added ${name}`);
  }

  const views = [
    ["remember", "Remember"],
    ["ask", "Ask"],
    ["history", "Timeline"],
    ["summary", "Summary"],
  ];

  return h("div", { className: "app-shell" },
    h("aside", { className: "sidebar" },
      h("div", { className: "brand-lockup" },
        h("div", { className: "brand-mark" }, "S"),
        h("div", null,
          h("h1", null, "Smriti"),
          h("p", null, "Health memory you can trust later.")
        )
      ),
      h("div", { className: "persona-card" },
        h("span", { className: "eyebrow" }, "Person"),
        h("div", { className: "segmented" },
          subjects.map((item) =>
            h("button", {
              key: item.id,
              className: subject.id === item.id ? "active" : "",
              onClick: () => setSubject(item),
            }, item.name)
          )
        ),
        h("div", { className: "add-person" },
          h("input", {
            value: newSubjectName,
            onChange: (event) => setNewSubjectName(event.target.value),
            onKeyDown: (event) => {
              if (event.key === "Enter") addSubject();
            },
            placeholder: "Add anyone...",
          }),
          h("select", {
            value: newSubjectPersona,
            onChange: (event) => setNewSubjectPersona(event.target.value),
          },
            h("option", { value: "care" }, "Care"),
            h("option", { value: "self" }, "Self")
          ),
          h("button", { className: "button mini secondary", onClick: addSubject }, "+ Add person")
        )
      ),
      h("nav", { className: "nav-list" },
        views.map(([id, label]) =>
          h("button", {
            key: id,
            className: activeView === id ? "active" : "",
            onClick: () => setActiveView(id),
          }, label)
        )
      ),
      h(BusyButton, {
        className: "button ghost wide",
        onClick: loadDemo,
        busy: busyAction === "demo",
        label: "Load demo memories",
        busyLabel: "Loading demo...",
      }),
      h("p", { className: "sidebar-note" }, "Demo data is local and duplicate-safe.")
    ),
    h("main", { className: "workspace" },
      h("header", { className: "hero-band" },
        h("div", null,
          h("span", { className: "eyebrow" }, activeTitle),
          h("h2", null, "Say it once. Find it when it matters."),
          h("p", null, "Capture care notes by voice or text, confirm the exact memory, then ask from a dated timeline.")
        ),
        h(StatusBadge, { status, statusOk, notice, refreshStatus, runMemoryCheck, memoryCheck, busyAction })
      ),
      h("section", { className: "flow-strip" },
        ["Speak or type", "Confirm memory", "Ask later"].map((step, index) =>
          h("div", { className: "flow-step", key: step },
            h("span", null, index + 1),
            h("strong", null, step)
          )
        )
      ),
      activeView === "remember" && h(RememberView, {
        persona, subject, log, setLog, currentDatetime, setCurrentDatetime, showMemoryDate,
        setShowMemoryDate, previewLog, preview, previewQuality, updatePreview,
        savePreview, setPreview, setPreviewQuality, setPreviewSelected,
        previewSelected, togglePreview, setPreviewFromUpload, setNotice, busyAction, setBusyAction,
      }),
      activeView === "ask" && h(AskView, {
        question, setQuestion, fromDate, setFromDate, toDate, setToDate, setRange,
        askMemory, answer, showAdvanced, setShowAdvanced, searchThreshold,
        setSearchThreshold, searchLimit, setSearchLimit, rerank, setRerank,
        acceptThreshold, setAcceptThreshold, maybeThreshold, setMaybeThreshold,
        evalText, setEvalText, evalResult, runRetrievalEval, busyAction,
      }),
      activeView === "history" && h(HistoryView, {
        history, loadHistory, persona, subject, editingId, setEditingId, editDraft, busyAction,
        setEditDraft, saveEdit, deleteMemory,
      }),
      activeView === "summary" && h(SummaryView, {
        summary, summaryFromDate, setSummaryFromDate, summaryToDate,
        setSummaryToDate, generateSummary, copySummary, busyAction,
      })
    )
  );
}

function StatusBadge({ status, statusOk, notice, refreshStatus, runMemoryCheck, memoryCheck, busyAction }) {
  const mode = status?.memory_mode ? ` · ${status.memory_mode}` : "";
  const label = statusOk
    ? `Ready${mode} · Groq AI`
    : status
      ? `API ${status.api} | Memory ${status.supermemory}${mode} | Groq ${status.groq}`
      : "Checking";
  const checkItems = memoryCheck ? [
    ["Save", memoryCheck.save_ok],
    ["Search", memoryCheck.search_ok],
    ["Cleanup", memoryCheck.cleanup_ok],
  ] : [];
  return h("div", { className: "status-card" },
    h("div", { className: "status-line" },
      h("span", { className: `status-dot ${statusOk ? "ok" : ""}` }),
      h("strong", null, label)
    ),
    h("p", null, status?.memory_target ? `${notice} Memory target: ${status.memory_target}.` : notice),
    memoryCheck && h("div", { className: "check-row" },
      checkItems.map(([label, ok]) =>
        h("span", { className: `pill ${ok ? "accent" : ""}`, key: label }, `${label}: ${ok ? "ok" : "fail"}`)
      )
    ),
    memoryCheck?.detail && h("p", { className: "tiny-warn" }, memoryCheck.detail),
    h("div", { className: "inline-actions tight" },
      h("button", { className: "button mini ghost", onClick: refreshStatus }, "Refresh"),
      h(BusyButton, {
        className: "button mini secondary",
        onClick: runMemoryCheck,
        disabled: !statusOk,
        busy: busyAction === "memory-check",
        label: "Test memory",
        busyLabel: "Testing...",
      })
    )
  );
}

function RememberView(props) {
  const fileInput = useRef(null);

  async function uploadReport(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    props.setNotice("Reading report...");
    props.setBusyAction("upload");
    const memoryDatetime = props.showMemoryDate ? props.currentDatetime : localDateTimeInputValue();
    if (!props.showMemoryDate) props.setCurrentDatetime(memoryDatetime);
    const formData = new FormData();
    formData.append("persona", props.persona);
    formData.append("subject_id", props.subject.id);
    formData.append("subject_name", props.subject.name);
    formData.append("current_datetime", toApiDateTime(memoryDatetime));
    formData.append("file", file);
    try {
      const data = await api.previewDocument(formData);
      props.setPreviewFromUpload(data);
    } catch (error) {
      props.setNotice(friendlyError(error));
    } finally {
      props.setBusyAction(null);
      event.target.value = "";
    }
  }

  const previewBusy = props.busyAction === "preview";
  const saveBusy = props.busyAction === "save";
  const uploadBusy = props.busyAction === "upload";
  return h("div", { className: "view-grid" },
    h("section", { className: `surface primary ${previewBusy || uploadBusy ? "working" : ""}` },
      h("div", { className: "section-head" },
        h("div", null, h("h3", null, "Add memory"), h("p", null, "Nothing saves until you confirm.")),
        h("span", { className: "pill accent" }, props.subject.name)
      ),
      h("div", { className: "capture-row" },
        h(VoiceButton, { label: "Speak memory", onTranscript: props.setLog }),
        h(BusyButton, {
          className: "button secondary",
          onClick: () => fileInput.current?.click(),
          busy: uploadBusy,
          label: "Upload report",
          busyLabel: "Reading...",
        }),
        h("input", {
          ref: fileInput,
          type: "file",
          className: "hidden-file",
          accept: "application/pdf,image/png,image/jpeg,image/webp",
          onChange: uploadReport,
        })
      ),
      h("label", null, "Memory note"),
      h("textarea", { value: props.log, onChange: (e) => props.setLog(e.target.value), placeholder: "Papa had stomach pain after dinner and took medicine." }),
      h("div", { className: "inline-actions" },
        h("button", { className: "button secondary", onClick: () => props.setShowMemoryDate(!props.showMemoryDate) }, props.showMemoryDate ? "Hide date" : "Advanced date"),
        h("span", { className: "pill" }, `Saving as ${displayDateTime(props.currentDatetime)}`)
      ),
      props.showMemoryDate && h("div", { className: "advanced-box two-col" },
        h("div", null, h("label", null, "Memory time"), h("input", { type: "datetime-local", value: props.currentDatetime, onChange: (e) => props.setCurrentDatetime(e.target.value) })),
        h("div", null, h("label", null, "Quick sample"), h("select", { value: props.log, onChange: (e) => props.setLog(e.target.value) }, samples[props.persona].map((sample) => h("option", { key: sample, value: sample }, sample))))
      ),
      h("div", { className: "actions" },
        h(BusyButton, {
          className: "button",
          onClick: props.previewLog,
          busy: previewBusy,
          label: "Preview",
          busyLabel: "Structuring...",
        }),
        h("button", { className: "button secondary", disabled: previewBusy || saveBusy || uploadBusy, onClick: () => { props.setPreview([]); props.setPreviewQuality([]); props.setPreviewSelected([]); } }, "Clear")
      )
    ),
    h("section", { className: `surface ${saveBusy ? "working" : ""}` },
      h("div", { className: "section-head" }, h("div", null, h("h3", null, "Confirm cards"), h("p", null, "Edit what Smriti will remember."))),
      (previewBusy || uploadBusy) ? h(LoadingState, { text: previewBusy ? "Structuring memory cards..." : "Reading report..." }) : null,
      props.preview.length === 0
        ? h("div", { className: "empty-state" }, "Preview cards appear here.")
        : props.preview.map((memory, index) => h(PreviewCard, {
          key: index,
          memory,
          index,
          selected: props.previewSelected[index] !== false,
          togglePreview: props.togglePreview,
          quality: props.previewQuality[index],
          updatePreview: props.updatePreview,
        })),
      h("div", { className: "actions" },
        h(BusyButton, {
          className: "button",
          onClick: props.savePreview,
          disabled: props.preview.length === 0,
          busy: saveBusy,
          label: "Save selected",
          busyLabel: "Saving...",
        })
      )
    )
  );
}

function PreviewCard({ memory, index, selected, togglePreview, quality = {}, updatePreview }) {
  return h("article", { className: `memory-card ${selected ? "" : "muted-card"}` },
    h("div", { className: "memory-title" },
      h("div", null, h("h4", null, quality.title || "Memory card"), h("p", null, memory.text)),
      h("label", { className: "check-label" },
        h("input", { type: "checkbox", checked: selected, onChange: () => togglePreview(index) }),
        h("span", null, selected ? "Save" : "Skip")
      )
    ),
    h("span", { className: `pill ${quality.duplicate ? "danger-soft" : "good"}` }, quality.confidence || "review"),
    h("div", { className: "pill-row" },
      h("span", { className: "pill accent" }, memory.subject_name || memory.subject_id || "Person"),
      h("span", { className: "pill" }, memory.type),
      h("span", { className: "pill" }, displayDateTime(memory.occurred_at)),
      (quality.signals || []).map((signal) => h("span", { className: "pill", key: signal }, signal))
    ),
    quality.duplicate ? h("div", { className: "empty-state compact" }, "Looks already saved. Save will skip it.") : null,
    h("label", null, "Edit text"),
    h("textarea", { value: memory.text, onChange: (e) => updatePreview(index, "text", e.target.value) }),
    h("div", { className: "two-col" },
      h("div", null, h("label", null, "Type"), h("select", { value: memory.type, onChange: (e) => updatePreview(index, "type", e.target.value) }, memoryTypes.map((type) => h("option", { key: type, value: type }, type)))),
      h("div", null, h("label", null, "Occurred at"), h("input", { type: "datetime-local", value: localDateTimeInputValue(memory.occurred_at), onChange: (e) => updatePreview(index, "occurred_at", toApiDateTime(e.target.value)) }))
    )
  );
}

function AskView(props) {
  const sourceCount = props.answer?.sources?.length || 0;
  const askBusy = props.busyAction === "ask";
  const evalBusy = props.busyAction === "eval";
  return h("div", { className: "view-grid" },
    h("section", { className: `surface primary ${askBusy ? "working" : ""}` },
      h("div", { className: "section-head" }, h("div", null, h("h3", null, "Ask Smriti"), h("p", null, "Answers use selected person and date window.")), h("span", { className: "pill accent" }, `${sourceCount} sources`)),
      h(VoiceButton, { label: "Speak question", onTranscript: props.setQuestion }),
      h("input", { value: props.question, onChange: (e) => props.setQuestion(e.target.value), placeholder: "Ask about symptoms, medicine, vitals..." }),
      h(DateFilters, props),
      h("div", { className: "actions" }, h(BusyButton, {
        className: "button",
        onClick: props.askMemory,
        busy: askBusy,
        label: "Ask",
        busyLabel: "Searching...",
      })),
      askBusy ? h(LoadingState, { text: "Searching saved memories..." }) : null,
      props.answer ? h(AnswerBlock, { answer: props.answer }) : h("div", { className: "empty-state" }, "Answer appears here.")
    ),
    h("section", { className: `surface ${evalBusy ? "working" : ""}` },
      h("div", { className: "section-head" }, h("div", null, h("h3", null, "Retrieval check"), h("p", null, "Batch-test real questions.")), h("span", { className: "pill warn" }, props.evalResult ? `${props.evalResult.pass_count}/${props.evalResult.total}` : "demo ready")),
      h("textarea", { value: props.evalText, onChange: (e) => props.setEvalText(e.target.value), placeholder: "What was Papa's BP? => 150" }),
      h("div", { className: "actions" }, h(BusyButton, {
        className: "button",
        onClick: props.runRetrievalEval,
        busy: evalBusy,
        label: "Run check",
        busyLabel: "Checking...",
      })),
      evalBusy ? h(LoadingState, { text: "Checking retrieval quality..." }) : null,
      props.evalResult ? h(EvalResults, { result: props.evalResult }) : h("div", { className: "empty-state" }, "Run the check to see pass/fail and top match."),
      h(AdvancedRetrieval, props)
    )
  );
}

function DateFilters(props) {
  return h("div", null,
    h("div", { className: "two-col" },
      h("div", null, h("label", null, "From date"), h("input", { type: "date", value: props.fromDate, onChange: (e) => props.setFromDate(e.target.value) })),
      h("div", null, h("label", null, "To date"), h("input", { type: "date", value: props.toDate, onChange: (e) => props.setToDate(e.target.value) }))
    ),
    h("div", { className: "inline-actions" },
      [["today", "Today"], ["yesterday", "Yesterday"], ["last7", "Last 7 days"], ["clear", "All dates"]].map(([kind, label]) =>
        h("button", { key: kind, className: "button mini ghost", onClick: () => props.setRange(kind) }, label)
      )
    )
  );
}

function AdvancedRetrieval(props) {
  return h("details", { className: "advanced-details" },
    h("summary", null, "Advanced retrieval"),
    h("div", { className: "two-col" },
      h(Slider, { label: "Supermemory threshold", value: props.searchThreshold, min: 0, max: 1, step: 0.05, onChange: props.setSearchThreshold }),
      h(Slider, { label: "Search limit", value: props.searchLimit, min: 1, max: 100, step: 1, onChange: props.setSearchLimit })
    ),
    h("div", { className: "inline-actions" }, h("button", { className: "button mini secondary", onClick: () => props.setRerank(!props.rerank) }, `Rerank ${props.rerank ? "on" : "off"}`)),
    h("div", { className: "two-col" },
      h(Slider, { label: "Local accept", value: props.acceptThreshold, min: 0, max: 1, step: 0.05, onChange: props.setAcceptThreshold }),
      h(Slider, { label: "Local maybe", value: props.maybeThreshold, min: 0, max: props.acceptThreshold, step: 0.05, onChange: props.setMaybeThreshold })
    )
  );
}

function Slider({ label, value, min, max, step, onChange }) {
  return h("div", null,
    h("label", null, `${label}: ${Number(value).toFixed(step === 1 ? 0 : 2)}`),
    h("input", { type: "range", min, max, step, value, onChange: (e) => onChange(Number(e.target.value)) })
  );
}

function AnswerBlock({ answer }) {
  return h("div", { className: "answer-block" },
    h("h4", null, "Answer"),
    h("p", null, answer.answer),
    h("details", { className: "advanced-details" },
      h("summary", null, "Sources and debug"),
      h("div", { className: "source-list" }, answer.sources.map((source) => h("div", { className: "source", key: source.id || source.text }, h("small", null, displayDateTime(source.occurred_at)), h("div", null, source.text)))),
      answer.debug ? h("div", { className: "debug" },
        h("p", null, `Rewritten: ${answer.debug.rewritten_query}`),
        h("p", null, `Accepted ${answer.debug.accepted_count} | Maybe ${answer.debug.maybe_count} | Rejected ${answer.debug.rejected_count}`),
        answer.debug.outside_date_count > 0 ? h("div", { className: "empty-state compact" }, `Found ${answer.debug.outside_date_count} likely match outside date range.`) : null
      ) : null
    )
  );
}

function EvalResults({ result }) {
  return h("div", { className: "eval-list" },
    h("div", { className: "empty-state compact" }, `${result.pass_count} pass | ${result.fail_count} fail | ${result.unchecked_count} unchecked`),
    result.results.map((item, index) => {
      const status = item.passed === true ? "pass" : item.passed === false ? "fail" : "unchecked";
      return h("article", { className: `eval-card ${status}`, key: `${item.question}-${index}` },
        h("div", { className: "pill-row" },
          h("span", { className: "pill" }, status),
          item.top_score === null ? null : h("span", { className: "pill" }, `score ${item.top_score}`),
          h("span", { className: "pill" }, `${item.accepted_count} accepted`)
        ),
        h("h4", null, item.question),
        item.expected_contains ? h("p", null, `Expected: ${item.expected_contains}`) : null,
        item.top_match ? h("div", { className: "source" }, h("small", null, displayDateTime(item.top_match.occurred_at)), h("div", null, item.top_match.text)) : h("div", { className: "empty-state compact" }, "No top match")
      );
    })
  );
}

function HistoryView(props) {
  const historyBusy = props.busyAction === "history";
  return h("section", { className: `surface wide-surface ${historyBusy ? "working" : ""}` },
    h("div", { className: "section-head" },
      h("div", null, h("h3", null, "Timeline"), h("p", null, "View, edit, or delete saved memories.")),
      h(BusyButton, {
        className: "button ghost",
        onClick: () => props.loadHistory(props.persona, props.subject.id),
        busy: historyBusy,
        label: "Refresh",
        busyLabel: "Loading...",
      })
    ),
    historyBusy ? h(LoadingState, { text: "Loading timeline..." }) : null,
    props.history.length === 0 ? h("div", { className: "empty-state" }, "No saved memories loaded yet.") :
      h("div", { className: "timeline-list" }, props.history.map((memory) => h(HistoryItem, { key: memory.id || `${memory.text}-${memory.occurred_at}`, memory, ...props })))
  );
}

function HistoryItem({ memory, editingId, setEditingId, editDraft, setEditDraft, saveEdit, deleteMemory }) {
  const editing = editingId === memory.id;
  return h("article", { className: "timeline-item" },
    h("div", { className: "pill-row" }, h("span", { className: "pill accent" }, memory.subject_name || memory.subject_id || memory.persona), h("span", { className: "pill" }, memory.type), h("span", { className: "pill" }, displayDateTime(memory.occurred_at))),
    editing ? h(EditForm, { draft: editDraft, setDraft: setEditDraft, saveEdit, cancel: () => { setEditingId(null); setEditDraft(null); } }) :
      h(React.Fragment, null, h("p", null, memory.text), h("div", { className: "actions" }, h("button", { className: "button secondary", onClick: () => { setEditingId(memory.id); setEditDraft({ ...memory }); } }, "Edit"), h("button", { className: "button danger", onClick: () => deleteMemory(memory.id) }, "Delete")))
  );
}

function EditForm({ draft, setDraft, saveEdit, cancel }) {
  if (!draft) return null;
  return h("div", null,
    h("textarea", { value: draft.text, onChange: (e) => setDraft({ ...draft, text: e.target.value }) }),
    h("div", { className: "two-col" },
      h("div", null, h("label", null, "Type"), h("select", { value: draft.type, onChange: (e) => setDraft({ ...draft, type: e.target.value }) }, memoryTypes.map((type) => h("option", { key: type, value: type }, type)))),
      h("div", null, h("label", null, "Occurred at"), h("input", { type: "datetime-local", value: localDateTimeInputValue(draft.occurred_at), onChange: (e) => setDraft({ ...draft, occurred_at: toApiDateTime(e.target.value) }) }))
    ),
    h("div", { className: "actions" }, h("button", { className: "button", onClick: saveEdit }, "Save edit"), h("button", { className: "button secondary", onClick: cancel }, "Cancel"))
  );
}

function SummaryView(props) {
  const summaryBusy = props.busyAction === "summary";
  return h("section", { className: `surface wide-surface ${summaryBusy ? "working" : ""}` },
    h("div", { className: "section-head" }, h("div", null, h("h3", null, "Visit summary"), h("p", null, "Generate recorded facts for a doctor visit.")), h("span", { className: "pill warn" }, `${props.summary?.sources?.length || 0} sources`)),
    h("div", { className: "two-col" },
      h("div", null, h("label", null, "From date"), h("input", { type: "date", value: props.summaryFromDate, onChange: (e) => props.setSummaryFromDate(e.target.value) })),
      h("div", null, h("label", null, "To date"), h("input", { type: "date", value: props.summaryToDate, onChange: (e) => props.setSummaryToDate(e.target.value) }))
    ),
    h("div", { className: "actions" },
      h(BusyButton, {
        className: "button",
        onClick: props.generateSummary,
        busy: summaryBusy,
        label: "Generate summary",
        busyLabel: "Generating...",
      }),
      h("button", { className: "button secondary", onClick: props.copySummary, disabled: !props.summary || summaryBusy }, "Copy")
    ),
    summaryBusy ? h(LoadingState, { text: "Preparing visit summary..." }) : null,
    props.summary ? h("div", { className: "answer-block" }, h("p", null, props.summary.summary), h("div", { className: "source-list" }, props.summary.sources.map((source) => h("div", { className: "source", key: source.id || source.text }, h("small", null, displayDateTime(source.occurred_at)), h("div", null, source.text))))) : h("div", { className: "empty-state" }, "Choose a date range and generate a visit summary.")
  );
}

function BusyButton({ className, onClick, busy, disabled, label, busyLabel }) {
  return h("button", {
    className: `${className || "button"} ${busy ? "is-busy" : ""}`,
    onClick,
    disabled: disabled || busy,
  },
    busy ? h("span", { className: "spinner", "aria-hidden": "true" }) : null,
    busy ? busyLabel : label
  );
}

function LoadingState({ text }) {
  return h("div", { className: "loading-state" },
    h("span", { className: "spinner", "aria-hidden": "true" }),
    h("span", null, text)
  );
}

function loadSubjects() {
  try {
    const saved = JSON.parse(localStorage.getItem(SUBJECTS_STORAGE_KEY) || "[]");
    const validSaved = Array.isArray(saved)
      ? saved.filter((item) => item?.id && item?.name && item?.persona)
      : [];
    const merged = [...defaultSubjects];
    for (const item of validSaved) {
      if (!merged.some((existing) => existing.id === item.id)) {
        merged.push(item);
      }
    }
    return merged;
  } catch {
    return defaultSubjects;
  }
}

function slugify(name) {
  return name
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "") || "person";
}

function uniqueSubjectId(base, subjects) {
  let id = base;
  let suffix = 2;
  while (subjects.some((item) => item.id === id)) {
    id = `${base}-${suffix}`;
    suffix += 1;
  }
  return id;
}

createRoot(document.getElementById("root")).render(h(App));
