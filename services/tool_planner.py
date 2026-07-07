from services.tool_manager import TOOLS

from services.tool_manager import TOOLS

def plan(message: str):

    if message.startswith("/"):

        parts = message[1:].split(maxsplit=1)

        tool = parts[0]
        argument = parts[1] if len(parts) > 1 else ""

        if tool in TOOLS:
            return {
                "use_tool": True,
                "tool": tool,
                "argument": argument
            }

    return {
        "use_tool": False
    }