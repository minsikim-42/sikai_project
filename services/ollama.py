import requests
from config import MODEL, OLLAMA_URL

def chat(message: str):
	instruction = "한글로 답하고 짧게 말한다."
	res = requests.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                        "model": MODEL,
                        "messages": [
				{
                                	"role": "system",
                                	"content": instruction
                        	},
				{
					"role": "user",
					"content": message
				}
			],
                        "stream": False,
			"options": {
				"num_predict": 200,
				"temperature": 0.7,
				"top_p": 0.9
			}
	})
	print(res.text)
	data = res.json()
	return data
