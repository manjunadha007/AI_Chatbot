import io, math, os, re, time
import requests
from pypdf import PdfReader
from flask import Flask, request, jsonify
from flask_cors import CORS

# Load GROQ_API_KEY etc. from backend/.env if present (no extra library needed).
_env = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_env):
    for _line in open(_env, encoding="utf-8"):
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))

# If GROQ_API_KEY is set, a hosted open-source model (Llama) on Groq is used.
# Otherwise a local model served by Ollama is used.
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
# The chatbot answers from the text of this PDF (college information compiled from www.oucde.net).
PDF_FILE = os.path.join(os.path.dirname(__file__), "knowledge", "PGRRCDE_College_Information.pdf")

app = Flask(__name__)
CORS(app)


_cache = {"mtime": None, "path": None, "text": "", "pages": 0}


def pdf_text(source):
    reader = PdfReader(source)
    return "\n".join((p.extract_text() or "") for p in reader.pages), len(reader.pages)


def load_knowledge():
    """Text of the college PDF. Re-read only when the file changes, so a newly uploaded PDF applies at once."""
    mtime = os.path.getmtime(PDF_FILE)
    if _cache["mtime"] != mtime or _cache["path"] != PDF_FILE:
        _cache["text"], _cache["pages"] = pdf_text(PDF_FILE)
        _cache["mtime"], _cache["path"] = mtime, PDF_FILE
    return _cache["text"]


CHUNK_CHARS = 700   # size of one piece of the PDF text
TOP_K = 6           # how many pieces are sent with each question
STOP = set("a an and are as at be by can do does for from how i in is it me of on or the to what when where which who will with you your my tell about please".split())


SYNONYMS = {"phone": "contact", "call": "contact", "email": "contact", "mail": "contact", "number": "contact",
            "telephone": "contact", "reach": "contact", "address": "contact", "date": "schedule", "last": "schedule"}


def words(text):
    """Lower-case keywords; dots are removed so that M.C.A. matches MCA; a trailing s is dropped; a few synonyms are mapped."""
    out = []
    for w in re.findall(r"[a-z0-9.]+", text.lower().replace("help desk", "helpdesk")):
        w = w.replace(".", "")
        if w and w not in STOP:
            w = w[:-1] if len(w) > 3 and w.endswith("s") else w
            out.append(SYNONYMS.get(w, w))
    return out


def chunks_of(text):
    """Split the PDF text into pieces of about CHUNK_CHARS. Each piece starts with its section heading and repeats
    the last two lines of the previous piece, so that a sentence cut at a boundary is still complete in one piece."""
    pieces, heading, cur, tail = [], "", [], []
    for line in text.splitlines():
        if re.match(r"^\d+\. [A-Z]", line):
            heading = line.strip()
        if sum(len(x) for x in cur) + len(line) > CHUNK_CHARS and cur:
            pieces.append(" ".join(cur))
            tail = cur[-2:]
            cur = ["[" + heading + "]"] + tail if heading else tail[:]
        cur.append(line)
    if cur:
        pieces.append(" ".join(cur))
    return pieces


def relevant_text(text, question):
    """Pick the TOP_K pieces that share the most (rarer = more important) keywords with the question."""
    pieces = chunks_of(text)
    if len(pieces) <= TOP_K:
        return "\n".join(pieces)
    counts = [words(p) for p in pieces]
    docs = [set(c) for c in counts]
    q = set(words(question))
    df = {w: sum(1 for d in docs if w in d) for w in q}
    score = [sum(math.log(1 + len(docs) / df[w]) * (1 + math.log(c.count(w))) for w in q if w in d)
             for c, d in zip(counts, docs)]
    best = sorted(sorted(range(len(pieces)), key=lambda i: -score[i])[:TOP_K])  # keep document order
    return "\n".join(pieces[i] for i in best)


def system_prompt(question=""):
    return (
        "You are a helpful college enquiry assistant. Answer ONLY using the college "
        "information (extracts from the college's PDF document) below. Keep answers short and clear. "
        "If the answer is not in the information, say you don't know and suggest contacting the college office. "
        "When you give eligibility, fees or dates, include every condition and value the information states for it. "
        "If the information gives more than one value for the same thing (for example two different fees), "
        "tell the user both values and where each comes from, and advise confirming on www.oucde.net. "
        "Reply in plain text only: no Markdown, no asterisks, no bold, no tables.\n\n"
        "COLLEGE INFORMATION (PDF extracts):\n" + relevant_text(load_knowledge(), question)
    )


def clean_reply(text):
    """Safety net: the UI shows plain text, so remove Markdown bold/code marks and turn '* ' bullets into dots."""
    text = text.replace("**", "").replace("__", "").replace("`", "")
    return re.sub(r"(?m)^\s*[*-] ", "• ", text)


def post_with_retry(*args, **kwargs):
    """POST; on HTTP 429 (free-tier rate limit) wait as long as the provider asks (max 30 s) and retry once."""
    r = requests.post(*args, **kwargs)
    if r.status_code == 429:
        try:
            wait = float(r.headers.get("retry-after", 5))
        except ValueError:
            wait = 5
        time.sleep(min(wait, 30))
        r = requests.post(*args, **kwargs)
    return r


@app.post("/api/chat")
def chat():
    body = request.get_json(silent=True) or {}
    history = body.get("messages", [])[-10:]  # last 10 turns
    if not history:
        return jsonify(error="No message provided"), 400
    users = [m["content"] for m in history if m.get("role") == "user"]
    asked = users[-1] if users else ""
    if len(words(asked)) < 2 and len(users) > 1:  # short follow-up such as "And for MBA?": add the previous question
        asked = users[-2] + " " + asked
    messages = [{"role": "system", "content": system_prompt(asked)}] + [
        {"role": m["role"], "content": m["content"]}
        for m in history
        if m.get("role") in ("user", "assistant")
    ]
    try:
        if GROQ_API_KEY:
            r = post_with_retry(
                GROQ_URL,
                headers={"Authorization": "Bearer " + GROQ_API_KEY},
                json={"model": GROQ_MODEL, "messages": messages},
                timeout=60,
            )
            r.raise_for_status()
            return jsonify(reply=clean_reply(r.json()["choices"][0]["message"]["content"]))
        r = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "messages": messages, "stream": False},
            timeout=120,
        )
        r.raise_for_status()
        return jsonify(reply=clean_reply(r.json()["message"]["content"]))
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 429:
            return jsonify(error="The model is busy (rate limit reached). Please try again in a few seconds."), 429
        return jsonify(error=str(e)), 500
    except requests.exceptions.ConnectionError:
        return jsonify(error="Cannot reach the model server. Set GROQ_API_KEY, or start Ollama and run: ollama pull " + OLLAMA_MODEL), 503
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.get("/api/knowledge")
def get_knowledge():
    text = load_knowledge()
    return jsonify(file=os.path.basename(PDF_FILE), pages=_cache["pages"], characters=len(text), preview=text[:500])


@app.post("/api/knowledge")
def upload_knowledge():
    """Admin: replace the college PDF. Multipart form field name: file."""
    f = request.files.get("file")
    if f is None or not f.filename.lower().endswith(".pdf"):
        return jsonify(error="Upload a PDF file in the form field 'file'"), 400
    data = f.read()
    try:
        text, pages = pdf_text(io.BytesIO(data))
    except Exception:
        return jsonify(error="The file is not a valid PDF"), 400
    if not text.strip():
        return jsonify(error="No text could be read from the PDF"), 400
    with open(PDF_FILE, "wb") as out:
        out.write(data)
    return jsonify(status="updated", pages=pages, characters=len(text))


if __name__ == "__main__":
    app.run(port=5000, debug=True)
