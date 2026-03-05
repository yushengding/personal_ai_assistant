_state = {"active": False}


def activate():
    _state["active"] = True


def deactivate():
    _state["active"] = False


def healthcheck():
    return {"ok": True, "active": _state["active"]}


def echo(text: str) -> str:
    return text
