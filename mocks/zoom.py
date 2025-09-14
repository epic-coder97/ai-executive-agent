_MEETINGS = []

def create_meeting(topic: str, when: str):
    m = {"id": len(_MEETINGS) + 1, "topic": topic, "when": when, "join_url": "https://zoom.example/demo"}
    _MEETINGS.append(m)
    return m