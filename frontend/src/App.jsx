import { useState, useRef, useEffect } from "react";
import "./App.css";

const LEVELS = ["JLPT N5", "JLPT N4", "JLPT N3", "JLPT N2", "JLPT N1"];
const LANGS = ["English", "Indonesian"];

function Bubble({ m, onSpeak }) {
  if (m.role === "user") {
    return <div className="bubble user">{m.content}</div>;
  }
  const [main, ...rest] = m.content.split("✏️");
  return (
    <div className="bubble assistant">
      <div>{main.trim()}</div>
      {rest.length > 0 && <div className="correction">✏️{rest.join("✏️")}</div>}
      <button
        type="button"
        className="speak"
        onClick={() => onSpeak(m.content)}
      >
        🔊
      </button>
    </div>
  );
}

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [level, setLevel] = useState("JLPT N5");
  const [lang, setLang] = useState("English");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [autoSpeak, setAutoSpeak] = useState(true);
  const [recording, setRecording] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const recorderRef = useRef(null);
  const chunksRef = useRef([]);
  const audioRef = useRef(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function send(e) {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    const next = [...messages, { role: "user", content: text }];
    setMessages(next);
    setInput("");
    setLoading(true);
    setError("");

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: next, level, lang }),
      });
      if (!res.ok) throw new Error(`Server error (${res.status})`);
      const data = await res.json();
      setMessages([...next, { role: "assistant", content: data.reply }]);
      if (autoSpeak) speak(data.reply);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function speak(text) {
    try {
      const res = await fetch("/api/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      if (!res.ok) throw new Error(`Voice error (${res.status})`);
      const url = URL.createObjectURL(await res.blob());
      audioRef.current?.pause();
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => URL.revokeObjectURL(url);
      await audio.play();
    } catch (err) {
      setError(err.message);
    }
  }

  async function toggleRecording() {
    if (recording) {
      recorderRef.current?.stop();
      return;
    }
    try {
      audioRef.current?.pause(); // don't record the tutor's own voice
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        setRecording(false);
        const blob = new Blob(chunksRef.current, {
          type: recorder.mimeType || "audio/webm",
        });
        await transcribe(blob);
      };
      recorder.start();
      recorderRef.current = recorder;
      setRecording(true);
      setError("");
    } catch {
      setError("Microphone access was denied or is unavailable.");
    }
  }

  async function transcribe(blob) {
    setTranscribing(true);
    try {
      const form = new FormData();
      form.append("audio", blob, "speech.webm");
      const res = await fetch("/api/transcribe", {
        method: "POST",
        body: form,
      });
      if (!res.ok) throw new Error(`Transcription error (${res.status})`);
      const data = await res.json();
      if (!data.text) {
        setError(
          "I couldn't hear anything. Try again, a bit closer to the mic.",
        );
      } else {
        setInput(data.text); // you can check and edit it before sending
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setTranscribing(false);
    }
  }

  return (
    <div className="app">
      <header>
        <h1>日本語 会話パートナー</h1>
        <div className="controls">
          <label>
            <input
              type="checkbox"
              checked={autoSpeak}
              onChange={(e) => setAutoSpeak(e.target.checked)}
            />{" "}
            Voice
          </label>
          <select value={level} onChange={(e) => setLevel(e.target.value)}>
            {LEVELS.map((l) => (
              <option key={l}>{l}</option>
            ))}
          </select>
          <select value={lang} onChange={(e) => setLang(e.target.value)}>
            {LANGS.map((l) => (
              <option key={l}>{l}</option>
            ))}
          </select>
          <button type="button" onClick={() => setMessages([])}>
            New chat
          </button>
        </div>
      </header>

      <main>
        {messages.length === 0 && (
          <p className="hint">
            こんにちは！ Say something in Japanese to start.
          </p>
        )}
        {messages.map((m, i) => (
          <Bubble key={i} m={m} onSpeak={speak} />
        ))}
        {loading && <div className="bubble assistant typing">…</div>}
        {error && <div className="error">{error}</div>}
        <div ref={bottomRef} />
      </main>

      <form onSubmit={send}>
        <button
          type="button"
          className={recording ? "mic recording" : "mic"}
          onClick={toggleRecording}
          disabled={loading || transcribing}
          title={recording ? "Stop recording" : "Speak"}
        >
          {recording ? "⏹" : "🎤"}
        </button>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={
            recording
              ? "Listening…"
              : transcribing
                ? "Transcribing…"
                : "日本語で書いてみましょう"
          }
          disabled={loading || transcribing}
        />
        <button disabled={loading || transcribing || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}
