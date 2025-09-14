_REPORTS = []

def create_report(user_id: str, title: str):
    rpt = {"id": len(_REPORTS) + 1, "title": title, "owner": user_id}
    _REPORTS.append(rpt)
    return rpt

def attach_placeholder_receipt():
    return {"receipt": "placeholder-receipt.jpg", "status": "attached"}