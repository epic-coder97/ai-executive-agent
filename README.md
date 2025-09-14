
# ai-executive-agent-portfolio

An end-to-end demo of an **Executive Assistant AI Agent** that can plan tasks, use tools, keep memory, run evals, apply guardrails with HITL, choose between prompting vs RAG vs fine-tuning, and integrate with productivity tools through zero-cost mocks.  
Built to showcase portfolio readiness **without paying for APIs**.

---

## 🚀 What This Demo Proves

- **Agents that plan and use tools**  
  Decomposes long-horizon tasks, calls tools (Calendar, Email, Slack, Expenses), and persists state in SQLite.

- **Evals with feedback loops**  
  Scripted scenarios measure task success, log failure modes, and produce metrics.

- **Guardrails + Human-in-the-Loop (HITL)**  
  Risky actions (like sending email or creating calendar events) require confirmation. Unsafe actions are blocked.

- **Prompting vs RAG vs Fine-Tune**  
  Side-by-side demos show when prompting is enough, when RAG is required, and why fine-tuning is unnecessary here.

- **Integrations**  
  Google Calendar, Gmail, Slack, Expensify, Zoom are **mocked adapters** that mirror real APIs.

- **Human workflow mapping**  
  Identifies where EAs spend time and automates 1–2 tasks.

---

## 🛠 Tech Stack

- Python 3.11  
- Streamlit (UI)  
- SQLite (agent memory + logs)  
- FAISS or Chroma (RAG index)  
- Pydantic (schemas)  
- PyTest (testing)  

---

## 📂 Project Structure

```

src/
app.py                  # Streamlit UI
agent/
planner.py            # task decomposition + execution
tools.py              # tool registry + adapters
memory.py             # SQLite-based memory
guardrails.py         # rules + HITL confirmation
rag.py                # RAG over /kb documents
mocks/
gmail.py              # mock Gmail
gcal.py               # mock Google Calendar
slack.py              # mock Slack
expensify.py          # mock Expenses
zoom.py               # mock Zoom
evals/
scenarios.yaml        # scripted tasks
run\_evals.py          # evaluation harness
kb/
handbook.pdf          # example source for RAG
data/
runs.sqlite           # created at runtime
tests/
test\_agent\_happy.py
test\_guardrails.py

````

---

## ⚡ Quickstart

### 1. Setup environment
```bash
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
````

### 2. Add a document

Place a sample PDF (e.g., fake handbook) into `kb/`.

### 3. Run the app

```bash
streamlit run src/app.py
```

### 4. Run evals

```bash
python src/evals/run_evals.py
```

---

## 🎬 Demo Flow

1. **Plan the week**

   > “Plan my next 7 days with daily standup at 9 am and DS interview prep.”
   > Restart app → ask *“What did we plan yesterday?”* → proves memory.

2. **Scheduling with HITL**

   > “Find a 30-min slot with Alex next Tuesday. Draft email but don’t send until I approve.”
   > Guardrail waits for **Approve** click.

3. **RAG vs Prompting**

   > “What is our expense approval policy?”
   > Show ungrounded vs grounded answers.

4. **Slack + Zoom**

   > “Post a status update in #ops and create a Zoom link.”
   > Goes through mock adapters, logged in SQLite.

---

## 🛡 Guardrails + HITL

* Unsafe phrases blocked automatically.
* Email + Calendar require confirmation.
* Slack posts scrubbed for PII before “sending”.

---

## 📊 Evals

* `evals/scenarios.yaml` → defines scripted tasks & acceptance checks.
* `evals/run_evals.py` → runs all, reports:

  * ✅ Success rate
  * 🔧 Tool-call precision
  * 🕑 Avg steps per task
  * ❌ Failure tags (hallucination, drift, misuse, timeout)

---

## 💾 Memory Model

* **Short-term:** context for current session.
* **Long-term:** stored in SQLite, recalled by topic.
* Reloaded at startup to maintain continuity.

---

## 📚 RAG Implementation

* PDFs in `kb/` → chunked + embedded.
* Retrieval with top-k + rerank.
* Citations displayed in UI.

---

## 📌 Requirements

`requirements.txt`

```
streamlit
pydantic
faiss-cpu
chromadb
pypdf
tiktoken
sqlalchemy
python-dotenv
pytest
```

---

## 🗺 Roadmap

* Add calendar conflict resolver with multiple options
* Mock expense OCR with sample receipts
* Richer evals with noisy inputs
* Exportable run reports (CSV)

---

## 📄 License

MIT

