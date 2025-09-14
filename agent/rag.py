from pathlib import Path
from typing import Tuple, List, Dict
import re

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")
_WORD = re.compile(r"[A-Za-z0-9']+")

def _sentences(text: str) -> List[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    parts = _SENT_SPLIT.split(text)
    return [p.strip() for p in parts if p.strip()]

def _words(s: str) -> List[str]:
    return [w.lower() for w in _WORD.findall(s)]

def _load_text(p: Path) -> str:
    ext = p.suffix.lower()
    if ext in {".md", ".txt"}:
        return p.read_text(encoding="utf-8", errors="ignore")
    if ext == ".pdf" and PdfReader:
        try:
            reader = PdfReader(str(p))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception:
            return ""
    return ""

class RAG:
    def __init__(self, kb_dir: Path, top_k: int = 3, window: int = 1):
        self.kb_dir = Path(kb_dir)
        self.top_k = top_k
        self.window = window
        self.index: List[Dict] = []
        self._build_index()

    def _build_index(self):
        self.index.clear()
        for p in list(self.kb_dir.glob("**/*.md")) + \
                 list(self.kb_dir.glob("**/*.txt")) + \
                 list(self.kb_dir.glob("**/*.pdf")):
            text = _load_text(p)
            if not text:
                continue
            sents = _sentences(text)
            for i, s in enumerate(sents):
                toks = _words(s)
                self.index.append({"file": p.name, "sent_idx": i, "sentence": s, "tokens": toks, "all_sents": sents})

    def answer(self, question: str) -> Tuple[str, List[str]]:
        if not self.index:
            return ("No documents loaded in KB. Add a .md or .txt or .pdf file to kb/.", [])
        q_tokens = [t for t in _words(question) if len(t) > 2]
        q_bigrams = set(zip(q_tokens, q_tokens[1:]))

        scored = []
        for row in self.index:
            toks = row["tokens"]
            overlap = len(set(q_tokens) & set(toks))
            if overlap == 0:
                continue
            toks_bi = set(zip(toks, toks[1:])) if len(toks) > 1 else set()
            bigram_bonus = 0.5 * len(q_bigrams & toks_bi)
            score = overlap + bigram_bonus
            if score > 0:
                scored.append((score, row))

        if not scored:
            return ("No direct sentence match found in KB. Rephrase the question or add policy text to kb/.", [])

        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[: self.top_k]

        snippets = []
        cites = []
        for _, row in top:
            sents = row["all_sents"]
            i = row["sent_idx"]
            start = max(0, i - self.window)
            end = min(len(sents), i + self.window + 1)
            snippet = " ".join(sents[start:end]).strip()
            file = row["file"]
            if file not in cites:
                cites.append(file)
            snippets.append(f'“{snippet}”  — {file}')

        answer = "Grounded answer:\n" + "\n\n".join(snippets)
        return (answer, cites)
