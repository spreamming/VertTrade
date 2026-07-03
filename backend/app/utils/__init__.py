def infer_exchange(code: str) -> str:
    if code.startswith(("6", "5")):
        return "SH"
    if code.startswith(("0", "3")):
        return "SZ"
    if code.startswith(("8", "4", "9")):
        return "BJ"
    return "UNKNOWN"
