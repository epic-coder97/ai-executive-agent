_MESSAGES = []

def post_message(channel: str, text: str):
    msg = {"channel": channel, "text": text}
    _MESSAGES.append(msg)
    return {"ok": True, "message": msg}