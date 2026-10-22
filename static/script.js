
"use strict";

// =====================================================
// APPLICATION STATE
// =====================================================

let currentUser = null;
let currentConversationId = null;
let selectedPdf = null;
let documentUploaded = false;
let isUploading = false;
let isAsking = false;
let isGeneratingInsights = false;
let conversationLoadToken = 0;

const MAX_FILE_SIZE = 20 * 1024 * 1024;

// =====================================================
// DOM REFERENCES
// =====================================================

const $ = (id) => document.getElementById(id);

const authScreen = $("authScreen");
const appShell = $("appShell");
const authForm = $("authForm");
const authTitle = $("authTitle");
const authDescription = $("authDescription");
const authName = $("authName");
const nameField = $("nameField");
const authEmail = $("authEmail");
const authPassword = $("authPassword");
const authSubmit = $("authSubmit");
const authStatus = $("authStatus");
const authSwitch = $("authSwitch");
const authSwitchText = $("authSwitchText");
const logoutButton = $("logoutButton");
const loggedInName = $("loggedInName");

const pdfFile = $("pdfFile");
const dropZone = $("dropZone");
const browseButton = $("browseButton");
const uploadButton = $("uploadButton");
const removeFileButton = $("removeFileButton");
const selectedFile = $("selectedFile");
const fileName = $("fileName");
const fileSize = $("fileSize");
const uploadStatus = $("uploadStatus");
const uploadProgress = $("uploadProgress");
const documentInfo = $("documentInfo");
const documentDetails = $("documentDetails");

const question = $("question");
const askButton = $("askButton");
const answerStatus = $("answerStatus");
const answer = $("answer");
const source = $("source");
const emptyAnswer = $("emptyAnswer");
const answerLoading = $("answerLoading");
const answerContent = $("answerContent");
const copyButton = $("copyButton");
const characterCount = $("characterCount");
const suggestionChips = document.querySelectorAll(".suggestion-chip");

const learningLevel = $("learningLevel");

const insightsCard = $("insightsCard");
const insightsLoading = $("insightsLoading");
const insightsError = $("insightsError");
const insightsContent = $("insightsContent");
const insightsSummary = $("insightsSummary");
const insightsTakeaways = $("insightsTakeaways");
const insightsTerms = $("insightsTerms");
const insightsFindings = $("insightsFindings");

let authMode = "login";

// =====================================================
// CHAT HISTORY UI
// =====================================================

const historyStyles = document.createElement("style");

historyStyles.textContent = `
#chatHistorySection { margin-top:24px; }
#newChatButton {
    width:100%; padding:11px; margin:10px 0 14px;
    border:1px solid rgba(255,255,255,.2);
    border-radius:9px; color:inherit;
    background:rgba(255,255,255,.06);
    cursor:pointer; font:inherit;
}
#historyList {
    display:flex; flex-direction:column; gap:6px;
    max-height:280px; overflow-y:auto;
}
.history-chat {
    width:100%; padding:10px; border:0;
    border-radius:8px; background:transparent;
    color:inherit; text-align:left; cursor:pointer;
    font:inherit; overflow-wrap:anywhere;
}
.history-chat.active,
.history-chat:hover,
#newChatButton:hover {
    background:rgba(139,128,255,.2);
}
#historyMessage { color:#aeb6ce; font-size:12px; margin:8px 0; }
#chatTranscript {
    display:flex; flex-direction:column; gap:14px; margin:20px 0;
}
.chat-bubble {
    padding:14px 16px; border-radius:14px;
    max-width:90%; white-space:pre-wrap;
    overflow-wrap:anywhere; line-height:1.6;
}
.chat-bubble.user {
    align-self:flex-end;
    background:rgba(116,101,255,.2);
    border:1px solid rgba(139,128,255,.35);
}
.chat-bubble.assistant {
    align-self:flex-start;
    background:rgba(255,255,255,.06);
    border:1px solid rgba(255,255,255,.12);
}
.chat-role {
    font-size:11px; font-weight:700;
    text-transform:uppercase; opacity:.7; margin-bottom:5px;
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
    <p id="historyMessage" role="status"></p>
`;

const sidebarDivider = sidebar?.querySelector(".sidebar-divider");

if (sidebarDivider) {
    sidebarDivider.insertAdjacentElement("afterend", historySection);
} else if (sidebar) {
    sidebar.appendChild(historySection);
}

const newChatButton = $("newChatButton");
const historyList = $("historyList");
const historyMessage = $("historyMessage");

const answerCard = $("answerCard");
const chatTranscript = document.createElement("div");
chatTranscript.id = "chatTranscript";

if (answerCard) {
    answerCard.insertAdjacentElement("afterbegin", chatTranscript);
}

// =====================================================
// STATUS HELPERS
// =====================================================

function setAuthStatus(message, isError = false) {
    authStatus.textContent = message;
    authStatus.style.color = isError ? "#fca5a5" : "#86efac";
}

function showUploadStatus(message, type = "info") {
    uploadStatus.textContent = message;
    uploadStatus.style.color =
        type === "error" ? "#fca5a5" :
        type === "success" ? "#86efac" : "#93c5fd";
}

function showUploadError(message) {
    showUploadStatus("✕ " + message, "error");
}

function showUploadSuccess(message) {
    showUploadStatus("✓ " + message, "success");
}

function showAnswerError(message) {
    answerStatus.textContent = "✕ " + message;
    answerStatus.style.color = "#fca5a5";
}

function clearUploadStatus() {
    uploadStatus.textContent = "";
    uploadStatus.style.color = "";
}

// =====================================================
// API HELPER
// =====================================================

async function apiRequest(url, options = {}) {
    const response = await fetch(url, {
        credentials: "same-origin",
        ...options,
        headers: { ...(options.headers || {}) }
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
// AUTHENTICATION
// =====================================================

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
    clearInsightsUI();

    currentConversationId = null;
    chatTranscript.replaceChildren();

    loadConversations();
}

function setAuthMode(mode) {
    authMode = mode;
    authForm.reset();
    setAuthStatus("");

    const registering = mode === "register";

    authTitle.textContent = registering
        ? "Create your account" : "Welcome back";

    authDescription.textContent = registering
        ? "Register to start using DocuMind AI."
        : "Sign in to upload documents and ask questions.";

    nameField.hidden = !registering;
    authName.required = registering;

    authSubmit.textContent = registering
        ? "Create account" : "Log in";

    authSwitchText.textContent = registering
        ? "Already have an account?" : "Don't have an account?";

    authSwitch.textContent = registering ? "Log in" : "Register";
    authPassword.autocomplete = registering
        ? "new-password" : "current-password";
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
        setAuthStatus("Password must contain at least 8 characters.", true);
        return;
    }

    authSubmit.disabled = true;
    authSubmit.textContent = "Please wait...";

    try {
        const endpoint = authMode === "register"
            ? "/api/auth/register" : "/api/auth/login";

        const payload = authMode === "register"
            ? { name, email, password } : { email, password };

        const data = await apiRequest(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (authMode === "register") {
            setAuthMode("login");
            authEmail.value = email;
            setAuthStatus("Account created! Please log in.");
            return;
        }

        showDashboard(data.user);

    } catch (error) {
        setAuthStatus(error.message, true);
    } finally {
        authSubmit.disabled = false;
        authSubmit.textContent =
            authMode === "register" ? "Create account" : "Log in";
    }
});

logoutButton.addEventListener("click", async () => {
    try {
        await apiRequest("/api/auth/logout", { method: "POST" });
    } catch (error) {
        console.error("Logout failed:", error);
    }

    conversationLoadToken++;
    currentConversationId = null;
    chatTranscript.replaceChildren();
    resetFileSelection();
    resetAnswer();
    clearInsightsUI();
    showAuthScreen();
    setAuthMode("login");
    setAuthStatus("You have been logged out.");
});

async function checkLogin() {
    try {
        const data = await apiRequest("/api/auth/me");

        if (data.success && data.user) {
            showDashboard(data.user);
        } else {
            showAuthScreen();
        }
    } catch {
        showAuthScreen();
    }
}

// =====================================================
// CONVERSATIONS
// =====================================================

async function loadConversations() {
    historyList.replaceChildren();
    historyMessage.textContent = "Loading chats...";

    try {
        const data = await apiRequest("/api/conversations");
        historyList.replaceChildren();

        if (!data.conversations?.length) {
            historyMessage.textContent = "No conversations in the last 7 days.";
            return;
        }

        historyMessage.textContent = "";

        data.conversations.forEach((conversation) => {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "history-chat";
            button.textContent = conversation.title || "New conversation";

            if (conversation.id === currentConversationId) {
                button.classList.add("active");
            }

            button.addEventListener("click", () => {
                openConversation(conversation.id);
            });

            historyList.appendChild(button);
        });
    } catch (error) {
        historyMessage.textContent = "Could not load chat history.";
    }
}

async function createConversation(title = "New conversation") {
    const data = await apiRequest("/api/conversations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title })
    });

    currentConversationId = data.conversation_id;
    await loadConversations();
    return currentConversationId;
}

async function saveChatMessage(role, content) {
    if (!currentConversationId) {
        await createConversation(
            role === "user" ? content.slice(0, 60) : "New conversation"
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
    const token = ++conversationLoadToken;

    currentConversationId = conversationId;
    clearDisplayedDocument();
    resetAnswer();
    clearInsightsUI();
    chatTranscript.replaceChildren();
    question.value = "";
    updateCharacterCount();

    try {
        const data = await apiRequest(
            `/api/conversations/${encodeURIComponent(conversationId)}/messages`
        );

        if (token !== conversationLoadToken) return;

        (data.messages || []).forEach((message) => {
            addChatBubble(message.role, message.content);
        });

        const documentData = await apiRequest(
            `/api/conversations/${encodeURIComponent(conversationId)}/document`
        );

        if (token !== conversationLoadToken) return;

        if (documentData.document) {
            showSavedDocument(documentData.document);
            historyMessage.textContent = "Conversation and PDF loaded.";

            // Generate insights for an existing uploaded PDF too.
            generateDocumentInsights(conversationId);
        } else {
            historyMessage.textContent = "Upload a PDF to ask questions.";
        }

        const lastAnswer = [...(data.messages || [])]
            .reverse()
            .find((message) => message.role === "assistant");

        if (lastAnswer) {
            answer.textContent = lastAnswer.content;
            source.textContent = "Loaded from saved chat history";
            emptyAnswer.classList.add("hidden");
            answerLoading.classList.add("hidden");
            answerContent.classList.remove("hidden");
            copyButton.disabled = false;
        }

        await loadConversations();

    } catch (error) {
        if (token === conversationLoadToken) {
            historyMessage.textContent =
                `Could not load conversation: ${error.message}`;
        }
    }
}

newChatButton.addEventListener("click", () => {
    conversationLoadToken++;
    currentConversationId = null;
    chatTranscript.replaceChildren();
    clearDisplayedDocument();
    resetAnswer();
    clearInsightsUI();
    question.value = "";
    updateCharacterCount();
    historyMessage.textContent = "New chat ready. Upload a PDF to begin.";
    loadConversations();
});

function addChatBubble(role, content) {
    const bubble = document.createElement("div");
    bubble.className =
        `chat-bubble ${role === "user" ? "user" : "assistant"}`;

    const label = document.createElement("div");
    label.className = "chat-role";
    label.textContent = role === "user" ? "You" : "DocuMind AI";

    const text = document.createElement("div");
    text.textContent = content;

    bubble.append(label, text);
    chatTranscript.appendChild(bubble);
    bubble.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

// =====================================================
// DOCUMENT UI
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
    clearInsightsUI();
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

function formatFileSize(bytes) {
    if (bytes === 0) return "0 Bytes";
    const units = ["Bytes", "KB", "MB", "GB"];
    const index = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, index)).toFixed(2)} ${units[index]}`;
}

function handleFile(file) {
    clearUploadStatus();
    documentUploaded = false;
    askButton.disabled = true;
    documentInfo.classList.add("hidden");
    resetAnswer();
    clearInsightsUI();

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
    if (pdfFile.files?.length) handleFile(pdfFile.files[0]);
});

removeFileButton.addEventListener("click", () => {
    selectedPdf = null;
    pdfFile.value = "";
    selectedFile.classList.add("hidden");
    uploadButton.disabled = true;
    clearUploadStatus();
});

["dragenter", "dragover"].forEach((name) => {
    dropZone.addEventListener(name, (event) => {
        event.preventDefault();
        event.stopPropagation();
        dropZone.classList.add("drag-over");
    });
});

["dragleave", "drop"].forEach((name) => {
    dropZone.addEventListener(name, (event) => {
        event.preventDefault();
        event.stopPropagation();
        dropZone.classList.remove("drag-over");
    });
});

dropZone.addEventListener("drop", (event) => {
    if (event.dataTransfer.files.length) {
        handleFile(event.dataTransfer.files[0]);
    }
});

document.addEventListener("dragover", (event) => event.preventDefault());
document.addEventListener("drop", (event) => event.preventDefault());

// =====================================================
// SMART DOCUMENT INSIGHTS
// =====================================================

function clearInsightsUI() {
    if (insightsLoading) insightsLoading.classList.add("hidden");

    if (insightsError) {
        insightsError.textContent = "";
        insightsError.classList.add("hidden");
    }

    if (insightsContent) insightsContent.classList.add("hidden");
    if (insightsCard) insightsCard.classList.add("hidden");

    if (insightsSummary) insightsSummary.textContent = "";
    if (insightsTakeaways) insightsTakeaways.replaceChildren();
    if (insightsTerms) insightsTerms.replaceChildren();
    if (insightsFindings) insightsFindings.replaceChildren();
}

function appendInsightItem(container, content) {
    const item = document.createElement("li");
    item.textContent = content;
    container.appendChild(item);
}

function renderInsights(data) {
    const requiredElements = [
        insightsCard,
        insightsContent,
        insightsSummary,
        insightsTakeaways,
        insightsTerms,
        insightsFindings
    ];

    if (requiredElements.some((element) => !element)) {
        throw new Error(
            "Smart Insights HTML is missing. Check templates/index.html."
        );
    }

    insightsSummary.textContent =
        data.summary || "No summary available.";

    insightsTakeaways.replaceChildren();

    (data.key_takeaways || []).forEach((item) => {
        appendInsightItem(insightsTakeaways, String(item));
    });

    insightsTerms.replaceChildren();

    (data.important_terms || []).forEach((item) => {
        if (typeof item === "object" && item !== null) {
            const li = document.createElement("li");
            const strong = document.createElement("strong");
            strong.textContent = String(item.term || "Term");

            const definition = document.createElement("span");
            definition.textContent =
                ` — ${String(item.definition || "")}`;

            li.append(strong, definition);
            insightsTerms.appendChild(li);
        } else {
            appendInsightItem(insightsTerms, String(item));
        }
    });

    insightsFindings.replaceChildren();

    (data.major_findings || []).forEach((item) => {
        appendInsightItem(insightsFindings, String(item));
    });

    insightsCard.classList.remove("hidden");
    insightsContent.classList.remove("hidden");
}

async function generateDocumentInsights(conversationId) {
    if (!conversationId || isGeneratingInsights) return;

    isGeneratingInsights = true;

    if (insightsCard) insightsCard.classList.remove("hidden");
    if (insightsLoading) insightsLoading.classList.remove("hidden");

    if (insightsContent) insightsContent.classList.add("hidden");

    if (insightsError) {
        insightsError.textContent = "";
        insightsError.classList.add("hidden");
    }

    try {
        const data = await apiRequest(
            `/api/conversations/${encodeURIComponent(conversationId)}/insights`,
            { method: "POST" }
        );

        if (currentConversationId !== conversationId) return;

        renderInsights(data);

    } catch (error) {
        if (currentConversationId === conversationId && insightsError) {
            insightsError.textContent = error.message;
            insightsError.classList.remove("hidden");
            insightsCard?.classList.remove("hidden");
        }
    } finally {
        isGeneratingInsights = false;
        insightsLoading?.classList.add("hidden");
    }
}

// =====================================================
// PDF UPLOAD HANDLER
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
            throw new Error("Could not create a conversation.");
        }

        const uploadConversationId = currentConversationId;
        const formData = new FormData();

        formData.append("file", selectedPdf);
        formData.append("conversation_id", uploadConversationId);

        const data = await apiRequest("/upload", {
            method: "POST",
            body: formData
        });

        if (currentConversationId !== uploadConversationId) return;

        documentUploaded = true;
        askButton.disabled = false;
        documentInfo.classList.remove("hidden");

        documentDetails.textContent =
            `${data.filename} • ${data.chunks_created} chunks indexed`;

        showUploadSuccess(
            `PDF ready! ${data.pages} pages, ${data.chunks_created} chunks indexed.`
        );

        await loadConversations();

        // Automatically generate insights after uploading the PDF.
        await generateDocumentInsights(uploadConversationId);

        question.focus();

    } catch (error) {
        showUploadError(error.message || "Unable to upload PDF.");
    } finally {
        isUploading = false;
        uploadProgress.classList.add("hidden");
        uploadButton.disabled = !selectedPdf;
        uploadButton.innerHTML =
            '<span class="button-icon">↑</span> Upload &amp; Analyze';
    }
});

// =====================================================
// ASK QUESTIONS WITH ADAPTIVE LEARNING MODE
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

    const conversationId = currentConversationId;
    addChatBubble("user", userQuestion);

    try {
        await saveChatMessage("user", userQuestion);

        const data = await apiRequest("/ask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                question: userQuestion,
                conversation_id: conversationId,
                learning_level: learningLevel?.value || "student"
            })
        });

        if (currentConversationId !== conversationId) return;

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
        if (currentConversationId === conversationId) {
            answerLoading.classList.add("hidden");
            answerContent.classList.remove("hidden");
            answer.textContent = "Unable to complete the request.";
            showAnswerError(error.message || "Question failed.");
        }
    } finally {
        isAsking = false;

        if (currentConversationId === conversationId) {
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
            showAnswerError("Upload a document first.");
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
    if (characterCount) {
        characterCount.textContent = `${question.value.length} / 1000`;
    }
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
        showAnswerError("Could not copy the answer.");
    }
});

// =====================================================
// START APPLICATION
// =====================================================

uploadButton.disabled = true;
askButton.disabled = true;
copyButton.disabled = true;

clearInsightsUI();
updateCharacterCount();
setAuthMode("login");
checkLogin();
