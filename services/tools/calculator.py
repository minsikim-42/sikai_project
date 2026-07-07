def run(expression: str):
    try:
        result = eval(expression)
        return str(result)
    except Exception:
        return "계산 오류"