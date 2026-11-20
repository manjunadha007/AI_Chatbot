import React, { useState } from "react";
import Header from "./components/Header.js";
import ChatWindow from "./components/ChatWindow.js";
import Suggestions from "./components/Suggestions.js";
import ChatInput from "./components/ChatInput.js";

const WELCOME = {
  role: "assistant",
  content:
    "Welcome to PGRRCDE, Osmania University. Ask me about admissions, courses, eligibility, fees, examinations, study material or contact details.",
};

export default function App() {
  const [messages, setMessages] = useState([WELCOME]);
  const [loading, setLoading] = useState(false);

  async function send(text) {
    const next = [...messages, { role: "user", content: text }];
    setMessages(next);
    setLoading(true);
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: next.slice(1) }),
      });
      const data = await res.json();
      const reply = data.reply || "Error: " + data.error;
      setMessages([...next, { role: "assistant", content: reply }]);
    } catch {
      setMessages([...next, { role: "assistant", content: "Error: backend not reachable." }]);
    }
    setLoading(false);
  }

  return (
    <div className="page">
      <Header />
      <main className="chat">
        <ChatWindow messages={messages} loading={loading} />
        {messages.length === 1 && <Suggestions onPick={send} disabled={loading} />}
        <ChatInput onSend={send} disabled={loading} />
      </main>
      <footer>
        Student project prototype, not an official service of Osmania University. Information is taken from
        www.oucde.net; please confirm important details there.
      </footer>
    </div>
  );
}
