_DRAFTS = []
_SENT = []

def create_draft(to: str, subject: str, body: str):
    draft = {"to": to, "subject": subject, "body": body}
    _DRAFTS.append(draft)
    return draft

def send(draft: dict):
    _SENT.append(draft)
    return {"ok": True, "sent": draft}

def get_sent():
    return list(_SENT)
