# PGRRCDE Enquiry Chatbot

A chat page where students and parents can ask questions about **Prof. G. Ram Reddy Centre for Distance Education (PGRRCDE), Osmania University** and get instant answers: admissions, courses, eligibility, fees, exams, classes and contact details.

> **Student project prototype.** It is not an official service of Osmania University. The information was collected from the official website (www.oucde.net) in November 2026 and can go out of date. Always confirm important details on the official website.

![Chat screen](docs/screenshots/5_followup.png)

---

## 1. What is this, in plain words?

Imagine a helpful office assistant who has read the college's information booklet and who never sleeps. You type a question like *"What is the MCA fee?"* and the assistant answers in a few seconds, in normal English.

That assistant is this project. It has three parts:

| Part | Everyday comparison | What it really is |
|---|---|---|
| **The chat page** | The reception desk where you talk | A web page (built with **React**) |
| **The brain** | An assistant who reads the booklet and writes the answer | An **AI language model** (see the glossary below) |
| **The booklet** | The college information the assistant is allowed to use | A **PDF file** (`PGRRCDE_College_Information.pdf`) |

Between the page and the brain sits a small program, the **backend** (written in Python with **Flask**), which acts like a messenger: it takes your question, finds the right pages of the booklet, hands both to the brain, and brings the answer back to the page.

### What happens when you ask a question

```
 You type a question
        |
        v
 [Chat page]  --->  [Backend messenger]  --->  [Booklet PDF]
                          |                    "find the 6 most relevant paragraphs"
                          v
                 [AI language model]
                 "answer ONLY from these paragraphs"
                          |
                          v
 You read the answer  <---  [Chat page]  <---  [Backend messenger]
```

*(Curious exactly how it finds the right part of the PDF? See **section 12** at the end for a full step-by-step explanation with real numbers.)*

Because the assistant is told to answer **only** from the booklet, it says *"I don't have that information, please contact the college office"* instead of making things up when you ask about something else (for example cricket).

---

## 2. Words you may have heard (mini glossary)

- **AI language model (LLM)**: a computer program trained on a huge amount of text so that it can read a question and write a sensible answer. ChatGPT is a famous example. This project uses an **open-source** one, which means its design is published and anyone may use it for free.
- **Cloud / hosted model**: instead of running the AI on your own laptop (which needs a strong computer), you "rent" it over the internet. This project uses a free service called **Groq** for that. Your laptop only sends the question and receives the answer.
- **Local model**: the AI runs on your own computer using a free tool called **Ollama**. No internet is needed, but it needs a decent computer and a 2 GB download.
- **API key**: like a password that tells Groq "this request comes from my free account". Keep it private.
- **Backend / frontend**: the frontend is what you see (the chat page). The backend is the hidden helper that does the work.
- **PDF "knowledge base"**: the document the assistant is allowed to read. Change the PDF and the assistant's knowledge changes. No programming is needed.
- **Hallucination**: when an AI confidently says something untrue. This project reduces it by forcing answers to come from the PDF.

---

## 3. What you need before you start

- A Windows, Mac or Linux computer with internet.
- **Python 3** (https://www.python.org/downloads/). Tick "Add Python to PATH" while installing.
- **Node.js** (https://nodejs.org/), the LTS version.
- A **free Groq account and API key** (https://console.groq.com, sign up, then "API Keys", then "Create API Key").
  *Prefer no account at all? See "Using a local model" in section 6.*

---

## 4. Setup, step by step (Windows)

Open **PowerShell** and go to the project folder (the one that contains this README).

**Step 1: Give the project your Groq key**

Copy `backend/.env.example` to a new file called `backend/.env` and put your own key in it:

```
GROQ_API_KEY=paste_your_key_here
```

This `.env` file is private and is never uploaded to GitHub.

**Step 2: Start the backend (the messenger)**

```powershell
python -m venv .venv
.venv\Scripts\activate
cd backend
python -m pip install -r requirements-dev.txt
python app.py
```

Leave this window open. It should say it is running on port 5000.

**Step 3: Start the chat page**

Open a **second** PowerShell window:

```powershell
cd frontend
npm install
npm run dev
```

**Step 4: Open the chatbot**

Go to **http://localhost:5173** in Google Chrome. Click a suggested question or type your own.

*(Mac/Linux: activate the virtual environment with `source .venv/bin/activate` instead.)*

---

## 5. Using it

- Click one of the four example questions, or type your own and press **Enter**.
- Follow-up questions work: ask *"What is the MCA fee?"* then simply *"And for MBA?"*
- If the website and an official notice disagree (for example on a fee), the chatbot tells you **both** numbers and where each came from.

---

## 6. Common tasks

### Update the college information
The assistant only knows what is in `backend/knowledge/PGRRCDE_College_Information.pdf`.

- Replace that file with a newer PDF (it must contain real text, not scanned pictures), **or**
- With the backend running, send a new PDF to `POST http://localhost:5000/api/knowledge` (form field name `file`).

The next question automatically uses the new PDF. No restart is needed.

### Using a local model instead of Groq (no account, works offline)
1. Install Ollama from https://ollama.com.
2. Run `ollama pull llama3.2:3b` (about 2 GB).
3. Remove the `GROQ_API_KEY` line from `backend/.env` (or delete the file) and restart the backend.

The project uses Groq when a key is present and Ollama when it is not.

### Change the AI model
Add `GROQ_MODEL=model_name` to `backend/.env` (default is `openai/gpt-oss-20b`). Model names offered by Groq change over time.

### Run the automated tests
```powershell
cd backend
..\.venv\Scripts\python -m pytest -v        # about a minute (some tests talk to the real AI)
cd ..\frontend
npm test
```
Currently 32 backend tests and 7 frontend tests pass. The tests that use the real AI are skipped automatically if there is no key.

---

## 7. If something goes wrong

| What you see | What it means | What to do |
|---|---|---|
| "Error: backend not reachable." | The backend window is not running | Start it (Step 2) |
| "Cannot reach the model server..." | No Groq key found and Ollama is not running | Check `backend/.env`, or start Ollama |
| "The model is busy (rate limit reached)..." | The free plan allows only a few questions per minute | Wait about 30 seconds and ask again |
| Error 401 | Wrong or missing key | Re-copy the key into `backend/.env` |
| Error 404 from groq | The AI model name was retired | Set `GROQ_MODEL` to a current one |
| Blank page | The chat page is not running | Run `npm install` then `npm run dev` |

---

## 8. What is inside the folders

```
chatbot/
  backend/
    app.py                     The messenger: reads the PDF, asks the AI, returns the answer
    knowledge/
      PGRRCDE_College_Information.pdf   The booklet (the assistant's only source of facts)
    tests/                     Automated checks for the backend
    requirements.txt           Python packages needed
    .env.example               Template for your private key file
  frontend/
    src/App.js                 The main chat page
    src/components/            Small building blocks: Header, ChatWindow, Message, ChatInput, Suggestions
    src/App.test.js            Automated checks for the page
  docs/screenshots/            Pictures of the running app
```

---

## 9. Good to know (limits and privacy)

- The AI can still occasionally give an imperfect answer. That is why the project tells it to quote the PDF and to advise confirming on the website.
- With **Groq**, the text of each question is sent to Groq's servers over the internet. Do not type personal details such as phone numbers or ID numbers. With **Ollama**, everything stays on your computer.
- The "replace the PDF" feature has no password in this prototype. Do not put it on the public internet as it is.
- The free Groq plan limits how many questions you can ask per minute.

---

## 10. Technology used

React 18 and Vite (chat page), Python and Flask (backend), pypdf (reads the PDF), Groq-hosted `openai/gpt-oss-20b` or Ollama `llama3.2:3b` (language model), pytest and Vitest (tests).

## 11. Credits

College information: public pages and notifications of www.oucde.net and www.osmania.ac.in (PGRRCDE, Osmania University). Built as an MCA mini project. This is an independent student work; the university's name and information belong to the university.

---

## 12. How the chatbot reads the PDF and finds the right parts (full detail)

This section explains, step by step and with real numbers from this project, what happens between "you press Enter" and "the AI answers". The code lives in `backend/app.py`.

### 12.0 The honest one-paragraph summary

The chatbot does **not** use "embeddings" or a "vector database". Those are a more advanced technique (explained in 12.9). Instead it uses a simpler and fully transparent method called **keyword scoring** (a cousin of the classic *TF-IDF* method). The PDF text is cut into small pieces called **chunks**; for every question each chunk is given a **score** based on how many of the question's important words it contains; the **6 best-scoring chunks** are pasted into the prompt, and the AI answers using only those. Everything below is just the detailed version of that sentence.

```
PDF  --1-->  plain text  --2-->  36 chunks  --3-->  keywords per chunk
                                                         |
 question --4--> keywords --5--> score every chunk --6--> best 6 chunks --7--> prompt --8--> AI --9--> answer
```

### 12.1 Why not just give the AI the whole PDF?

An AI model reads text in small units called **tokens** (roughly 4 characters, or three-quarters of a word). Each request has a size limit and, on the free Groq plan, a speed limit.

| Fact | Number |
|---|---|
| Size of the PDF text | 17,902 characters, about 4,900 tokens (7 pages) |
| Free Groq limit | 8,000 tokens per minute |
| Cost of sending the whole PDF with every question | about 4,900 tokens, so only about **one question per minute** |
| Cost when sending only the 6 best chunks | about 1,200 tokens, so about **5 to 6 questions per minute** |

So sending only the relevant parts is faster, cheaper, and also gives the AI less irrelevant text to get confused by.

### 12.2 Step 1: Reading the PDF (`pdf_text`, `load_knowledge`)

- The library **pypdf** opens `backend/knowledge/PGRRCDE_College_Information.pdf` and asks every page for its text (`page.extract_text()`). The pages are joined into one long text.
- This only works for PDFs that contain **real text** (like this one, created from text). A PDF that is just a scanned photo has no text to read, and the upload feature rejects it ("No text could be read from the PDF").
- The text is **cached**: the program remembers the file's "last modified" time and only re-reads the PDF when that time changes. That is why replacing or uploading a new PDF takes effect immediately, without restarting anything, and why normal questions are fast.

### 12.3 Step 2: Cutting the text into chunks (`chunks_of`)

A chunk is a small passage, about one short paragraph. The rules:

1. Go through the text **line by line**, adding lines to the current chunk.
2. When adding the next line would make the chunk longer than **`CHUNK_CHARS = 700` characters**, close the chunk and start a new one.
3. **Section headings are remembered.** Any line that looks like `5. Courses Offered, ...` (a number, a dot, a space, a capital letter) is a heading. Every chunk starts with a tag such as `[5. Courses Offered, Eligibility, Duration and Fees]`, so even a chunk from the middle of a section still "knows" which section it belongs to.
4. **Overlap.** A new chunk begins by **repeating the last two lines of the previous chunk**. Why? Cutting text at an arbitrary place can split an important sentence in two. This really happened in this project: the MCA fee sentence was cut as `... Rs. 15,000 per` | `annum (2024-25 notification)`, so the number and its meaning ended up in different chunks. With overlap, each chunk contains the full sentence.

Result for this PDF: **36 chunks**, averaging **656 characters** each. A real chunk looks like this (shortened):

```
[5. Courses Offered, Eligibility, Duration and Fees] 5. Courses Offered, Eligibility,
Duration and Fees  Important note on fees: two official sources give different annual
fees. (a) The course pages of www.oucde.net show the figures marked 'Website'. (b) The
Admission Notification 2024-25 ... A student must confirm the current fee on www.oucde.net
or with the help desk before paying. ...
```

Chunks are **not stored on disk**; they are re-created from the cached text in a few milliseconds whenever a question arrives.

### 12.4 Step 3: Turning text into keywords (`words`)

To compare a question with a chunk, both are reduced to a list of **keywords** the same way:

| Rule | Example |
|---|---|
| Lower-case everything | `MCA` becomes `mca` |
| Split into words, keep letters, digits and dots | `2026-27` becomes `2026`, `27` |
| Remove dots **inside** words | `M.C.A.` becomes `mca` (so it matches `MCA`) |
| Treat `help desk` as one word | `help desk` becomes `helpdesk` |
| Drop **stop words** (very common words with no meaning for search) | `what`, `is`, `the`, `how`, `can`, `I`, `for`, `and` ... (list `STOP` in the code) |
| Remove a trailing `s` from longer words | `fees` becomes `fee`, `courses` becomes `course` |
| Map a few **synonyms** to one word (`SYNONYMS`) | `phone`, `call`, `email`, `mail`, `number`, `telephone`, `reach`, `address` all become `contact`; `date` and `last` become `schedule` |

Real outputs from the program:

| Question | Keywords used for searching |
|---|---|
| What is the MCA fee? | `mca`, `fee` |
| How can I contact the helpdesk? | `contact`, `helpdesk` |
| M.C.A. entrance exam dates | `mca`, `entrance`, `exam`, `schedule` |

### 12.5 Step 4: Which words represent the question? (`chat`)

Normally the keywords come from the **latest question only**. This matters: in a long chat, mixing in all the earlier questions would drown out the newest one (this bug actually happened: asking about the helpdesk after several fee questions returned a fee chunk).

There is one exception, for **very short follow-ups**. If the latest question has fewer than 2 keywords (for example `And for MBA?` has only `mba`), the **previous user question is added**:

```
Previous: "What is the MCA fee?"   +   Latest: "And for MBA?"
Search words: mca, fee, mba
```

This is how a follow-up like "And for MBA?" still finds the fee information.

### 12.6 Step 5: Scoring every chunk (`relevant_text`)

Each chunk gets a number: the higher, the more relevant. For every search word that appears in the chunk:

```
score of a chunk  =  sum over each search word w found in the chunk of
                     idf(w)  x  ( 1 + ln( how many times w appears in the chunk ) )

idf(w) = ln( 1 + N / df(w) )
         N      = total number of chunks (36)
         df(w)  = number of chunks that contain the word w
```

In everyday words:

- **idf ("rarity")**: a word that appears in only a few chunks is a stronger clue than a word that appears everywhere, so it earns more points. (`ln` is just the natural logarithm; it makes the numbers grow gently.)
- **Frequency**: a chunk that mentions the word several times is more likely to be "about" it, but repeating a word 10 times does not give 10 times the points (the `1 + ln(count)` part), which stops long repetitive chunks from winning unfairly.

**Worked example** for the question *"What is the MCA fee?"* on this PDF (real numbers):

- Search words: `mca`, `fee`
- `mca` appears in 17 of 36 chunks, so idf = ln(1 + 36/17) = **1.14**
- `fee` appears in 19 of 36 chunks, so idf = ln(1 + 36/19) = **1.06**

Top chunk (number 15, the one that contains "Rs. 20,000 ... but Rs. 15,000 per annum"): it contains `mca` 2 times and `fee` 4 times.

```
mca:  1.14 x (1 + ln 2) = 1.14 x 1.69 = 1.93
fee:  1.06 x (1 + ln 4) = 1.06 x 2.39 = 2.53
score = 1.93 + 2.53 = 4.46
```

The six highest-scoring chunks for that question:

| Rank | Chunk no. | Score | `mca` x | `fee` x | Section it comes from |
|---|---|---|---|---|---|
| 1 | 15 | 4.46 | 2 | 4 | 5. Courses Offered (end of the MCA entry: Rs. 20,000 on the website but Rs. 15,000 in the 2024-25 notification) |
| 2 | 11 | 4.27 | 1 | 7 | 5. Courses Offered (note that two sources give different fees; start of the MBA entry) |
| 3 | 14 | 4.16 | 2 | 3 | 5. Courses Offered (MCA eligibility, Mathematics condition) |
| 4 | 12 | 3.72 | 2 | 2 | 5. Courses Offered (MBA/MCA eligibility, medium, duration) |
| 5 | 8 | 3.45 | 3 | 1 | 4. Admissions (MBA and MCA entrance test) |
| 6 | 16 | 2.54 | 0 | 4 | 5. Courses Offered (MA programmes' fees) |

The 6 winners are then put back into **document order** (so the text reads naturally, top to bottom) rather than score order.

If a document is so small that it has 6 chunks or fewer, all chunks are simply used.

### 12.7 Step 6: Building the message for the AI (`system_prompt`, `chat`)

The AI receives a list of messages:

1. **A "system" message** (the standing instructions, never shown to the user), made of:
   - the rules: *answer ONLY from the information below; keep it short; if the answer is not there, say you don't know and suggest the college office; include every condition and value for eligibility, fees and dates; if two different values exist for the same thing, report both and where each comes from and advise checking www.oucde.net; reply in plain text, no Markdown;*
   - then the heading `COLLEGE INFORMATION (PDF extracts):` followed by the **6 chosen chunks**.
2. **The conversation so far**, only the last **10** messages, and only messages whose role is `user` or `assistant`. (A browser cannot sneak in a fake "system" message, because any other role is thrown away.)

For the MCA fee question this whole system message is about 4,745 characters, roughly **1,200 tokens**, instead of 4,900 for the full PDF.

### 12.8 Step 7: Calling the AI and tidying the reply (`chat`, `post_with_retry`, `clean_reply`)

- The messages are sent to **Groq** (if `GROQ_API_KEY` exists) or to a local **Ollama** server.
- If Groq answers "too many requests" (HTTP 429), the program waits as long as Groq asks (at most 30 seconds) and **tries once more**. If it fails again, the user sees: *"The model is busy (rate limit reached). Please try again in a few seconds."*
- The reply is cleaned: stray Markdown symbols (`**bold**`, backticks, `__`) are removed and list markers (`* ` or `- `) become `•`, because the chat page shows plain text.
- The cleaned reply is returned to the chat page and shown as a grey bubble.

### 12.9 So what are "embeddings", and how is this different?

An **embedding** is a long list of numbers (for example 384 or 1,536 numbers) that a special AI model produces for a piece of text so that texts with **similar meaning get similar numbers**. A system using embeddings would:

1. Turn every chunk into a list of numbers once, and store them in a **vector database**.
2. Turn the question into a list of numbers too.
3. Pick the chunks whose numbers are **closest** to the question's numbers (usually measured with "cosine similarity").

The big advantage is that it understands **meaning**: a question about *"charges"* can find a chunk that only says *"fee"*, because the two words mean the same thing.

| | Keyword scoring (this project) | Embeddings + vector database |
|---|---|---|
| Understands synonyms | Only the few listed in `SYNONYMS` | Yes, automatically |
| Needs an extra AI model | No | Yes (to create the numbers) |
| Needs extra storage | No | Yes (vector database) |
| Easy to explain and debug | Very (you can print the scores) | Harder |
| Speed and cost | Instant, free | Extra work per question and per document |
| Good enough for a 7-page handbook? | Yes | Overkill, but better for huge document sets |

**Known weakness of the current method:** if a question uses a word that is not in the PDF and not in the synonym list (for example "cost" or "charges" instead of "fee"), that word scores nothing. The other words in the question usually still find the right chunk (and the AI understands the meaning once it has the chunk), but it can occasionally miss. If that happens, add the word to `SYNONYMS`.

**Upgrade path:** only the function `relevant_text(text, question)` decides which chunks to send. To move to embeddings later, replace that one function (for example with the `sentence-transformers` library, or an embeddings API), and the rest of the program stays unchanged.

### 12.10 Where each step lives in the code (`backend/app.py`)

| Step | Function or constant | What it does |
|---|---|---|
| Read the PDF | `pdf_text()` | pypdf: text of all pages |
| Cache | `load_knowledge()`, `_cache` | Re-reads only when the file's modified time changes |
| Cut into chunks | `chunks_of()`, `CHUNK_CHARS` | 700-character pieces, heading tag, two-line overlap |
| Make keywords | `words()`, `STOP`, `SYNONYMS` | Lower-case, remove dots, stop words, plurals, synonyms |
| Pick the best chunks | `relevant_text()`, `TOP_K` | Score = idf x (1 + ln count); keep best 6 in document order |
| Build instructions | `system_prompt()` | Rules plus the chosen chunks |
| Choose the question words | `chat()` | Latest question; add previous one for short follow-ups |
| Call the AI | `chat()`, `post_with_retry()` | Groq or Ollama; one retry on rate limit |
| Tidy the reply | `clean_reply()` | Remove Markdown marks |
| Replace the PDF | `upload_knowledge()` | Checks it is a readable PDF with text, then saves it |

### 12.11 Settings you can tune

| Setting (top of `app.py`) | Now | If you raise it | If you lower it |
|---|---|---|---|
| `CHUNK_CHARS` | 700 | Bigger passages, more context per chunk, fewer chunks | Smaller, more precise chunks, but sentences may be cut |
| `TOP_K` | 6 | More information for the AI, but more tokens and more chance of the free-plan limit | Faster and cheaper, but may miss a needed chunk |
| `STOP` | common English words | Fewer words used for matching | More words used (more noise) |
| `SYNONYMS` | contact words, `date`, `last` | Better matching for the words you add | Fewer matches |

### 12.12 See exactly what the AI was given

From the `backend` folder (with the virtual environment active) you can print the full instruction text for any question:

```powershell
python -c "import app; print(app.system_prompt('What is the MCA fee?'))"
```

To see the keywords and chunk count:

```powershell
python -c "import app; t=app.load_knowledge(); print(app.words('What is the MCA fee?')); print(len(app.chunks_of(t)), 'chunks')"
```

This is the best way to find out *why* the chatbot answered the way it did: if the needed fact is not in the printed text, the problem is in retrieval (steps 2 to 6); if it is there but the answer is wrong, the problem is in the AI's reading of it.

### 12.13 Automated tests that protect this logic

These run with `python -m pytest` in `backend/tests/test_api.py` (and need no internet):

- the PDF text really ends up inside the system message;
- only the relevant chunk is selected for a contact question and an unrelated one is left out;
- `M.C.A.` matches `MCA`, and `help desk` matches `helpdesk`;
- chunks keep their section heading and repeat boundary lines;
- a short follow-up uses the previous question, but a normal question does not;
- only the last 10 messages and only `user`/`assistant` roles are sent;
- uploading a new PDF changes the next prompt; a text file or a corrupt PDF is rejected;
- Markdown marks are removed from replies; the rate-limit retry works once, then shows a friendly error.

Further tests in `test_live.py` ask the real AI questions (fees with both values, eligibility, admission dates, helpdesk contact, the Director's name, the entrance exam date, and an off-topic question) and check that the key facts appear.

### 12.14 Limits of this approach

- Keyword scoring can miss a chunk when the question uses unusual wording (see 12.9).
- The AI sees only 6 chunks (about 4,000 characters), so a question that needs facts from many far-apart places (for example "compare all PG course fees") may get only part of the answer.
- The quality of every answer depends on the quality of the PDF. If the PDF is wrong or outdated, so are the answers.
- The AI can still occasionally misread a correct chunk, which is why the project tells it to advise confirming important details on www.oucde.net.
