
const pdfFile = document.getElementById("pdfFile");
const chooseBtn = document.getElementById("chooseBtn");
const uploadBtn = document.getElementById("uploadBtn");
const uploadArea = document.getElementById("uploadArea");
const fileInfo = document.getElementById("fileInfo");
const progress = document.getElementById("progress");
const result = document.getElementById("result");

let selectedFile = null;

// Open file picker
chooseBtn.addEventListener("click", () => {
    pdfFile.click();
});

// Select a file
pdfFile.addEventListener("change", () => {
    handleFile(pdfFile.files[0]);
});

// Handle selected file
function handleFile(file) {

    if (!file) return;

    result.innerHTML = "";
    progress.textContent = "";

    if (
        file.type !== "application/pdf" ||
        !file.name.toLowerCase().endsWith(".pdf")
    ) {
        alert("Please select a valid PDF file.");
        return;
    }

    if (file.size > 20 * 1024 * 1024) {
        alert("Maximum file size is 20 MB.");
        return;
    }

    selectedFile = file;

    fileInfo.textContent =
        `Selected: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;

    uploadBtn.disabled = false;
}

// Drag and drop
uploadArea.addEventListener("dragover", (event) => {
    event.preventDefault();
    uploadArea.classList.add("dragover");
});

uploadArea.addEventListener("dragleave", () => {
    uploadArea.classList.remove("dragover");
});

uploadArea.addEventListener("drop", (event) => {
    event.preventDefault();
    uploadArea.classList.remove("dragover");

    const file = event.dataTransfer.files[0];

    handleFile(file);
});

// Upload PDF
uploadBtn.addEventListener("click", async () => {

    if (!selectedFile) return;

    const formData = new FormData();

    formData.append("file", selectedFile);

    uploadBtn.disabled = true;
    progress.textContent = "Uploading and extracting PDF text...";
    result.innerHTML = "";

    try {

        const response = await fetch("/api/upload", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Upload failed");
        }

        progress.textContent = "";

        result.innerHTML = `
            <p class="success">✓ ${data.message}</p>
            <p><strong>File:</strong> ${escapeHTML(data.filename)}</p>
            <p><strong>Total pages:</strong> ${data.total_pages}</p>
            <p><strong>Extracted characters:</strong> ${data.total_characters}</p>
            <p><strong>Possible scanned pages:</strong>
                ${data.scanned_pages.length
                    ? escapeHTML(data.scanned_pages.join(", "))
                    : "None detected"}
            </p>
            <h3>Extracted Text Preview</h3>
            <pre>${escapeHTML(data.preview || "No selectable text found. OCR will be needed.")}</pre>
        `;

    } catch (error) {

        progress.textContent = "";

        result.innerHTML = `
            <p class="error">${escapeHTML(error.message)}</p>
        `;

    } finally {

        uploadBtn.disabled = !selectedFile;
    }
});

// Safely display server-provided text
function escapeHTML(value) {
    return String(value).replace(/[&<>"']/g, char => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[char]);
}
