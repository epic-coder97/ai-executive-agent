from datetime import datetime, timedelta

_FAKE_BUSY = [
    {"start": "2025-10-21T09:00", "end": "2025-10-21T09:30"},  # Tuesday
    {"start": "2025-10-22T13:00", "end": "2025-10-22T14:00"},  # Wednesday
]

_DAY_MAP = {
    "tue": "2025-10-21",
    "tues": "2025-10-21",
    "tuesday": "2025-10-21",
    "thu": "2025-10-23",
    "thur": "2025-10-23",
    "thurs": "2025-10-23",
    "thursday": "2025-10-23",
}

def list_events(user_id: str):
    return _FAKE_BUSY

def _overlaps(a_start, a_end, b_start, b_end):
    return max(a_start, b_start) < min(a_end, b_end)

def _busy_intervals_for_day(day_iso):
    return [
        (datetime.fromisoformat(b["start"]), datetime.fromisoformat(b["end"]))
        for b in _FAKE_BUSY
        if b["start"].startswith(day_iso)
    ]

def propose_slots(user_id: str, duration_min: int, day_hint: str):
    day_iso = _DAY_MAP.get((day_hint or "").lower(), "2025-10-21")
    day_start = datetime.fromisoformat(day_iso + "T08:00")
    busy = _busy_intervals_for_day(day_iso)

    slots = []
    t = day_start
    while len(slots) < 3 and t.hour < 18:
        start = t
        end = start + timedelta(minutes=duration_min)
        if not any(_overlaps(start, end, bs, be) for bs, be in busy):
            slots.append({
                "start": start.isoformat(timespec="minutes"),
                "end":   end.isoformat(timespec="minutes")
            })
        t += timedelta(minutes=30)
    return slots
