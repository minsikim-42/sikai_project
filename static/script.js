function getUserId() {
    let userId = localStorage.getItem("my_ai_user_id");
    if (!userId) {
        // ID가 없으면 'user_' 뒤에 랜덤 9자리 문자열 생성
        userId = "user_" + Math.random().toString(36).substring(2, 11);
        localStorage.setItem("my_ai_user_id", userId);
    }
    return userId;
}

const USER_ID = getUserId();
console.log("현재 접속한 유저 ID:", USER_ID);

// 💡 공통 헤더 생성 함수
function getAuthHeaders() {
    return {
        "Content-Type": "application/json",
        "X-User-Id": USER_ID  // 백엔드로 유저 ID 전달!
    };
}

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

    // chat POST 요청
    try {
        const model = document.getElementById("modelSelect").value;
        const predict = document.getElementById("num_predict").value;
        const thinkCheck = document.getElementById("thinkCheck").checked;

        const response = await fetch("/chat", {
            method: "POST",
            headers: getAuthHeaders(),
            body: JSON.stringify({
                conversation_id: currentConversationId,
                message: userText,
                model: model,
                predict: predict, // 토큰 수 제한
                isThink: thinkCheck,
            })
        });

        const data = await response.json();
        const jobId = data.job_id;

        while (true) {

            const res = await fetch(`/chat/stream/${jobId}`);

            const job = await res.json();

            thinkingDiv.textContent = job.thinking;
            contentDiv.innerHTML = marked.parse(job.answer);

            chatBox.scrollTop = chatBox.scrollHeight;

            if (job.finished)
                break;

            await new Promise(r => setTimeout(r, 200));
        }
        // const reader = response.body.getReader();
        // const decoder = new TextDecoder();

        // let buffer = "";
        // let contentText = "";

        // while (true) {

        //     const { done, value } = await reader.read();

        //     if (done) break;

        //     buffer += decoder.decode(value, { stream: true });

        //     const lines = buffer.split("\n");
        //     buffer = lines.pop();

        //     for (const line of lines) {

        //         if (!line.trim()) continue;

        //         const chunk = JSON.parse(line);

        //         if (chunk.thinking)
        //             thinkingDiv.textContent += chunk.thinking;

        //         if (chunk.content) {
        //             contentText += chunk.content;
        //             contentDiv.innerHTML = marked.parse(contentText);
        //         }
        //     }

        //     chatBox.scrollTop = chatBox.scrollHeight;
        // }
        
    } catch (error) {

        aiMessage.textContent = "서버 연결 실패: " + error.message;
        // input.focus();
    } finally {
        isGenerating = false;
        input.disabled = false;
        sendButton.disabled = false;
        input.placeholder = "메시지를 입력해주세요...";
        input.focus();
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
input.addEventListener("keyup", function (e) {
    if (e.key !== "Enter") return;
    if (isComposing) return;

    e.preventDefault();
    sendMessage();
});

// =========================== 페이지 로드 시 불러오기 ==============================
document.addEventListener("DOMContentLoaded", () => {
    document
        .getElementById("new-chat")
        .addEventListener("click", newChat); // 새로운 세션
    loadModels(); // 모델 불러오기
    loadChatHistory(currentConversationId); // 대화내역
    loadConversations();
});

// 특정 대화의 내역을 서버에서 가져와 화면에 그리는 함수
async function loadChatHistory(conversation_id) {
    try {
        const response = await fetch(`/chat/${conversation_id}/messages`, {headers: getAuthHeaders()});
        const data = await response.json();
        
        currentConversationId = conversation_id

        chatBox.innerHTML =
        '<div class="message ai">안녕하세요! 무엇을 도와드릴까요?</div>';
        // 메시지들을 순회하며 화면에 추가
        data.messages.forEach(msg => {
            if (msg.role === "user") {
                addMessage("user", msg.content);
            } else if (msg.role === "assistant") {
                const aiMessage = document.createElement("div");
                aiMessage.classList.add("message", "ai");

                let innerHTML = "";

                // 💡 만약 JSON에 저장된 thinking 데이터가 있다면 먼저 붙여줌
                if (msg.thinking) {
                    innerHTML += `
                        <details class="thinking-box">
                            <summary>🤔 Thinking</summary>
                            <pre class="thinking">${msg.thinking}</pre>
                        </details>
                    `;
                }

                // 본문 텍스트 마크다운 처리해서 붙여줌
                innerHTML += `<div class="content">${marked.parse(msg.content)}</div>`;
                
                aiMessage.innerHTML = innerHTML;
                chatBox.appendChild(aiMessage);
            }
        });

        chatBox.scrollTop = chatBox.scrollHeight;

    } catch (error) {
        alert("대화 내역을 불러오는 중 오류 발생:", error);
    }
}

// ======================= 새로운 세션 =========================
let currentConversationId = 1;

async function newChat(){
    try {

        const response = await fetch("/conversation/new",{
            method:"POST",
            headers: getAuthHeaders()
        });

        console.log("status:", response.status);

        const data = await response.json();

        console.log("data:", data);

        // info = {
        //     "id": conversation_id,
        //     "title": f"대화 {conversation_id}",
        //     "created_at": datetime.now().isoformat()
        // }
        currentConversationId = data.id;

        // localStorage.setItem(
        //     "current_conversation_id",
        //     currentConversationId
        // );

        addHistory(currentConversationId, data.title);

        chatBox.innerHTML =
            '<div class="message ai">안녕하세요! 무엇을 도와드릴까요?</div>';

    }
    catch(e){

        console.error("new chat error:", e);

    }
}
function addHistory(id, title="-"){

    const history = document.querySelector(".history");

    const item = document.createElement("div");

    item.className = "history-item";

    item.textContent = title;

    item.dataset.id = id;

    item.onclick = () => {

        document
            .querySelectorAll(".history-item")
            .forEach(e => e.classList.remove("active"));

        item.classList.add("active");

        currentConversationId = id;

        loadChatHistory(id);
    };

    history.prepend(item);
}

// async function loadConversation(id){

//     currentConversationId = id;

//     const response = await fetch(`/conversation/${id}`,{
//         headers: getAuthHeaders()
//     });

//     const messages = await response.json();


//     chatBox.innerHTML = "";


//     for(const msg of messages){

//         const div = document.createElement("div");

//         div.className =
//             "message " + msg.role;

//         div.textContent =
//             msg.content;


//         chatBox.appendChild(div);
//     }
// }
async function loadConversations(){

    const response = await fetch("/api/conversations", {
        headers: getAuthHeaders()
    });

    const data = await response.json();

    data.conversations.forEach(conv => {
        addHistory(
            conv.id,
            conv.title
        );
    });
}


// ====================== 모델 불러오기 ======================
async function loadModels() {
    // const modelSelect = document.getElementById("modelSelect");
    // if (!modelSelect) return;
    // const DEFAULT_MODEL = "qwen3:0.6b";

    // try {
    //     const response = await fetch("/api/models", {headers: getAuthHeaders()});
    //     const data = await response.json();

    //     // 기존 하드코딩된 옵션 초기화
    //     modelSelect.innerHTML = "";

    //     if (data.models && data.models.length > 0) {
    //         data.models.forEach(modelName => {
    //             const option = document.createElement("option");
    //             option.value = modelName;
    //             option.textContent = modelName;
    //             modelSelect.appendChild(option);
    //         });
    //         if (data.models.includes(DEFAULT_MODEL)) {
    //             modelSelect.value = DEFAULT_MODEL;  // 디폴트 모델을 기본으로 선택!
    //         } else {
    //             modelSelect.value = data.models[0]; // 없으면 목록의 첫 번째 모델 선택
    //         }
    //         console.log("모델 목록 로드 완료:", data.models);
    //     } else {
    //         // 설치된 모델이 없을 경우 안내
    //         modelSelect.innerHTML = `<option value="">설치된 모델 없음</option>`;
    //     }
    // } catch (error) {
    //     console.error("모델 목록 불러오기 실패:", error);
    //     modelSelect.innerHTML = `<option value="qwen3:0.6b">기본 모델 (연결 실패)</option>`;
    // }
}

