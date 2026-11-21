
const pdfFile = document.getElementById("pdfFile");
const chooseBtn = document.getElementById("chooseBtn");
const uploadArea = document.getElementById("uploadArea");
const fileInfo = document.getElementById("fileInfo");

const sourceLanguage = document.getElementById("sourceLanguage");
const targetLanguage = document.getElementById("targetLanguage");

const translateBtn = document.getElementById("translateBtn");
const progress = document.getElementById("progress");
const result = document.getElementById("result");

let selectedFile = null;
let uploadedFileId = null;


// Safely read JSON responses from Flask
async function readJSON(response, action) {
    const responseText = await response.text();

    try {
        return responseText ? JSON.parse(responseText) : {};
    } catch (error) {
        console.error(`${action}: Server returned non-JSON response.`);
        console.error("HTTP status:", response.status);
        console.error("Response:", responseText);

        throw new Error(
            `${action} failed (HTTP ${response.status}). ` +
            "The server returned an invalid response. Check the VS Code terminal."
        );
    }
}


// Load supported languages
async function loadLanguages() {
    try {
        progress.textContent = "Loading available languages...";

        const response = await fetch("/api/languages");
        const data = await readJSON(response, "Loading languages");

        if (!response.ok) {
            throw new Error(data.error || "Could not load languages.");
        }

        sourceLanguage.innerHTML =
            '<option value="auto">Detect language automatically</option>';

        targetLanguage.innerHTML = "";

        data.languages.forEach(language => {
            const sourceOption = document.createElement("option");
            sourceOption.value = language.code;
            sourceOption.textContent = language.name;

            const targetOption = document.createElement("option");
            targetOption.value = language.code;
            targetOption.textContent = language.name;

            sourceLanguage.appendChild(sourceOption);
            targetLanguage.appendChild(targetOption);
        });

        sourceLanguage.value = "en";

        if ([...targetLanguage.options].some(option => option.value === "ta")) {
            targetLanguage.value = "ta";
        } else {
            targetLanguage.value = "en";
        }

        progress.textContent = "";
        updateButton();

    } catch (error) {
        progress.textContent = "";
        result.innerHTML =
            `<p class="error">${escapeHTML(error.message)}</p>`;
    }
}


// Select PDF
chooseBtn.addEventListener("click", () => {
    pdfFile.click();
});

pdfFile.addEventListener("change", () => {
    handleFile(pdfFile.files[0]);
});


function handleFile(file) {
    if (!file) return;

    result.innerHTML = "";
    progress.textContent = "";
    uploadedFileId = null;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
        alert("Please select a PDF file.");
        return;
    }

    if (file.size > 20 * 1024 * 1024) {
        alert("Maximum file size is 20 MB.");
        return;
    }

    selectedFile = file;

    fileInfo.textContent =
        `Selected: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;

    updateButton();
}


// Drag and drop
uploadArea.addEventListener("dragover", event => {
    event.preventDefault();
    uploadArea.classList.add("dragover");
});

uploadArea.addEventListener("dragleave", () => {
    uploadArea.classList.remove("dragover");
});

uploadArea.addEventListener("drop", event => {
    event.preventDefault();
    uploadArea.classList.remove("dragover");

    handleFile(event.dataTransfer.files[0]);
});


// Enable/disable translation button
function updateButton() {
    const hasFile = Boolean(selectedFile);
    const hasTarget = Boolean(targetLanguage.value);

    translateBtn.disabled = !(hasFile && hasTarget);

    translateBtn.textContent = uploadedFileId
        ? "Translate PDF"
        : "Upload and Translate PDF";
}


// Upload the PDF
async function uploadPDF() {
    const formData = new FormData();
    formData.append("file", selectedFile);

    progress.textContent = "Uploading and extracting PDF text...";

    const response = await fetch("/api/upload", {
        method: "POST",
        body: formData
    });

    const data = await readJSON(response, "PDF upload");

    if (!response.ok) {
        throw new Error(data.error || "PDF upload failed.");
    }

    uploadedFileId = data.file_id;

    progress.textContent =
        `Extracted ${data.total_characters} characters from ${data.total_pages} pages.`;

    return data;
}


// Translate PDF
translateBtn.addEventListener("click", async () => {
    if (!selectedFile || !targetLanguage.value) return;

    translateBtn.disabled = true;
    result.innerHTML = "";

    try {
        if (!uploadedFileId) {
            await uploadPDF();
        }

        progress.textContent = "Translating your document. Please wait...";

        const response = await fetch("/api/translate", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                file_id: uploadedFileId,
                source_language: sourceLanguage.value,
                target_language: targetLanguage.value
            })
        });

        const data = await readJSON(response, "PDF translation");

        if (!response.ok) {
            throw new Error(data.error || "Translation failed.");
        }

        progress.textContent = "";

        const downloadLink = document.createElement("a");
        downloadLink.href = data.download_url;
        downloadLink.className = "download-link";
        downloadLink.textContent = "Download translated PDF";

        result.innerHTML = `
            <p class="success">✓ ${escapeHTML(data.message)}</p>
            <p>Your translated document contains ${data.total_pages} pages.</p>
        `;

        result.appendChild(downloadLink);

        uploadedFileId = null;

    } catch (error) {
        progress.textContent = "";

        result.innerHTML =
            `<p class="error">${escapeHTML(error.message)}</p>`;

        console.error("LinguaPDF error:", error);

    } finally {
        updateButton();
    }
});


sourceLanguage.addEventListener("change", updateButton);
targetLanguage.addEventListener("change", updateButton);


// Escape text before displaying it
function escapeHTML(value) {
    return String(value).replace(/[&<>"']/g, character => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[character]);
}


loadLanguages();
