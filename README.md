### 1. install uv and ollama
window
`powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`

*install ollama in https://ollama.com/download

### 2. activate uv

`uv venv`

`.venv\Scripts\activate`

### 3. install import
`./import_library_win.bat`

### 4. config.py
```
OLLAMA_URL = "http://localhost:11434"

SERVER_MODE = "tailscale"
# SERVER_MODE = "public" or "tailscale"
# public is not active

API_KEY = ""

NAVER_CLIENT_ID = ""
NAVER_CLIENT_SECRET = ""
SERPER_API_KEY = ""
```
### 5. run, ollama serve
`./run_win.bat`

ollama serve (you need to install model like 'ollama run qwen3:8b' or if you want use downloaded model, using script.js fnc)

### 6. view

https://github.com/user-attachments/assets/1b18b8aa-758b-4de3-8bb1-fbc0f079bc06


