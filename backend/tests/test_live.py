"""Live tests against the real Groq model. Skipped automatically if no GROQ_API_KEY.
LLM wording varies, so assertions check facts, not exact sentences."""
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import app as appmod  # noqa: E402

pytestmark = pytest.mark.skipif(not appmod.GROQ_API_KEY, reason="GROQ_API_KEY not set")


@pytest.fixture(autouse=True)
def pace_requests():
    """Free tier allows 8,000 tokens per minute; space the live requests out."""
    yield
    time.sleep(6)


@pytest.fixture(scope="module")
def client():
    return appmod.app.test_client()


def chat(client, turns):
    for _ in range(3):  # the free tier may still say "busy" (429) after the app's own retry
        r = client.post("/api/chat", json={"messages": turns})
        if r.status_code != 429:
            break
        time.sleep(20)
    assert r.status_code == 200, r.json
    return r.json["reply"].replace(" ", " ").replace(" ", " ")  # models use special spaces


def test_fee_question(client):
    reply = chat(client, [{"role": "user", "content": "What is the MCA fee?"}])
    assert "20,000" in reply and "15,000" in reply  # website and 2024-25 notification differ; both reported


def test_eligibility_question(client):
    # LLM wording varies between runs, so allow up to 3 attempts for the key facts to appear.
    for _ in range(3):
        reply = chat(client, [{"role": "user", "content": "What is the eligibility for MCA?"}])
        if ("Mathematics" in reply or "Maths" in reply) and "50" in reply:
            return
    raise AssertionError("eligibility facts missing: " + reply)


def test_followup_uses_context(client):
    reply = chat(client, [
        {"role": "user", "content": "What is the MCA fee?"},
        {"role": "assistant", "content": "MCA fee is Rs. 20,000 per year on the website."},
        {"role": "user", "content": "And for MBA?"},
    ])
    assert "20,000" in reply


def test_admission_dates(client):
    reply = chat(client, [{"role": "user", "content": "What are the admission dates for 2026-27?"}])
    assert "11 September" in reply or "September" in reply


def test_contact_details(client):
    reply = chat(client, [{"role": "user", "content": "What is the enquiry phone number?"}])
    assert "27098350" in reply


def test_out_of_scope_declines(client):
    reply = chat(client, [{"role": "user", "content": "Who won the cricket world cup?"}]).lower()
    assert any(w in reply for w in ("not sure", "don't know", "do not know", "contact", "office"))


def test_administration_from_pdf(client):
    reply = chat(client, [{"role": "user", "content": "Who is the Director of the centre?"}])
    assert "Bhatracharyulu" in reply


def test_entrance_exam_date_from_pdf(client):
    reply = chat(client, [{"role": "user", "content": "When was the MBA MCA entrance exam in 2026?"}])
    assert "27" in reply and "September" in reply
