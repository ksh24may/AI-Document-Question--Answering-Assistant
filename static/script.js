/* =========================================================
   DOCUMIND AI
   Frontend JavaScript
   ========================================================= */


/* =========================================================
   GET ELEMENTS
   ========================================================= */

const pdfFile =
    document.getElementById("pdfFile");

const dropZone =
    document.getElementById("dropZone");

const browseButton =
    document.getElementById("browseButton");

const uploadButton =
    document.getElementById("uploadButton");

const removeFileButton =
    document.getElementById("removeFileButton");

const selectedFile =
    document.getElementById("selectedFile");

const fileName =
    document.getElementById("fileName");

const fileSize =
    document.getElementById("fileSize");

const uploadStatus =
    document.getElementById("uploadStatus");

const uploadProgress =
    document.getElementById("uploadProgress");

const documentInfo =
    document.getElementById("documentInfo");

const documentDetails =
    document.getElementById("documentDetails");

const question =
    document.getElementById("question");

const askButton =
    document.getElementById("askButton");

const answerStatus =
    document.getElementById("answerStatus");

const answer =
    document.getElementById("answer");

const source =
    document.getElementById("source");

const emptyAnswer =
    document.getElementById("emptyAnswer");

const answerLoading =
    document.getElementById("answerLoading");

const answerContent =
    document.getElementById("answerContent");

const copyButton =
    document.getElementById("copyButton");

const characterCount =
    document.getElementById("characterCount");

const suggestionChips =
    document.querySelectorAll(".suggestion-chip");


/* =========================================================
   APPLICATION STATE
   ========================================================= */

let selectedPdf = null;

let documentUploaded = false;

let isUploading = false;

let isAsking = false;


/* =========================================================
   CONSTANTS
   ========================================================= */

const MAX_FILE_SIZE =
    20 * 1024 * 1024;


/* =========================================================
   INITIAL STATE
   ========================================================= */

function initializeApp() {

    uploadButton.disabled = true;

    askButton.disabled = true;

    copyButton.disabled = true;

    updateCharacterCount();

}


initializeApp();


/* =========================================================
   OPEN FILE SELECTOR
   ========================================================= */

browseButton.addEventListener(
    "click",
    function () {

        pdfFile.click();

    }
);


/* =========================================================
   FILE SELECTED
   ========================================================= */

pdfFile.addEventListener(
    "change",
    function () {

        if (
            pdfFile.files &&
            pdfFile.files.length > 0
        ) {

            handleFile(
                pdfFile.files[0]
            );

        }

    }
);


/* =========================================================
   HANDLE FILE
   ========================================================= */

function handleFile(file) {

    clearUploadStatus();

    documentUploaded = false;

    askButton.disabled = true;

    documentInfo.classList.add(
        "hidden"
    );


    /* Check file type */

    const isPdf =
        file.type === "application/pdf" ||
        file.name.toLowerCase().endsWith(".pdf");


    if (!isPdf) {

        showUploadError(
            "Please select a PDF file."
        );

        resetFileSelection();

        return;
    }


    /* Check file size */

    if (file.size > MAX_FILE_SIZE) {

        showUploadError(
            "File is too large. Maximum size is 20 MB."
        );

        resetFileSelection();

        return;
    }


    /* Store file */

    selectedPdf = file;


    /* Show file information */

    fileName.textContent =
        file.name;

    fileSize.textContent =
        formatFileSize(file.size);


    selectedFile.classList.remove(
        "hidden"
    );


    uploadButton.disabled = false;


    showUploadStatus(
        "PDF selected and ready to upload.",
        "info"
    );

}


/* =========================================================
   FORMAT FILE SIZE
   ========================================================= */

function formatFileSize(bytes) {

    if (bytes === 0) {
        return "0 Bytes";
    }


    const units = [
        "Bytes",
        "KB",
        "MB",
        "GB"
    ];


    const index =
        Math.floor(
            Math.log(bytes) /
            Math.log(1024)
        );


    return (
        parseFloat(
            (
                bytes /
                Math.pow(1024, index)
            ).toFixed(2)
        )
        + " "
        + units[index]
    );

}


/* =========================================================
   REMOVE SELECTED FILE
   ========================================================= */

removeFileButton.addEventListener(
    "click",
    function () {

        resetFileSelection();

        clearUploadStatus();

    }
);


/* =========================================================
   RESET FILE SELECTION
   ========================================================= */

function resetFileSelection() {

    selectedPdf = null;

    documentUploaded = false;

    pdfFile.value = "";

    selectedFile.classList.add(
        "hidden"
    );

    uploadButton.disabled = true;

    askButton.disabled = true;

    documentInfo.classList.add(
        "hidden"
    );

}


/* =========================================================
   DRAG ENTER
   ========================================================= */

[
    "dragenter",
    "dragover"
].forEach(
    eventName => {

        dropZone.addEventListener(
            eventName,
            function (event) {

                event.preventDefault();

                event.stopPropagation();

                dropZone.classList.add(
                    "drag-over"
                );

            }
        );

    }
);


/* =========================================================
   DRAG LEAVE
   ========================================================= */

[
    "dragleave",
    "drop"
].forEach(
    eventName => {

        dropZone.addEventListener(
            eventName,
            function (event) {

                event.preventDefault();

                event.stopPropagation();

                dropZone.classList.remove(
                    "drag-over"
                );

            }
        );

    }
);


/* =========================================================
   DROP FILE
   ========================================================= */

dropZone.addEventListener(
    "drop",
    function (event) {

        const files =
            event.dataTransfer.files;


        if (
            files &&
            files.length > 0
        ) {

            handleFile(
                files[0]
            );

        }

    }
);


/* =========================================================
   UPLOAD PDF
   ========================================================= */

uploadButton.addEventListener(
    "click",
    async function () {

        if (!selectedPdf) {

            showUploadError(
                "Please select a PDF first."
            );

            return;
        }


        if (isUploading) {
            return;
        }


        isUploading = true;

        uploadButton.disabled = true;

        uploadButton.innerHTML =
            "⏳ Processing...";


        uploadProgress.classList.remove(
            "hidden"
        );


        showUploadStatus(
            "Uploading and analyzing your document...",
            "info"
        );


        try {

            const formData =
                new FormData();


            formData.append(
                "file",
                selectedPdf
            );


            const response =
                await fetch(
                    "/upload",
                    {
                        method: "POST",
                        body: formData
                    }
                );


            const data =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    data.error ||
                    "Unable to upload document."
                );

            }


            /* Success */

            documentUploaded = true;


            askButton.disabled = false;


            uploadProgress.classList.add(
                "hidden"
            );


            documentInfo.classList.remove(
                "hidden"
            );


            documentDetails.textContent =
                `${data.filename} • ${data.chunks_created} chunks indexed`;


            showUploadSuccess(
                `Document ready! ${data.chunks_created} text chunks were indexed.`
            );


            /* Reset answer */

            resetAnswer();


            /* Focus question */

            question.focus();


        } catch (error) {

            documentUploaded = false;

            askButton.disabled = true;


            uploadProgress.classList.add(
                "hidden"
            );


            showUploadError(
                error.message
            );


        } finally {

            isUploading = false;

            uploadButton.disabled =
                !selectedPdf;

            uploadButton.innerHTML =
                '<span class="button-icon">↑</span> Upload & Analyze';

        }

    }
);


/* =========================================================
   ASK QUESTION
   ========================================================= */

askButton.addEventListener(
    "click",
    askQuestion
);


async function askQuestion() {

    if (isAsking) {
        return;
    }


    if (!documentUploaded) {

        showAnswerError(
            "Please upload a document first."
        );

        return;
    }


    const userQuestion =
        question.value.trim();


    if (!userQuestion) {

        showAnswerError(
            "Please enter a question."
        );

        question.focus();

        return;
    }


    isAsking = true;

    askButton.disabled = true;

    askButton.innerHTML =
        "⏳ Thinking...";


    answerStatus.textContent =
        "Searching the document and generating an answer...";

    answerStatus.style.color =
        "#93c5fd";


    /* Show loading UI */

    emptyAnswer.classList.add(
        "hidden"
    );

    answerContent.classList.add(
        "hidden"
    );

    answerLoading.classList.remove(
        "hidden"
    );

    copyButton.disabled = true;


    try {

        const response =
            await fetch(
                "/ask",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        question:
                            userQuestion
                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.error ||
                "Unable to generate answer."
            );

        }


        /* Hide loading */

        answerLoading.classList.add(
            "hidden"
        );


        /* Show answer */

        answerContent.classList.remove(
            "hidden"
        );


        answer.textContent =
            data.answer ||
            "No answer was generated.";


        /* Source */

        if (data.filename) {

            source.textContent =
                `Source document: ${data.filename}`;

        } else {

            source.textContent =
                "Source: Uploaded document";

        }


        /* Enable copy */

        copyButton.disabled = false;


        answerStatus.textContent =
            "✓ Answer generated successfully.";

        answerStatus.style.color =
            "#86efac";


        /* Scroll to answer */

        setTimeout(
            function () {

                answerContent.scrollIntoView({
                    behavior: "smooth",
                    block: "center"
                });

            },
            100
        );


    } catch (error) {

        answerLoading.classList.add(
            "hidden"
        );

        answerContent.classList.remove(
            "hidden"
        );


        answer.textContent =
            "Unable to generate an answer.";


        source.textContent = "";


        copyButton.disabled = true;


        showAnswerError(
            error.message
        );


    } finally {

        isAsking = false;

        askButton.disabled =
            !documentUploaded;

        askButton.innerHTML =
            "<span>✦</span> Ask AI";

    }

}


/* =========================================================
   EXAMPLE QUESTIONS
   ========================================================= */

suggestionChips.forEach(
    chip => {

        chip.addEventListener(
            "click",
            function () {

                const text =
                    chip.dataset.question;


                question.value =
                    text;


                updateCharacterCount();


                question.focus();


                if (documentUploaded) {

                    askQuestion();

                } else {

                    showAnswerError(
                        "Upload a document first, then ask this question."
                    );

                }

            }
        );

    }
);


/* =========================================================
   CHARACTER COUNTER
   ========================================================= */

question.addEventListener(
    "input",
    updateCharacterCount
);


function updateCharacterCount() {

    const length =
        question.value.length;


    characterCount.textContent =
        `${length} / 1000`;

}


/* =========================================================
   CTRL + ENTER
   ========================================================= */

question.addEventListener(
    "keydown",
    function (event) {

        if (
            event.ctrlKey &&
            event.key === "Enter"
        ) {

            event.preventDefault();

            askQuestion();

        }

    }
);


/* =========================================================
   COPY ANSWER
   ========================================================= */

copyButton.addEventListener(
    "click",
    async function () {

        const text =
            answer.textContent.trim();


        if (!text) {
            return;
        }


        try {

            await navigator.clipboard.writeText(
                text
            );


            const originalText =
                copyButton.innerHTML;


            copyButton.innerHTML =
                "✓ Copied";


            setTimeout(
                function () {

                    copyButton.innerHTML =
                        originalText;

                },
                1500
            );


        } catch (error) {

            console.error(
                "Copy failed:",
                error
            );

        }

    }
);


/* =========================================================
   RESET ANSWER
   ========================================================= */

function resetAnswer() {

    emptyAnswer.classList.remove(
        "hidden"
    );

    answerLoading.classList.add(
        "hidden"
    );

    answerContent.classList.add(
        "hidden"
    );

    answer.textContent = "";

    source.textContent = "";

    answerStatus.textContent = "";

    copyButton.disabled = true;

}


/* =========================================================
   UPLOAD STATUS HELPERS
   ========================================================= */

function clearUploadStatus() {

    uploadStatus.textContent = "";

    uploadStatus.style.color = "";

}


function showUploadStatus(
    message,
    type
) {

    uploadStatus.textContent =
        message;


    if (type === "error") {

        uploadStatus.style.color =
            "#fca5a5";

    } else if (type === "success") {

        uploadStatus.style.color =
            "#86efac";

    } else {

        uploadStatus.style.color =
            "#93c5fd";

    }

}


function showUploadSuccess(
    message
) {

    showUploadStatus(
        "✓ " + message,
        "success"
    );

}


function showUploadError(
    message
) {

    showUploadStatus(
        "✕ " + message,
        "error"
    );

}


/* =========================================================
   ANSWER ERROR
   ========================================================= */

function showAnswerError(
    message
) {

    answerStatus.textContent =
        "✕ " + message;

    answerStatus.style.color =
        "#fca5a5";

}


/* =========================================================
   GLOBAL DRAG PREVENTION
   ========================================================= */

document.addEventListener(
    "dragover",
    function (event) {

        event.preventDefault();

    }
);


document.addEventListener(
    "drop",
    function (event) {

        event.preventDefault();

    }
);
