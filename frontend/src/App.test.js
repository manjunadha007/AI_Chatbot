import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, cleanup } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom/vitest";
import App from "./App.js";

function mockFetch(impl) {
  global.fetch = vi.fn(impl);
}

afterEach(cleanup);

beforeEach(() => {
  window.HTMLElement.prototype.scrollIntoView = vi.fn();
});

describe("Chatbot UI", () => {
  it("shows header, welcome message and input", () => {
    render(<App />);
    expect(screen.getByText("PROF. G. RAM REDDY CENTRE FOR DISTANCE EDUCATION")).toBeInTheDocument();
    expect(screen.getByText(/Welcome to PGRRCDE/)).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Type your question...")).toBeInTheDocument();
  });

  it("sends a suggested question when its chip is clicked, then hides the chips", async () => {
    mockFetch(async () => ({ json: async () => ({ reply: "Rs. 15,000 per year" }) }));
    render(<App />);
    await userEvent.click(screen.getByRole("button", { name: "What is the MCA fee?" }));
    expect(await screen.findByText("Rs. 15,000 per year")).toBeInTheDocument();
    const body = JSON.parse(fetch.mock.calls[0][1].body);
    expect(body.messages[0].content).toBe("What is the MCA fee?");
    expect(screen.queryByRole("button", { name: "What is the MCA fee?" })).not.toBeInTheDocument();
  });

  it("does not send an empty message", async () => {
    mockFetch(async () => ({ json: async () => ({ reply: "x" }) }));
    render(<App />);
    await userEvent.click(screen.getByRole("button", { name: "Send" }));
    expect(fetch).not.toHaveBeenCalled();
  });

  it("sends the question, shows typing, then the reply", async () => {
    let resolve;
    mockFetch(() => new Promise((r) => (resolve = r)));
    render(<App />);
    await userEvent.type(screen.getByPlaceholderText("Type your question..."), "MCA fee?{Enter}");
    expect(screen.getByText("MCA fee?")).toBeInTheDocument();
    expect(screen.getByText("Typing...")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Type your question...")).toBeDisabled();

    resolve({ json: async () => ({ reply: "Rs. 15,000 per year" }) });
    expect(await screen.findByText("Rs. 15,000 per year")).toBeInTheDocument();
    expect(screen.queryByText("Typing...")).not.toBeInTheDocument();

    const body = JSON.parse(fetch.mock.calls[0][1].body);
    expect(fetch.mock.calls[0][0]).toBe("/api/chat");
    expect(body.messages).toEqual([{ role: "user", content: "MCA fee?" }]); // welcome message excluded
  });

  it("sends conversation history on follow-up", async () => {
    mockFetch(async () => ({ json: async () => ({ reply: "answer" }) }));
    render(<App />);
    const box = screen.getByPlaceholderText("Type your question...");
    await userEvent.type(box, "first{Enter}");
    await screen.findByText("answer");
    await userEvent.type(box, "second{Enter}");
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
    const body = JSON.parse(fetch.mock.calls[1][1].body);
    expect(body.messages.map((m) => m.content)).toEqual(["first", "answer", "second"]);
  });

  it("shows the backend error message", async () => {
    mockFetch(async () => ({ json: async () => ({ error: "model down" }) }));
    render(<App />);
    await userEvent.type(screen.getByPlaceholderText("Type your question..."), "hi{Enter}");
    expect(await screen.findByText("Error: model down")).toBeInTheDocument();
  });

  it("shows an error when the backend is unreachable", async () => {
    mockFetch(async () => {
      throw new Error("network");
    });
    render(<App />);
    await userEvent.type(screen.getByPlaceholderText("Type your question..."), "hi{Enter}");
    expect(await screen.findByText("Error: backend not reachable.")).toBeInTheDocument();
  });
});
