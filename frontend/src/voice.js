import React, { useState } from "react";
import { api, friendlyError } from "./api.js";

export function VoiceButton({ label = "Speak", onTranscript }) {
  const [recorder, setRecorder] = useState(null);
  const [state, setState] = useState("idle");
  const [message, setMessage] = useState("");

  async function startRecording() {
    if (!navigator.mediaDevices || !window.MediaRecorder) {
      setMessage("Voice is not supported in this browser.");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const chunks = [];
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunks.push(event.data);
      };
      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());
        setState("transcribing");
        setMessage("Transcribing...");
        try {
          const blob = new Blob(chunks, { type: mediaRecorder.mimeType || "audio/webm" });
          const formData = new FormData();
          formData.append("audio", blob, "recording.webm");
          const data = await api.transcribe(formData);
          onTranscript(data.text);
          setMessage("Transcript added. Review before continuing.");
        } catch (error) {
          setMessage(friendlyError(error));
        } finally {
          setState("idle");
        }
      };
      mediaRecorder.start();
      setRecorder(mediaRecorder);
      setState("recording");
      setMessage("Listening...");
    } catch {
      setMessage("Microphone permission was not granted.");
      setState("idle");
    }
  }

  function stopRecording() {
    if (!recorder) return;
    recorder.stop();
    setRecorder(null);
  }

  const recording = state === "recording";
  const transcribing = state === "transcribing";

  return React.createElement("div", { className: "voice-row" },
    recording ? React.createElement("span", { className: "voice-pulse" }) : null,
    React.createElement("button", {
      className: `button voice ${recording ? "danger" : transcribing ? "wait" : "ghost"}`,
      onClick: recording ? stopRecording : startRecording,
      disabled: transcribing,
    }, recording ? "Stop" : transcribing ? "Transcribing" : label),
    message ? React.createElement("span", { className: "pill" }, message) : null
  );
}
