import React from "react";

const QUESTIONS = [
  "What is the eligibility for MCA?",
  "What is the MCA fee?",
  "What are the admission dates for 2026-27?",
  "How can I contact the helpdesk?",
];

export default function Suggestions({ onPick, disabled }) {
  return (
    <div className="chips">
      {QUESTIONS.map((q) => (
        <button key={q} type="button" disabled={disabled} onClick={() => onPick(q)}>
          {q}
        </button>
      ))}
    </div>
  );
}
