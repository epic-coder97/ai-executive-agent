from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.planner import plan_and_execute
from agent.memory import Memory
from agent.guardrails import Guardrails, ApprovalQueue
from agent.rag import RAG

DB_PATH = ROOT / "data" / "runs.sqlite"
KB_DIR  = ROOT / "kb"

import yaml
from pathlib import Path
from agent.planner import plan_and_execute
from agent.memory import Memory
from agent.guardrails import Guardrails, ApprovalQueue
from agent.rag import RAG



MEM = Memory(str(DB_PATH))
GUARDS = Guardrails()
APPROVALS = ApprovalQueue(MEM)
RAG_ENGINE = RAG(KB_DIR)

SCEN = Path(__file__).with_name("scenarios.yaml")

def run():
    spec = yaml.safe_load(SCEN.read_text())
    passed = 0
    total = 0
    rows = []
    for sc in spec:
        total += 1
        res = plan_and_execute(
            user_id="eval-user",
            task=sc["task"],
            memory=MEM,
            guards=GUARDS,
            approvals=APPROVALS,
            rag=RAG_ENGINE,
            mock_mode=True,
        )
        names = {list(a.keys())[0] for a in res.get("artifacts", [])}
        need = set()
        for exp in sc.get("expects", {}).get("artifacts", []):
            need.add(exp)
        ok = need.issubset(names)
        passed += 1 if ok else 0
        rows.append({"name": sc["name"], "ok": ok, "need": list(need), "got": list(names)})

    print("=== Eval Summary ===")
    print(f"passed: {passed}/{total}")
    for r in rows:
        print(r)

if __name__ == "__main__":
    run()