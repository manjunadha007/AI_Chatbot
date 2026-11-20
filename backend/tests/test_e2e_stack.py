"""Full-stack test: starts real Flask + Vite servers and calls the API through the Vite proxy
(the same path the browser uses). Uses the real model, so it is skipped without GROQ_API_KEY."""
import os
import subprocess
import sys
import time

import pytest
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(HERE, ".."))
import app as appmod  # noqa: E402

pytestmark = pytest.mark.skipif(not appmod.GROQ_API_KEY, reason="GROQ_API_KEY not set")


def wait(url, tries=40):
    for _ in range(tries):
        try:
            return requests.get(url, timeout=2)
        except requests.RequestException:
            time.sleep(0.5)
    raise RuntimeError("server did not start: " + url)


@pytest.fixture(scope="module")
def stack():
    flask = subprocess.Popen([sys.executable, "app.py"], cwd=os.path.join(ROOT, "backend"),
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    vite = subprocess.Popen("npm run dev", cwd=os.path.join(ROOT, "frontend"), shell=True,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        wait("http://localhost:5000/api/knowledge")
        wait("http://localhost:5173/")
        yield
    finally:
        for p in (flask, vite):
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) if os.name == "nt" else p.kill()


def test_page_served(stack):
    r = requests.get("http://localhost:5173/")
    assert "PGRRCDE Enquiry Chatbot" in r.text
    assert requests.get("http://localhost:5173/src/App.js").status_code == 200


def test_chat_through_frontend_proxy(stack):
    r = requests.post("http://localhost:5173/api/chat", timeout=90,
                      json={"messages": [{"role": "user", "content": "What is the MCA fee?"}]})
    assert r.status_code == 200 and "20,000" in r.json()["reply"]
