from fastapi import FastAPI
from services import ollama
from models import ChatRequest

app = FastAPI()

@app.get("/")
def root():
	return { "message": "Hello AI Server" }

@app.post("/chat")
def chat(request: ChatRequest):
	response = ollama.chat(request.message)
	content = response["message"].get("content")
	nyang_content = f"{content} 냥."
	thinking = response["message"].get("thinking")
	return {
		"response": f"{nyang_content}\n(thinking){thinking}"
	}


