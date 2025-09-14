# app.py
import os
import sys
import json
from pathlib import Path

import streamlit as st
import yaml  # for inline evals panel

# Path setup so PyCharm runs this directly from project root
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# App imports
from agent.planner import plan_and_execute
from agent.memory import Memory
from agent.guardrails import Guardrails, ApprovalQueue
from agent.rag import RAG
from agent.tools import Toolbelt
from mocks import gmail  # for mock "send"

# Storage and KB paths
DB_PATH = ROOT / "data" / "runs.sqlite"
KB_DIR = ROOT / "kb"
os.makedirs(ROOT / "data", exist_ok=True)

# Singletons
MEM = Memory(str(DB_PATH))
GUARDS = Guardrails()
APPROVALS = ApprovalQueue(MEM)
RAG_ENGINE = RAG(KB_DIR)

# Streamlit page
st.set_page_config(page_title="AI Executive Agent", page_icon="🗂", layout="wide")
st.title("AI Executive Agent — Portfolio Demo")

# Persist last run so other buttons do not wipe the UI
if "last_result" not in st.session_state:
    st.session_state["last_result"] = None
if "last_task" not in st.session_state:
    st.session_state["last_task"] = ""

# ---------------------- Sidebar ----------------------
with st.sidebar:
    st.header("Settings")
    mock_mode = st.toggle("Mock Mode", value=True, help="Use mocked integrations only")
    enable_rag = st.toggle("Enable RAG", value=True)
    show_traces = st.toggle("Show traces", value=True)

    st.divider()
    st.header("Quick presets")
    preset = st.selectbox(
        "Pick a demo task",
        [
            "Schedule a 30-minute sync with Alex next Tuesday and draft the email for approval.",
            "Create an expense report for October Ops and attach a placeholder receipt.",
            "Create a Zoom meeting for Thursday 2 pm and draft the invite.",
            "What is our expense approval policy?",
        ],
        index=0,
    )
    if st.button("Use preset"):
        st.session_state["preset_task"] = preset

    st.divider()
    st.header("Memory")
    user_id = st.text_input("User ID", value="demo-user")
    if st.button("Reset session memory"):
        MEM.reset_session(user_id)
        st.success("Session memory cleared")

# ---------------------- Input + Controls ----------------------
st.subheader("Enter a task")
st.caption("Example: Find a 30 minute slot with Alex next Tuesday and draft the email for approval.")
user_task = st.text_area(
    "",
    value=st.session_state.get("preset_task", ""),
    height=80,
    placeholder="Type a task..."
)

col1, col2 = st.columns([1, 1])
with col1:
    run_btn = st.button("Run Agent", type="primary")
with col2:
    approve_all_btn = st.button("Approve all pending actions")

# Approve-all executes side effects too
if approve_all_btn:
    pend = APPROVALS.list_pending(user=user_id)
    executed = 0
    for item in pend:
        approved_row = APPROVALS.approve(item["id"])
        payload = approved_row.get("payload")
        try:
            payload = json.loads(payload) if isinstance(payload, str) else payload
        except Exception:
            pass
        if approved_row.get("action") == "send_email":
            gmail.send(payload)
        executed += 1
    st.success(f"Approved {executed} action(s)" + (" and executed them" if executed else ""))

# ---------------------- Run Agent ----------------------
result = None
if run_btn and user_task.strip():
    result = plan_and_execute(
        user_id=user_id,
        task=user_task,
        memory=MEM,
        guards=GUARDS,
        approvals=APPROVALS,
        rag=RAG_ENGINE if enable_rag else None,
        mock_mode=mock_mode,
    )
    # persist last run
    st.session_state["last_result"] = result
    st.session_state["last_task"] = user_task.strip()

# ---------------------- Plan / Artifacts / Trace ----------------------
display = result or st.session_state.get("last_result")
if display:
    st.subheader("Plan & Execution")
    st.write(display["plan"])

    st.subheader("Artifacts")
    for art in display.get("artifacts", []):
        st.json(art)

    if show_traces:
        st.subheader("Trace")
        for step in display["trace"]:
            with st.expander(step["title"]):
                st.write(step["detail"])

# ---------------------- Last run metrics ----------------------
if display:
    steps = len(display.get("trace", []))
    artifacts_count = len(display.get("artifacts", []))
    try:
        pending_now = len(APPROVALS.list_pending(user=user_id))
    except Exception:
        pending_now = 0
    cand = []
    for a in display.get("artifacts", []):
        if "candidate_slots" in a:
            cand = a["candidate_slots"]
            break

    st.subheader("Metrics")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Steps", steps)
    m2.metric("Artifacts", artifacts_count)
    m3.metric("Pending approvals", pending_now)
    m4.metric("Candidate slots", len(cand))

    if st.button("Clear last run (UI only)"):
        st.session_state["last_result"] = None
        st.session_state["last_task"] = ""

# ---------------------- RAG vs Prompting ----------------------
with st.expander("Policy Q&A — RAG vs Prompting", expanded=False):
    st.caption("Ask a policy question. Compare ungrounded vs grounded with citations.")
    q = st.text_input("Question", value="What is our expense approval policy?", key="policy_q")
    if st.button("Answer policy question", key="policy_btn"):
        prompt_only = "For expenses, typical approval is manager sign-off. (Ungrounded demo answer.)"
        st.write("**Prompt-only:**")
        st.write(prompt_only)
        if enable_rag:
            ans, cites = RAG_ENGINE.answer(q)
            st.write("**RAG (grounded):**")
            st.code(ans)
            if cites:
                st.write("**Citations:**")
                for c in cites:
                    st.write("•", c)
        else:
            st.info("RAG disabled in sidebar. Toggle it on to see grounded answers.")

# ---------------------- Guardrails Demo: Slack Post ----------------------
with st.expander("Slack post — Guardrails and PII scrub", expanded=False):
    st.caption("Unsafe phrases blocked. Email-like PII scrubbed (@ becomes [at]).")
    slack_msg = st.text_input(
        "Message to post in #ops",
        value="Status: dataset ready. Contact me at alex@example.com",
        key="slack_msg",
    )
    if st.button("Post to #ops (mock)", key="slack_post"):
        tb = Toolbelt(memory=MEM, approvals=APPROVALS, guards=GUARDS, mock_mode=mock_mode)
        res = tb.slack_post("#ops", slack_msg)
        st.json(res)
        if res.get("blocked"):
            st.error(f"Blocked by guardrails: {res.get('reason')}")
        else:
            st.success("Posted in mock. Note the [at] scrub if an email was present.")

# ---------------------- Memory Notes (persistence proof) ----------------------
with st.expander("Memory notes", expanded=False):
    st.caption("Save a note, reload the app, and confirm it persists for this user.")
    new_note = st.text_input("Add note", value="", key="mem_note")
    row1, row2 = st.columns([1, 1])
    with row1:
        if st.button("Save note"):
            if new_note.strip():
                MEM.add_note(user_id, new_note.strip())
                st.success("Saved")
            else:
                st.warning("Type something first")
    with row2:
        if st.button("Refresh notes"):
            pass
    notes = MEM.list_notes(user_id)
    if notes:
        st.write(f"Notes for `{user_id}`:")
        for n in notes[:10]:
            st.write("•", n["note"])
    else:
        st.info("No notes yet")

# ---------------------- Approvals (HITL) AFTER agent run ----------------------
st.subheader("Pending Approvals (HITL)")
pend = APPROVALS.list_pending(user=user_id)
if pend and st.button("Clear pending approvals (this user)"):
    MEM.clear_pending(user_id)
    st.success("Cleared pending approvals for this user.")
    pend = []

if pend:
    for item in pend:
        with st.expander(f"{item['action']} — {item['summary']}"):
            st.code(item["payload"], language="json")
            if st.button(f"Approve #{item['id']}", key=f"approve_{item['id']}"):
                approved_row = APPROVALS.approve(item["id"])
                payload = approved_row.get("payload")
                try:
                    payload = json.loads(payload) if isinstance(payload, str) else payload
                except Exception:
                    pass
                sent = None
                if approved_row.get("action") == "send_email":
                    sent = gmail.send(payload)
                st.success("Approved" + (" and sent email" if sent else ""))
else:
    st.info("No pending approvals.")

st.divider()
st.subheader("Sent emails (mock)")
try:
    st.json(gmail.get_sent())
except Exception:
    st.caption("No sent-email ledger available yet.")

# ---------------------- Evals Panel ----------------------
with st.expander("Run Evals (inline)", expanded=False):
    st.caption("Runs evals/scenarios.yaml and reports pass or fail.")
    if st.button("Run evals now", key="run_evals_inline"):
        try:
            spec = yaml.safe_load((ROOT / "evals" / "scenarios.yaml").read_text())
        except Exception as e:
            st.error(f"Could not load scenarios.yaml: {e}")
            spec = []
        passed = 0
        rows = []
        for sc in spec:
            res = plan_and_execute(
                user_id="eval-user",
                task=sc["task"],
                memory=MEM,
                guards=GUARDS,
                approvals=APPROVALS,
                rag=RAG_ENGINE if enable_rag else None,
                mock_mode=mock_mode,
            )
            names = {list(a.keys())[0] for a in res.get("artifacts", [])}
            need = set(sc.get("expects", {}).get("artifacts", []))
            ok = need.issubset(names)
            passed += 1 if ok else 0
            rows.append({
                "name": sc.get("name"),
                "ok": ok,
                "need": sorted(list(need)),
                "got": sorted(list(names)),
            })
        st.write(f"Summary: {passed}/{len(spec)} passed")
        st.json(rows)

# Final caption
st.caption("Mocked Gmail, GCal, Slack, Expensify, Zoom adapters. Swap for real APIs later.")
