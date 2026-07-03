let isGenerating = false;

// 채팅 박스 가져오기
const chatBox = document.getElementById("chatBox");
const input = document.getElementById("input");

// 메시지 추가 함수
function addMessage(role, text) {
    const msg = document.createElement("div");
    msg.classList.add("message", role);
    msg.textContent = text;

    chatBox.appendChild(msg);

    // 자동 스크롤
    chatBox.scrollTop = chatBox.scrollHeight;
}

// 유저 메시지 전송
async function sendMessage() {
    if (isGenerating) return; // 생성 중이면 무시

    const userText = input.value.trim();
    if (!userText) return;

    isGenerating = true;
    input.disabled = true;
    input.placeholder = "AI 답변중..";

    const sendButton = document.getElementById("sendButton");
    sendButton.disabled = true;

    addMessage("user", userText);

    input.value = "";

    const aiMessage = document.createElement("div");
    aiMessage.classList.add("message", "ai");

    aiMessage.innerHTML = `
    <details class="thinking-box">
        <summary>🤔 Thinking</summary>
        <pre class="thinking"></pre>
    </details>

    <div class="content"></div>
    `;

    chatBox.appendChild(aiMessage);

    const thinkingDiv = aiMessage.querySelector(".thinking");
    const contentDiv = aiMessage.querySelector(".content");

    try {

        const model = document.getElementById("modelSelect").value;
        const predict = document.getElementById("num_predict").value;

        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: userText,
                model: model,
                predict: predict, // 토큰 수 제한
            })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        let buffer = "";
        let contentText = "";

        while (true) {

            const { done, value } = await reader.read();

            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            const lines = buffer.split("\n");
            buffer = lines.pop();

            for (const line of lines) {

                if (!line.trim()) continue;

                const chunk = JSON.parse(line);

                if (chunk.thinking)
                    thinkingDiv.textContent += chunk.thinking;

                if (chunk.content) {
                    contentText += chunk.content;
                    contentDiv.innerHTML = marked.parse(contentText);                }
            }

            chatBox.scrollTop = chatBox.scrollHeight;
        }
        isGenerating = false;
        input.disabled = false;
        sendButton.disabled = false;
        input.placeholder = "메시지를 입력해주세요...";
        // input.focus();
    } catch (error) {

        aiMessage.textContent = "서버 연결 실패: " + error.message;

        isGenerating = false;
        input.disabled = false;
        sendButton.disabled = false;
        input.placeholder = "메시지를 입력해주세요...";
        // input.focus();
    }
}

let isComposing = false;

// 한글 입력 시작
input.addEventListener("compositionstart", () => {
    isComposing = true;
});

// 한글 입력 끝
input.addEventListener("compositionend", () => {
    isComposing = false;
});

// Enter 처리
input.addEventListener("keydown", function (e) {
    if (e.key === "Enter") {

        // ⭐ 중요: 조합 중이면 무시
        if (isComposing) return;

        e.preventDefault(); // 기본 엔터 방지
        sendMessage();
    }
});