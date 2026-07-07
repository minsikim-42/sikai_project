from services.tools import calculator
from services.tools import time
from services.tools import search

TOOLS = {
    "calc": {
        "func": calculator.run,

        "ollama": {
            "type": "function",

            "function": {
                "name": "calc",

                "description": "수식을 계산한다.",

                "parameters": {
                    "type": "object",

                    "properties": {
                        "expression": {
                            "type": "string"
                        }
                    },

                    "required": [
                        "expression"
                    ]
                }
            }
        }
    },
    "time": {
        "func": time.run,

        "ollama": {
            "type": "function",

            "function": {
                "name": "time",

                "description": "현재 시간을 알려준다.",

                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string"
                        }
                    },
                    "required": []
                }
            }
        }
    },
    "search": {
        "func": search.run,

        "ollama": {
            "type": "function",

            "function": {
                "name": "search",

                "description": "인터넷에서 최신 정보를 검색한다.",

                "parameters": {
                    "type": "object",
                    "query": {
                        "type": "string",
                        "description": "검색할 내용"
                    },
                    "required": [
                        "query"
                    ]
                }
            }
        }
    }
}

def run(tool: str, arguments: str):
    tool_info = TOOLS.get(tool)
    if tool_info is None:
        return None

    return {
        "tool": tool,
        "success": True,
        "content": tool_info["func"](**arguments)
    }

def get_ollama_tools():
    return [
        tool["ollama"]
        for tool in TOOLS.values()
    ]