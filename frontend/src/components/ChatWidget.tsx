// src/components/ChatWidget.tsx
import React, { useEffect, useRef, useState } from "react";
import axios from "axios";
import { CHAT_API } from "../config";

type ChatMsg = { role: "user" | "ai"; text: string; ts?: string };

export default function ChatWidget(): JSX.Element {
  const [msgs, setMsgs] = useState<ChatMsg[]>([
    { role: "ai", text: 'Hi — ask me about your expenses. Try: "How much I spent on coffee this month?"', ts: timestamp() }
  ]);
  const [input, setInput] = useState("");
  const [useAi, setUseAi] = useState(true);
  const [sending, setSending] = useState(false);
  const messagesRef = useRef<HTMLDivElement | null>(null);

  // microphone
  const [listening, setListening] = useState(false);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    if ("SpeechRecognition" in window || (window as any).webkitSpeechRecognition) {
      const SpeechRec = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      const r = new SpeechRec();
      r.lang = "en-IN";
      r.interimResults = false;
      r.maxAlternatives = 1;
      r.onresult = (ev: any) => {
        const txt = ev.results[0][0].transcript;
        setInput(txt);
        sendChat(txt);
      };
      r.onend = () => { setListening(false); };
      r.onerror = () => { setListening(false); };
      recognitionRef.current = r;
    }
  }, []);

  useEffect(() => {
    // auto-scroll
    const el = messagesRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [msgs]);

  function timestamp() {
    return new Date().toLocaleTimeString();
  }

  async function sendChat(text?: string) {
    const content = (text ?? input).trim();
    if (!content) return;
    setInput("");
    const userMsg: ChatMsg = { role: "user", text: content, ts: timestamp() };
    setMsgs((m) => [...m, userMsg]);
    // placeholder for AI
    const placeholder: ChatMsg = { role: "ai", text: useAi ? "Thinking..." : "Searching...", ts: timestamp() };
    setMsgs((m) => [...m, placeholder]);
    setSending(true);

    try {
      const body = {
        messages: [{ role: "user", content }],
        use_ai: useAi,
      };

      const res = await axios.post(CHAT_API, body, { timeout: 30000 });
      // backend expected to return { reply: string } or structured response
      const data = res.data || {};
      const aiText = data.reply ?? (data.total !== undefined ? `You spent ${data.total} across ${data.count ?? "N/A"} txns.` : JSON.stringify(data));
      // replace last AI placeholder
      setMsgs((m) => {
        const copy = m.slice(0, -1);
        copy.push({ role: "ai", text: aiText, ts: timestamp() });
        return copy;
      });
    } catch (err: any) {
      console.error(err);
      const errMsg = err?.response?.data?.detail ?? err?.message ?? "Network error";
      setMsgs((m) => {
        const copy = m.slice(0, -1);
        copy.push({ role: "ai", text: `Error: ${errMsg}`, ts: timestamp() });
        return copy;
      });
    } finally {
      setSending(false);
    }
  }

  function quick(q: string) {
    setInput(q);
    sendChat(q);
  }

  function toggleMic() {
    if (!recognitionRef.current) return;
    if (listening) {
      recognitionRef.current.stop();
      setListening(false);
    } else {
      recognitionRef.current.start();
      setListening(true);
    }
  }

  return (
    <div style={{ border: "1px solid #e6e6e6", borderRadius: 8, padding: 12, background: "#fff", maxWidth: 820 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
        <div>
          <strong>AI Chat Assistant</strong>
          <div style={{ fontSize: 12, color: "#666" }}>Ask questions about your expenses or use AI for summaries.</div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <label style={{ fontSize: 13 }}>
            <input type="checkbox" checked={useAi} onChange={(e) => setUseAi(e.target.checked)} /> Use AI
          </label>
        </div>
      </div>

      <div ref={messagesRef} style={{ maxHeight: 260, overflow: "auto", padding: 8, background: "#fafafa", borderRadius: 6 }}>
        {msgs.map((m, i) => (
          <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: m.role === "user" ? "flex-end" : "flex-start", marginBottom: 8 }}>
            <div style={{
              maxWidth: "80%",
              padding: "8px 10px",
              borderRadius: 8,
              background: m.role === "user" ? "#e6f7ff" : "#fff",
              border: m.role === "ai" ? "1px solid #eee" : undefined,
              fontSize: 14
            }}>
              {m.text}
            </div>
            <div style={{ fontSize: 11, color: "#777", marginTop: 4 }}>{m.role === "user" ? "U" : "AI"} • {m.ts}</div>
          </div>
        ))}
      </div>

      <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button type="button" onClick={() => quick("How much on coffee")} style={smallBtn}>How much on coffee</button>
          <button type="button" onClick={() => quick("Category summary")} style={smallBtn}>Category summary</button>
          <button type="button" onClick={() => quick("Top merchants")} style={smallBtn}>Top merchants</button>
          <button type="button" onClick={() => quick("Large transactions")} style={smallBtn}>Large transactions</button>
          <button type="button" onClick={() => quick("Tips")} style={smallBtn}>Tips</button>
        </div>
        <div style={{ marginLeft: "auto", display: "flex", gap: 6, alignItems: "center" }}>
          <button type="button" onClick={toggleMic} disabled={!recognitionRef.current} style={smallBtn}>
            {listening ? "Stop 🎙" : "🎙"}
          </button>
        </div>
      </div>

      <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendChat(); } }}
          placeholder='Ask: "How much I spent on coffee this month?"'
          style={{ flex: 1, padding: 10, borderRadius: 6, border: "1px solid #ccc" }}
        />
        <button onClick={() => sendChat()} disabled={sending || !input.trim()} style={{ padding: "8px 12px", borderRadius: 6 }}>Send</button>
      </div>
    </div>
  );
}

const smallBtn: React.CSSProperties = {
  padding: "6px 10px",
  borderRadius: 6,
  border: "1px solid #ddd",
  background: "#fff",
  cursor: "pointer",
};
