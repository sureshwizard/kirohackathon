import React, { useEffect, useRef, useState } from "react";
import axios from "axios";
import { EXPENSES_API } from "../config";

type Msg = {
  id: string;
  from: "user" | "assistant";
  text: string;
  time: string;
  status?: "sending" | "sent" | "error";
};

function nowTime(): string {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function uid(prefix = "") {
  return prefix + Math.random().toString(36).slice(2, 9);
}

export default function Chat(): JSX.Element {
  const [messages, setMessages] = useState<Msg[]>([
    {
      id: uid("m_"),
      from: "assistant",
      text: "Hi — ask me about your expenses. Try: “How much I spent on coffee this month?”",
      time: nowTime(),
    },
  ]);
  const [text, setText] = useState("");
  const [useAI, setUseAI] = useState(false);
  const [loading, setLoading] = useState(false);
  const [listening, setListening] = useState(false);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    // auto-scroll to bottom when messages change
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const appendMessage = (m: Msg) => setMessages((prev) => [...prev, m]);

  const postToServer = async (txt: string) => {
    return axios.post(`${EXPENSES_API}/api/v1/chat`, {
      message: txt,
      text: txt,
      use_ai: useAI,
    });
  };

  const send = async () => {
    const t = text.trim();
    if (!t) return;

    const id = uid("u_");
    const userMsg: Msg = { id, from: "user", text: t, time: nowTime(), status: "sent" };
    appendMessage(userMsg);
    setText("");
    setLoading(true);

    const botId = uid("b_");
    const pendingBot: Msg = {
      id: botId,
      from: "assistant",
      text: "Thinking...",
      time: nowTime(),
      status: "sending",
    };
    appendMessage(pendingBot);

    try {
      const res = await postToServer(t);
      const reply =
        res?.data?.reply ??
        res?.data?.message ??
        (typeof res?.data === "string" ? res.data : JSON.stringify(res?.data));

      setMessages((prev) =>
        prev.map((m) =>
          m.id === botId ? { ...m, text: String(reply), status: "sent", time: nowTime() } : m
        )
      );

      speak(String(reply));
    } catch (err: any) {
      console.error("chat error", err);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === botId
            ? { ...m, text: "Error contacting server", status: "error", time: nowTime() }
            : m
        )
      );
    } finally {
      setLoading(false);
      const el = document.getElementById("chat-input") as HTMLInputElement | null;
      el?.focus();
    }
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!loading) send();
    }
  };

  const speak = (txt: string) => {
    try {
      if (!("speechSynthesis" in window)) return;
      window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(txt);
      u.lang = "en-IN";
      window.speechSynthesis.speak(u);
    } catch (e) {
      console.warn("speak error", e);
    }
  };

  const startListening = () => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) return alert("Speech recognition not supported in this browser.");

    if (listening && recognitionRef.current) {
      recognitionRef.current.stop();
      return;
    }

    const r = new SpeechRecognition();
    recognitionRef.current = r;
    r.lang = "en-IN";
    r.interimResults = false;
    r.maxAlternatives = 1;
    setListening(true);

    r.onresult = (ev: any) => {
      const transcript = ev.results[0][0].transcript;
      setText(transcript);
      setListening(false);
    };
    r.onerror = (ev: any) => {
      console.error("speech recognition error", ev);
      setListening(false);
    };
    r.onend = () => {
      setListening(false);
    };
    r.start();
  };

  const bubbleStyle = (from: "user" | "assistant"): React.CSSProperties => ({
    maxWidth: "78%",
    padding: "10px 12px",
    borderRadius: 12,
    whiteSpace: "pre-wrap",
    lineHeight: 1.35,
    boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
    background: from === "user" ? "#3b82f6" : "#f3f4f6",
    color: from === "user" ? "#fff" : "#111",
  });

  return (
    <div
      style={{
        maxWidth: 880,
        margin: "1.25rem auto",
        fontFamily:
          "Inter, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 12,
        }}
      >
        <div>
          <h2 style={{ margin: 0 }}>Chat Assistant</h2>
          <div style={{ color: "#666", marginTop: 6 }}>
            Ask questions about your expenses or use AI for summaries.
          </div>
        </div>

        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <label style={{ display: "flex", gap: 8, alignItems: "center", color: "#444" }}>
            <input
              type="checkbox"
              checked={useAI}
              onChange={(e) => setUseAI(e.target.checked)}
            />{" "}
            Use AI
          </label>
          <button
            onClick={() => {
              const sample = "Summarize my spending this month.";
              setText(sample);
            }}
            style={btnStyle}
            aria-label="Use AI sample"
          >
            Suggest
          </button>
        </div>
      </div>

      <div style={{ display: "flex", gap: 12 }}>
        {/* Left column: messages */}
        <div style={{ flex: 1 }}>
          <div
            style={{
              borderRadius: 10,
              border: "1px solid #eee",
              overflow: "hidden",
              background: "#fff",
            }}
          >
            <div
              ref={scrollRef}
              style={{
                maxHeight: 520,
                overflow: "auto",
                padding: 12,
                display: "flex",
                flexDirection: "column",
                gap: 10,
              }}
            >
              {messages.map((m) => (
                <div
                  key={m.id}
                  style={{
                    display: "flex",
                    justifyContent: m.from === "user" ? "flex-end" : "flex-start",
                    alignItems: "flex-end",
                    gap: 10,
                  }}
                >
                  {m.from === "assistant" && (
                    <div
                      style={{
                        width: 36,
                        height: 36,
                        borderRadius: 10,
                        background: "#eef2ff",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        color: "#334155",
                        fontWeight: 700,
                      }}
                    >
                      AI
                    </div>
                  )}

                  <div style={bubbleStyle(m.from)}>
                    <div style={{ fontSize: 14 }}>{m.text}</div>
                    <div
                      style={{
                        marginTop: 6,
                        fontSize: 11,
                        color:
                          m.from === "user" ? "rgba(255,255,255,0.75)" : "#666",
                        textAlign: "right",
                      }}
                    >
                      {m.time}{" "}
                      {m.status === "sending"
                        ? " • sending…"
                        : m.status === "error"
                        ? " • failed"
                        : ""}
                    </div>
                  </div>

                  {m.from === "user" && (
                    <div
                      style={{
                        width: 36,
                        height: 36,
                        borderRadius: 10,
                        background: "#D1FAE5",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        color: "#065f46",
                        fontWeight: 700,
                      }}
                    >
                      U
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Input area */}
          <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
            <input
              id="chat-input"
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder='Ask: "How much I spent on coffee this month?"'
              style={{
                flex: 1,
                padding: "12px 14px",
                borderRadius: 10,
                border: "1px solid #e6e9ee",
                fontSize: 14,
                outline: "none",
              }}
              disabled={loading}
            />

            <button onClick={startListening} title="Record" style={microBtnStyle(listening)}>
              {listening ? "Listening…" : "🎤"}
            </button>

            <button
              onClick={send}
              disabled={loading || !text.trim()}
              style={primaryBtnStyle}
            >
              {loading ? "Sending…" : "Send"}
            </button>
          </div>
        </div>

        {/* Right column: quick actions + tips */}
        <div style={{ width: 260 }}>
          <div
            style={{
              background: "#fff",
              border: "1px solid #eee",
              borderRadius: 8,
              padding: 12,
            }}
          >
            <h4 style={{ marginTop: 0, marginBottom: 8 }}>Quick prompts</h4>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <button
                style={chipBtn}
                onClick={() => {
                  setText("How much I spent on coffee this month?");
                }}
              >
                How much on coffee
              </button>
              <button
                style={chipBtn}
                onClick={() => {
                  setText("Show expenses by category this month.");
                }}
              >
                Category summary
              </button>
              <button
                style={chipBtn}
                onClick={() => {
                  setText("Top 5 merchants I spent with this month");
                }}
              >
                Top merchants
              </button>
              <button
                style={chipBtn}
                onClick={() => {
                  setText("Any large transactions above 1000 this month?");
                }}
              >
                Large transactions
              </button>
            </div>

            <hr
              style={{ margin: "12px 0", border: "none", borderTop: "1px solid #f0f0f0" }}
            />

            <h5 style={{ margin: "6px 0 8px 0" }}>Tips</h5>
            <div style={{ color: "#666", fontSize: 13, lineHeight: 1.4 }}>
              You can toggle <strong>Use AI</strong> to run more sophisticated prompts. Use
              the microphone to dictate questions.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* styles */
const btnStyle: React.CSSProperties = {
  background: "#f3f4f6",
  border: "1px solid #e6e9ee",
  padding: "8px 10px",
  borderRadius: 8,
  cursor: "pointer",
};

const primaryBtnStyle: React.CSSProperties = {
  background: "#2563eb",
  color: "#fff",
  border: "none",
  padding: "10px 14px",
  borderRadius: 10,
  cursor: "pointer",
  fontWeight: 600,
};

const chipBtn: React.CSSProperties = {
  textAlign: "left",
  background: "#fafafa",
  border: "1px solid #f0f0f0",
  padding: "8px 10px",
  borderRadius: 8,
  cursor: "pointer",
};

const microBtnStyle = (on: boolean): React.CSSProperties => ({
  background: on ? "#fee2e2" : "#fff",
  border: "1px solid #e6e9ee",
  padding: "10px",
  borderRadius: 10,
  cursor: "pointer",
});
