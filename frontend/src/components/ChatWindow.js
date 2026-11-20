import React, { useEffect, useRef } from "react";
import Message from "./Message.js";

export default function ChatWindow({ messages, loading }) {
  const end = useRef(null);
  useEffect(() => {
    if (end.current) end.current.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  return (
    <div className="window">
      {messages.map((m, i) => (
        <Message key={i} role={m.role} content={m.content} />
      ))}
      {loading && <div className="msg assistant">Typing...</div>}
      <div ref={end} />
    </div>
  );
}
