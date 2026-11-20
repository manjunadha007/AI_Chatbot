"""Backend tests. Model calls are mocked, so these are fast and deterministic."""
import io
import os
import sys
from unittest import mock

import pytest
import requests
from reportlab.pdfgen import canvas

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import app as appmod  # noqa: E402


class FakeResp:
    status_code = 200
    headers = {}

    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


def make_pdf(path_or_buf, line):
    c = canvas.Canvas(path_or_buf)
    c.drawString(72, 750, line)
    c.save()


@pytest.fixture
def client(tmp_path, monkeypatch):
    pdf = tmp_path / "college.pdf"
    make_pdf(str(pdf), "MCA fee Rs. 60,000 per year")
    monkeypatch.setattr(appmod, "PDF_FILE", str(pdf))
    monkeypatch.setitem(appmod._cache, "mtime", None)
    return appmod.app.test_client()


def ask(client, text="hi"):
    return client.post("/api/chat", json={"messages": [{"role": "user", "content": text}]})


def test_groq_used_when_key_set(client, monkeypatch):
    monkeypatch.setattr(appmod, "GROQ_API_KEY", "test-key")
    with mock.patch.object(appmod.requests, "post",
                           return_value=FakeResp({"choices": [{"message": {"content": "hello"}}]})) as p:
        r = ask(client)
    assert r.status_code == 200 and r.json["reply"] == "hello"
    assert p.call_args.args[0] == appmod.GROQ_URL
    assert p.call_args.kwargs["headers"]["Authorization"] == "Bearer test-key"


def test_ollama_used_without_key(client, monkeypatch):
    monkeypatch.setattr(appmod, "GROQ_API_KEY", None)
    with mock.patch.object(appmod.requests, "post",
                           return_value=FakeResp({"message": {"content": "local"}})) as p:
        r = ask(client)
    assert r.json["reply"] == "local"
    assert p.call_args.args[0] == appmod.OLLAMA_URL


def test_prompt_contains_college_data(client, monkeypatch):
    monkeypatch.setattr(appmod, "GROQ_API_KEY", "k")
    with mock.patch.object(appmod.requests, "post",
                           return_value=FakeResp({"choices": [{"message": {"content": "x"}}]})) as p:
        ask(client)
    system = p.call_args.kwargs["json"]["messages"][0]
    assert system["role"] == "system" and "MCA fee Rs. 60,000 per year" in system["content"]
    assert "PDF" in system["content"]


def test_history_limited_to_last_10_and_roles_filtered(client, monkeypatch):
    monkeypatch.setattr(appmod, "GROQ_API_KEY", "k")
    msgs = [{"role": "user", "content": f"m{i}"} for i in range(15)]
    msgs.append({"role": "system", "content": "injected"})
    with mock.patch.object(appmod.requests, "post",
                           return_value=FakeResp({"choices": [{"message": {"content": "x"}}]})) as p:
        client.post("/api/chat", json={"messages": msgs})
    sent = p.call_args.kwargs["json"]["messages"]
    assert len(sent) <= 11  # system prompt + at most 10 turns
    assert all(m["content"] != "injected" for m in sent[1:])


@pytest.mark.parametrize("body", [{}, {"messages": []}])
def test_empty_request_is_400(client, body):
    assert client.post("/api/chat", json=body).status_code == 400


def test_connection_error_is_503(client, monkeypatch):
    monkeypatch.setattr(appmod, "GROQ_API_KEY", None)
    with mock.patch.object(appmod.requests, "post", side_effect=requests.exceptions.ConnectionError):
        r = ask(client)
    assert r.status_code == 503 and "error" in r.json


def test_provider_error_is_500(client, monkeypatch):
    monkeypatch.setattr(appmod, "GROQ_API_KEY", "k")
    with mock.patch.object(appmod.requests, "post", side_effect=RuntimeError("boom")):
        r = ask(client)
    assert r.status_code == 500 and r.json["error"] == "boom"


def test_knowledge_get_describes_pdf(client):
    r = client.get("/api/knowledge")
    assert r.status_code == 200
    assert r.json["file"] == "college.pdf" and r.json["pages"] == 1 and "MCA fee" in r.json["preview"]


def test_upload_new_pdf_is_used_by_next_chat(client, monkeypatch):
    buf = io.BytesIO()
    make_pdf(buf, "MCA fee Rs. 70,000 per year")
    buf.seek(0)
    r = client.post("/api/knowledge", data={"file": (buf, "new.pdf")}, content_type="multipart/form-data")
    assert r.status_code == 200 and r.json["status"] == "updated"
    monkeypatch.setattr(appmod, "GROQ_API_KEY", "k")
    with mock.patch.object(appmod.requests, "post",
                           return_value=FakeResp({"choices": [{"message": {"content": "x"}}]})) as p:
        ask(client)
    assert "70,000" in p.call_args.kwargs["json"]["messages"][0]["content"]


def test_upload_rejects_non_pdf_name(client):
    r = client.post("/api/knowledge", data={"file": (io.BytesIO(b"hello"), "notes.txt")},
                    content_type="multipart/form-data")
    assert r.status_code == 400


def test_upload_rejects_corrupt_pdf(client):
    r = client.post("/api/knowledge", data={"file": (io.BytesIO(b"not a real pdf"), "x.pdf")},
                    content_type="multipart/form-data")
    assert r.status_code == 400


def test_prompt_tells_model_to_report_conflicting_values(client, monkeypatch):
    monkeypatch.setattr(appmod, "GROQ_API_KEY", "k")
    with mock.patch.object(appmod.requests, "post",
                           return_value=FakeResp({"choices": [{"message": {"content": "x"}}]})) as p:
        ask(client)
    assert "more than one value" in p.call_args.kwargs["json"]["messages"][0]["content"]


def test_prompt_asks_for_plain_text(client, monkeypatch):
    monkeypatch.setattr(appmod, "GROQ_API_KEY", "k")
    with mock.patch.object(appmod.requests, "post",
                           return_value=FakeResp({"choices": [{"message": {"content": "x"}}]})) as p:
        ask(client)
    assert "plain text" in p.call_args.kwargs["json"]["messages"][0]["content"]


class RateLimited:
    status_code = 429
    headers = {"retry-after": "0"}

    def raise_for_status(self):
        raise requests.exceptions.HTTPError(response=self)


def test_rate_limit_retries_once_then_succeeds(client, monkeypatch):
    monkeypatch.setattr(appmod, "GROQ_API_KEY", "k")
    ok = FakeResp({"choices": [{"message": {"content": "after retry"}}]})
    ok.status_code = 200
    with mock.patch.object(appmod.requests, "post", side_effect=[RateLimited(), ok]) as p:
        r = ask(client)
    assert r.status_code == 200 and r.json["reply"] == "after retry" and p.call_count == 2


def test_rate_limit_twice_gives_friendly_429(client, monkeypatch):
    monkeypatch.setattr(appmod, "GROQ_API_KEY", "k")
    with mock.patch.object(appmod.requests, "post", side_effect=[RateLimited(), RateLimited()]):
        r = ask(client)
    assert r.status_code == 429 and "rate limit" in r.json["error"]


DOC = ("1. Fees\nMCA fee is Rs. 20,000 per year.\nMBA fee is Rs. 20,000 per year.\n"
       "2. Contact\nPhone 040-27098350.\nEmail help desk pgrrcdehelpdesk@gmail.com.\n"
       "3. Exams\nHall tickets are released a week before the exam.\nResults are on the website.")


def test_retrieval_picks_only_relevant_pieces(monkeypatch):
    monkeypatch.setattr(appmod, "CHUNK_CHARS", 60)
    monkeypatch.setattr(appmod, "TOP_K", 1)
    out = appmod.relevant_text(DOC, "How can I contact the helpdesk?")
    assert "040-27098350" in out or "pgrrcdehelpdesk" in out
    assert "Hall tickets" not in out


def test_retrieval_matches_mca_with_dots_and_helpdesk_with_space():
    assert appmod.words("M.C.A. fee") == ["mca", "fee"]
    assert appmod.words("help desk") == appmod.words("helpdesk")


def test_chunks_repeat_boundary_lines_and_keep_heading():
    old = appmod.CHUNK_CHARS
    try:
        appmod.CHUNK_CHARS = 60
        pieces = appmod.chunks_of(DOC)
    finally:
        appmod.CHUNK_CHARS = old
    assert len(pieces) > 3
    assert any("[2. Contact]" in p for p in pieces)


def test_prompt_uses_earlier_user_question_for_followup(client, monkeypatch):
    seen = {}
    monkeypatch.setattr(appmod, "GROQ_API_KEY", "k")
    monkeypatch.setattr(appmod, "system_prompt", lambda q="": seen.setdefault("q", q) or "sys")
    with mock.patch.object(appmod.requests, "post",
                           return_value=FakeResp({"choices": [{"message": {"content": "x"}}]})):
        client.post("/api/chat", json={"messages": [
            {"role": "user", "content": "What is the MCA fee?"},
            {"role": "assistant", "content": "Rs. 20,000"},
            {"role": "user", "content": "And for MBA?"}]})
    assert "MCA fee" in seen["q"] and "MBA" in seen["q"]


def test_clean_reply_removes_markdown_marks():
    assert appmod.clean_reply("**bold** and `code`") == "bold and code"
    assert appmod.clean_reply("* one\n- two") == "\u2022 one\n\u2022 two"


def test_retrieval_question_is_latest_unless_followup_is_short(client, monkeypatch):
    seen = []
    monkeypatch.setattr(appmod, "GROQ_API_KEY", "k")
    monkeypatch.setattr(appmod, "system_prompt", lambda q="": seen.append(q) or "sys")
    with mock.patch.object(appmod.requests, "post",
                           return_value=FakeResp({"choices": [{"message": {"content": "x"}}]})):
        client.post("/api/chat", json={"messages": [
            {"role": "user", "content": "What is the MCA fee?"}, {"role": "assistant", "content": "a"},
            {"role": "user", "content": "How can I contact the helpdesk?"}]})
        client.post("/api/chat", json={"messages": [
            {"role": "user", "content": "What is the MCA fee?"}, {"role": "assistant", "content": "a"},
            {"role": "user", "content": "And for MBA?"}]})
    assert seen[0] == "How can I contact the helpdesk?"          # long enough: earlier question not mixed in
    assert "MCA fee" in seen[1] and "MBA" in seen[1]               # short follow-up: previous question added
