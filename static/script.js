"use strict";

// =====================================================
// AUTHENTICATION
// =====================================================

const authScreen = document.getElementById("authScreen");
const appShell = document.getElementById("appShell");
const authForm = document.getElementById("authForm");
const authTitle = document.getElementById("authTitle");
const authDescription = document.getElementById("authDescription");
const authName = document.getElementById("authName");
const nameField = document.getElementById("nameField");
const authEmail = document.getElementById("authEmail");
const authPassword = document.getElementById("authPassword");
const authSubmit = document.getElementById("authSubmit");
const authStatus = document.getElementById("authStatus");
const authSwitch = document.getElementById("authSwitch");
const authSwitchText = document.getElementById("authSwitchText");
const logoutButton = document.getElementById("logoutButton");
const loggedInName = document.getElementById("loggedInName");

let authMode = "login";
let currentUser = null;

// =====================================================
// APPLICATION STATE
// =====================================================

let selectedPdf = null;
let documentUploaded = false;
let isUploading = false;
let isAsking = false;
let currentConversationId = null;
let currentConversationTitle = "New conversation";

// Used to prevent an older conversation request from updating the UI.
let conversationLoadToken = 0;

const MAX_FILE_SIZE = 20 * 1024 * 1024;

// =====================================================
// CHAT HISTORY UI
// =====================================================

const historyStyles = document.createElement("style");

historyStyles.textContent = `
#chatHistorySection {
    margin-top: 24px;
}
#newChatButton {
    width: 100%;
    padding: 11px;
    margin: 10px 0 14px;
    border: 1px solid rgba(255,255,255,.2);
    border-radius: 9px;
    color: inherit;
    background: rgba(255,255,255,.06);
    cursor: pointer;
    font: inherit;
}
#newChatButton:hover, .history-chat:hover {
    background: rgba(139,128,255,.18);
}
#historyList {
    display: flex;
    flex-direction: column;
    gap: 6px;
    max-height: 280px;
    overflow-y: auto;
}
.history-chat {
    width: 100%;
    padding: 10px;
    border: 0;
    border-radius: 8px;
    background: transparent;
    color: inherit;
    text-align: left;
    cursor: pointer;
    font: inherit;
    overflow-wrap: anywhere;
}
.history-chat.active {
    background: rgba(139,128,255,.22);
}
#historyMessage {
    color: #aeb6ce;
    font-size: 12px;
    margin: 8px 0;
}
#chatTranscript {
    display: flex;
    flex-direction: column;
    gap: 14px;
    margin: 20px 0;
}
.chat-bubble {
    padding: 14px 16px;
    border-radius: 14px;
    max-width: 90%;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
    line-height: 1.6;
}
.chat-bubble.user {
    align-self: flex-end;
    background: rgba(116,101,255,.2);
    border: 1px solid rgba(139,128,255,.35);
}
.chat-bubble.assistant {
    align-self: flex-start;
    background: rgba(255,255,255,.06);
    border: 1px solid rgba(255,255,255,.12);
}
.chat-role {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    opacity: .7;
    margin-bottom: 5px;
}
#chatHistorySection .history-empty {
    font-size: 12px;
    color: #aeb6ce;
    line-height: 1.5;
}
`;

document.head.appendChild(historyStyles);

const sidebar = document.querySelector(".sidebar");
const historySection = document.createElement("section");

historySection.id = "chatHistorySection";
historySection.className = "sidebar-section";

historySection.innerHTML = `
    <p class="sidebar-label">YOUR CHATS · 7 DAYS</p>
    <button id="newChatButton" type="button">＋ New chat</button>
    <div id="historyList"></div>
    <p id="historyMessage" role="status" aria-live="polite"></p>
`;

const sidebarDivider = sidebar?.querySelector(".sidebar-divider");

if (sidebarDivider) {
    sidebarDivider.insertAdjacentElement("afterend", historySection);
} else if (sidebar) {
    sidebar.appendChild(historySection);
}

const newChatButton = document.getElementById("newChatButton");
const historyList = document.getElementById("historyList");
const historyMessage = document.getElementById("historyMessage");

const answerCard = document.getElementById("answerCard");
const chatTranscript = document.createElement("div");

chatTranscript.id = "chatTranscript";

if (answerCard) {
    answerCard.insertAdjacentElement("afterbegin", chatTranscript);
}

// =====================================================
// DOM REFERENCES
// =====================================================

const pdfFile = document.getElementById("pdfFile");
const dropZone = document.getElementById("dropZone");
const browseButton = document.getElementById("browseButton");
const uploadButton = document.getElementById("uploadButton");
const removeFileButton = document.getElementById("removeFileButton");
const selectedFile = document.getElementById("selectedFile");
const fileName = document.getElementById("fileName");
const fileSize = document.getElementById("fileSize");
const uploadStatus = document.getElementById("uploadStatus");
const uploadProgress = document.getElementById("uploadProgress");
const documentInfo = document.getElementById("documentInfo");
const documentDetails = document.getElementById("documentDetails");

const question = document.getElementById("question");
const askButton = document.getElementById("askButton");
const answerStatus = document.getElementById("answerStatus");
const answer = document.getElementById("answer");
const source = document.getElementById("source");
const emptyAnswer = document.getElementById("emptyAnswer");
const answerLoading = document.getElementById("answerLoading");
const answerContent = document.getElementById("answerContent");
const copyButton = document.getElementById("copyButton");
const characterCount = document.getElementById("characterCount");
const suggestionChips = document.querySelectorAll(".suggestion-chip");

// =====================================================
// AUTHENTICATION HELPERS
// =====================================================

function setAuthStatus(message, isError = false) {
    authStatus.textContent = message;
    authStatus.style.color = isError ? "#fca5a5" : "#86efac";
}

function showAuthScreen() {
    currentUser = null;
    authScreen.hidden = false;
    appShell.hidden = true;
}

function showDashboard(user) {
    currentUser = user;
    authScreen.hidden = true;
    appShell.hidden = false;

    loggedInName.textContent =
        `Signed in: ${user.name || user.email || ""}`;

    setAuthStatus("");
    resetFileSelection();
    resetAnswer();

    currentConversationId = null;
    currentConversationTitle = "New conversation";
    chatTranscript.replaceChildren();

    loadConversations();
}

function setAuthMode(mode) {
    authMode = mode;
    authForm.reset();
    setAuthStatus("");

    const registering = mode === "register";

    authTitle.textContent = registering
        ? "Create your account"
        : "Welcome back";

    authDescription.textContent = registering
        ? "Register to start using DocuMind AI."
        : "Sign in to upload documents and ask questions.";

    nameField.hidden = !registering;
    authName.required = registering;

    authPassword.autocomplete = registering
        ? "new-password"
        : "current-password";

    authSubmit.textContent = registering
        ? "Create account"
        : "Log in";

    authSwitchText.textContent = registering
        ? "Already have an account?"
        : "Don't have an account?";

    authSwitch.textContent = registering ? "Log in" : "Register";
}

authSwitch.addEventListener("click", () => {
    setAuthMode(authMode === "login" ? "register" : "login");
});

authForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = authEmail.value.trim();
    const password = authPassword.value;
    const name = authName.value.trim();

    if (!email || !password) {
        setAuthStatus("Enter your email and password.", true);
        return;
    }

    if (authMode === "register" && !name) {
        setAuthStatus("Enter your name.", true);
        return;
    }

    if (authMode === "register" && password.length < 8) {
        setAuthStatus(
            "Password must contain at least 8 characters.",
            true
        );
        return;
    }

    authSubmit.disabled = true;
    authSubmit.textContent = "Please wait...";

    try {
        const endpoint = authMode === "register"
            ? "/api/auth/register"
            : "/api/auth/login";

        const payload = authMode === "register"
            ? { name, email, password }
            : { email, password };

        const response = await fetch(endpoint, {
            method: "POST",
            credentials: "same-origin",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Authentication failed.");
        }

        if (authMode === "register") {
            setAuthMode("login");
            authEmail.value = email;
            setAuthStatus(
                "Account created! Please log in with your new account."
            );
            return;
        }

        showDashboard(data.user);

    } catch (error) {
        setAuthStatus(error.message, true);
    } finally {
        authSubmit.disabled = false;
        authSubmit.textContent = authMode === "register"
            ? "Create account"
            : "Log in";
    }
});

logoutButton.addEventListener("click", async () => {
    try {
        await fetch("/api/auth/logout", {
            method: "POST",
            credentials: "same-origin"
        });
    } catch (error) {
        console.error("Logout failed:", error);
    }

    conversationLoadToken++;
    currentConversationId = null;
    currentConversationTitle = "New conversation";
    chatTranscript.replaceChildren();

    resetFileSelection();
    resetAnswer();
    showAuthScreen();
    setAuthMode("login");
    setAuthStatus("You have been logged out.");
});

async function checkLogin() {
    try {
        const response = await fetch("/api/auth/me", {
            credentials: "same-origin"
        });

        const data = await response.json();

        if (response.ok && data.success && data.user) {
            showDashboard(data.user);
        } else {
            showAuthScreen();
        }
    } catch (error) {
        showAuthScreen();
        setAuthStatus(
            "Could not check your session. Please log in.",
            true
        );
    }
}

// =====================================================
// API HELPER
// =====================================================

async function apiRequest(url, options = {}) {
    const response = await fetch(url, {
        credentials: "same-origin",
        ...options,
        headers: {
            ...(options.headers || {})
        }
    });

    const data = await response.json().catch(() => ({}));

    if (response.status === 401) {
        showAuthScreen();
        setAuthStatus("Your session expired. Please log in again.", true);
        throw new Error("Please log in again.");
    }

    if (!response.ok) {
        throw new Error(data.error || "Request failed.");
    }

    return data;
}

// =====================================================
// DOCUMENT UI STATE
// =====================================================

function clearDisplayedDocument() {
    selectedPdf = null;
    documentUploaded = false;

    pdfFile.value = "";
    selectedFile.classList.add("hidden");
    documentInfo.classList.add("hidden");
    uploadProgress.classList.add("hidden");

    uploadButton.disabled = true;
    askButton.disabled = true;

    fileName.textContent = "";
    fileSize.textContent = "";
    documentDetails.textContent = "";

    clearUploadStatus();
}

function showSavedDocument(document) {
    selectedPdf = null;
    pdfFile.value = "";

    selectedFile.classList.add("hidden");
    uploadButton.disabled = true;

    documentUploaded = true;
    askButton.disabled = false;

    documentInfo.classList.remove("hidden");

    documentDetails.textContent =
        `${document.filename} • ${document.chunks ?? "?"} chunks indexed`;
}

// =====================================================
// CONVERSATION HISTORY
// =====================================================

async function loadConversations() {
    historyList.replaceChildren();
    historyMessage.textContent = "Loading chats...";

    try {
        const data = await apiRequest("/api/conversations");

        historyList.replaceChildren();

        if (!data.conversations || data.conversations.length === 0) {
            historyMessage.textContent =
                "No conversations in the last 7 days.";
            return;
        }

        historyMessage.textContent = "";

        data.conversations.forEach((conversation) => {
            const button = document.createElement("button");

            button.type = "button";
            button.className = "history-chat";
            button.textContent = conversation.title || "New conversation";
            button.title = button.textContent;

            if (conversation.id === currentConversationId) {
                button.classList.add("active");
            }

            button.addEventListener("click", () => {
                openConversation(conversation.id);
            });

            historyList.appendChild(button);
        });

    } catch (error) {
        historyMessage.textContent =
            error.message === "Please log in again."
                ? ""
                : "Could not load chat history.";
    }
}

async function createConversation(title = "New conversation") {
    const data = await apiRequest("/api/conversations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title })
    });

    currentConversationId = data.conversation_id;
    currentConversationTitle = data.title || title;

    await loadConversations();

    return currentConversationId;
}

async function saveChatMessage(role, content) {
    if (!currentConversationId) {
        await createConversation(
            role === "user"
                ? content.slice(0, 60)
                : "New conversation"
        );
    }

    await apiRequest(
        `/api/conversations/${encodeURIComponent(currentConversationId)}/messages`,
        {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ role, content })
        }
    );

    await loadConversations();
}

async function openConversation(conversationId) {
    const loadToken = ++conversationLoadToken;

    // Immediately clear the previous conversation's document UI.
    currentConversationId = conversationId;
    clearDisplayedDocument();
    resetAnswer();
    chatTranscript.replaceChildren();

    question.value = "";
    updateCharacterCount();

    historyMessage.textContent = "Loading conversation...";

    try {
        const data = await apiRequest(
            `/api/conversations/${encodeURIComponent(conversationId)}/messages`
        );

        // Ignore results from a conversation that is no longer selected.
        if (
            loadToken !== conversationLoadToken ||
            currentConversationId !== conversationId
        ) {
            return;
        }

        currentConversationTitle =
            data.conversation?.title || "Conversation";

        (data.messages || []).forEach((message) => {
            addChatBubble(message.role, message.content);
        });

        historyMessage.textContent = "Checking saved PDF...";

        const documentData = await apiRequest(
            `/api/conversations/${encodeURIComponent(conversationId)}/document`
        );

        if (
            loadToken !== conversationLoadToken ||
            currentConversationId !== conversationId
        ) {
            return;
        }

        if (documentData.document) {
            showSavedDocument(documentData.document);
            historyMessage.textContent = "Conversation and PDF loaded.";
        } else {
            clearDisplayedDocument();
            historyMessage.textContent =
                "History loaded. Upload a PDF to ask new questions.";
        }

        const messages = data.messages || [];

        if (messages.length > 0) {
            const lastAssistantMessage = [...messages]
                .reverse()
                .find((message) => message.role === "assistant");

            if (lastAssistantMessage) {
                answer.textContent = lastAssistantMessage.content;
                source.textContent = "Loaded from saved chat history";

                emptyAnswer.classList.add("hidden");
                answerLoading.classList.add("hidden");
                answerContent.classList.remove("hidden");
                copyButton.disabled = false;
            }
        }

        await loadConversations();

    } catch (error) {
        if (loadToken !== conversationLoadToken) {
            return;
        }

        clearDisplayedDocument();
        historyMessage.textContent =
            `Could not load conversation: ${error.message}`;
    }
}

newChatButton.addEventListener("click", () => {
    conversationLoadToken++;

    currentConversationId = null;
    currentConversationTitle = "New conversation";

    chatTranscript.replaceChildren();
    clearDisplayedDocument();
    resetAnswer();

    historyMessage.textContent =
        "New chat ready. Upload a PDF to begin.";

    question.value = "";
    updateCharacterCount();

    loadConversations();
});

function addChatBubble(role, content) {
    const bubble = document.createElement("div");

    bubble.className = `chat-bubble ${
        role === "user" ? "user" : "assistant"
    }`;

    const label = document.createElement("div");
    label.className = "chat-role";
    label.textContent = role === "user" ? "You" : "DocuMind AI";

    const text = document.createElement("div");
    text.textContent = content;

    bubble.append(label, text);
    chatTranscript.appendChild(bubble);

    bubble.scrollIntoView({
        behavior: "smooth",
        block: "nearest"
    });
}

// =====================================================
// PDF UPLOAD
// =====================================================

function formatFileSize(bytes) {
    if (bytes === 0) return "0 Bytes";

    const units = ["Bytes", "KB", "MB", "GB"];
    const index = Math.floor(Math.log(bytes) / Math.log(1024));

    return `${(bytes / Math.pow(1024, index)).toFixed(2)} ${units[index]}`;
}

function showUploadStatus(message, type = "info") {
    uploadStatus.textContent = message;
    uploadStatus.style.color =
        type === "error" ? "#fca5a5" :
        type === "success" ? "#86efac" : "#93c5fd";
}

function showUploadError(message) {
    showUploadStatus(`✕ ${message}`, "error");
}

function showUploadSuccess(message) {
    showUploadStatus(`✓ ${message}`, "success");
}

function showAnswerError(message) {
    answerStatus.textContent = `✕ ${message}`;
    answerStatus.style.color = "#fca5a5";
}

function clearUploadStatus() {
    uploadStatus.textContent = "";
    uploadStatus.style.color = "";
}

function resetFileSelection() {
    clearDisplayedDocument();
}

function resetAnswer() {
    emptyAnswer.classList.remove("hidden");
    answerLoading.classList.add("hidden");
    answerContent.classList.add("hidden");

    answer.textContent = "";
    source.textContent = "";
    answerStatus.textContent = "";
    copyButton.disabled = true;
}

function handleFile(file) {
    clearUploadStatus();

    documentUploaded = false;
    askButton.disabled = true;
    documentInfo.classList.add("hidden");
    resetAnswer();

    const isPdf = file.type === "application/pdf" ||
        file.name.toLowerCase().endsWith(".pdf");

    if (!isPdf) {
        showUploadError("Please select a PDF file.");
        selectedPdf = null;
        uploadButton.disabled = true;
        selectedFile.classList.add("hidden");
        return;
    }

    if (file.size > MAX_FILE_SIZE) {
        showUploadError("File is too large. Maximum size is 20 MB.");
        selectedPdf = null;
        uploadButton.disabled = true;
        selectedFile.classList.add("hidden");
        return;
    }

    selectedPdf = file;

    fileName.textContent = file.name;
    fileSize.textContent = formatFileSize(file.size);

    selectedFile.classList.remove("hidden");
    uploadButton.disabled = false;

    showUploadStatus("PDF selected and ready to upload.", "info");
}

browseButton.addEventListener("click", () => pdfFile.click());

pdfFile.addEventListener("change", () => {
    if (pdfFile.files && pdfFile.files.length > 0) {
        handleFile(pdfFile.files[0]);
    }
});

removeFileButton.addEventListener("click", () => {
    selectedPdf = null;
    pdfFile.value = "";

    selectedFile.classList.add("hidden");
    uploadButton.disabled = true;

    clearUploadStatus();
});

["dragenter", "dragover"].forEach((eventName) => {
    dropZone.addEventListener(eventName, (event) => {
        event.preventDefault();
        event.stopPropagation();
        dropZone.classList.add("drag-over");
    });
});

["dragleave", "drop"].forEach((eventName) => {
    dropZone.addEventListener(eventName, (event) => {
        event.preventDefault();
        event.stopPropagation();
        dropZone.classList.remove("drag-over");
    });
});

dropZone.addEventListener("drop", (event) => {
    const files = event.dataTransfer.files;

    if (files && files.length > 0) {
        handleFile(files[0]);
    }
});

document.addEventListener("dragover", (event) => event.preventDefault());
document.addEventListener("drop", (event) => event.preventDefault());

// =====================================================
// UPLOAD HANDLER
// =====================================================

uploadButton.addEventListener("click", async () => {
    if (!currentUser) {
        showUploadError("Please log in first.");
        return;
    }

    if (!selectedPdf || isUploading) return;

    isUploading = true;
    uploadButton.disabled = true;
    uploadButton.textContent = "Processing...";

    uploadProgress.classList.remove("hidden");
    showUploadStatus("Uploading and analyzing your PDF...", "info");

    try {
        if (!currentConversationId) {
            await createConversation(
                selectedPdf.name.replace(/\.pdf$/i, "").slice(0, 60)
            );
        }

        if (!currentConversationId) {
            throw new Error(
                "Could not create a conversation. Please click New chat and try again."
            );
        }

        const uploadConversationId = currentConversationId;
        const uploadFile = selectedPdf;
        const formData = new FormData();

        formData.append("file", uploadFile);
        formData.append("conversation_id", uploadConversationId);

        const data = await apiRequest("/upload", {
            method: "POST",
            body: formData
        });

        // Do not let an upload for an old chat overwrite the newly selected chat.
        if (currentConversationId !== uploadConversationId) {
            await loadConversations();
            return;
        }

        documentUploaded = true;
        askButton.disabled = false;

        documentInfo.classList.remove("hidden");

        documentDetails.textContent =
            `${data.filename} • ${data.chunks_created} chunks indexed`;

        showUploadSuccess(
            `PDF ready! ${data.pages} pages, ${data.chunks_created} chunks indexed.`
        );

        await loadConversations();
        question.focus();

    } catch (error) {
        if (currentConversationId) {
            showUploadError(error.message || "Unable to upload PDF.");
        }
    } finally {
        isUploading = false;
        uploadProgress.classList.add("hidden");

        uploadButton.disabled = !selectedPdf;
        uploadButton.innerHTML =
            '<span class="button-icon">↑</span> Upload &amp; Analyze';
    }
});

// =====================================================
// ASK QUESTIONS AND SAVE HISTORY
// =====================================================
async function askQuestion() {
    if (!currentUser) {
        showAnswerError("Please log in first.");
        return;
    }

    if (isAsking) return;

    if (!documentUploaded || !currentConversationId) {
        showAnswerError("Upload a document to this conversation first.");
        return;
    }

    const userQuestion = question.value.trim();

    if (!userQuestion) {
        showAnswerError("Please enter a question.");
        question.focus();
        return;
    }

    isAsking = true;
    askButton.disabled = true;
    askButton.textContent = "Thinking...";

    answerStatus.textContent =
        "Searching the document and generating an answer...";
    answerStatus.style.color = "#93c5fd";

    emptyAnswer.classList.add("hidden");
    answerContent.classList.add("hidden");
    answerLoading.classList.remove("hidden");
    copyButton.disabled = true;

    const questionConversationId = currentConversationId;

    addChatBubble("user", userQuestion);

    try {
        await saveChatMessage("user", userQuestion);

        const response = await fetch("/ask", {
            method: "POST",
            credentials: "same-origin",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                question: userQuestion,
                conversation_id: questionConversationId
            })
        });

        const data = await response.json();

        if (response.status === 401) {
            showAuthScreen();
            setAuthStatus("Please log in again.", true);
            return;
        }

        if (!response.ok) {
            throw new Error(
                data.error || "Unable to generate an answer."
            );
        }

        // Avoid displaying a response in a different conversation.
        if (currentConversationId !== questionConversationId) {
            return;
        }

        const aiAnswer = data.answer || "No answer was generated.";

        addChatBubble("assistant", aiAnswer);
        await saveChatMessage("assistant", aiAnswer);

        answer.textContent = aiAnswer;

        source.textContent = data.filename
            ? `Source document: ${data.filename}`
            : "Source: Uploaded document";

        answerLoading.classList.add("hidden");
        answerContent.classList.remove("hidden");
        copyButton.disabled = false;

        answerStatus.textContent = "✓ Answer generated and saved.";
        answerStatus.style.color = "#86efac";

    } catch (error) {
        if (currentConversationId === questionConversationId) {
            answerLoading.classList.add("hidden");
            answerContent.classList.remove("hidden");

            answer.textContent = "Unable to complete the request.";
            source.textContent = "";

            showAnswerError(error.message || "Question failed.");
        }
    } finally {
        isAsking = false;

        if (currentConversationId === questionConversationId) {
            askButton.disabled = !documentUploaded;
            askButton.innerHTML = "<span>✦</span> Ask AI";
        }
    }
}

askButton.addEventListener("click", askQuestion);

suggestionChips.forEach((chip) => {
    chip.addEventListener("click", () => {
        question.value = chip.dataset.question || "";
        updateCharacterCount();

        if (documentUploaded) {
            askQuestion();
        } else {
            showAnswerError(
                "Upload a document first, then ask this question."
            );
        }
    });
});

question.addEventListener("input", updateCharacterCount);

question.addEventListener("keydown", (event) => {
    if (event.ctrlKey && event.key === "Enter") {
        event.preventDefault();
        askQuestion();
    }
});

function updateCharacterCount() {
    characterCount.textContent = `${question.value.length} / 1000`;
}

// =====================================================
// COPY ANSWER
// =====================================================

copyButton.addEventListener("click", async () => {
    const text = answer.textContent.trim();

    if (!text) return;

    try {
        await navigator.clipboard.writeText(text);

        const originalText = copyButton.textContent;
        copyButton.textContent = "✓ Copied";

        setTimeout(() => {
            copyButton.textContent = originalText;
        }, 1500);

    } catch (error) {
        console.error("Copy failed:", error);
        showAnswerError("Could not copy the answer.");
    }
});

// =====================================================
// START APPLICATION
// =====================================================

uploadButton.disabled = true;
askButton.disabled = true;
copyButton.disabled = true;

updateCharacterCount();
setAuthMode("login");
checkLogin();