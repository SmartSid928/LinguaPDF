from flask import Flask, send_from_directory, jsonify, request
from pathlib import Path
from werkzeug.utils import secure_filename
import uuid

from backend.pdf_processor import extract_pdf_text
from backend.translator import translate_text, get_languages
from backend.pdf_generator import generate_pdf


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

app = Flask(
    __name__,
    static_folder=str(FRONTEND_DIR),
    static_url_path="/static"
)

app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024


@app.route("/")
def home():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/api/status")
def status():
    return jsonify({
        "status": "online",
        "project": "LinguaPDF"
    })


@app.route("/api/languages")
def languages():
    try:
        return jsonify({
            "success": True,
            "languages": get_languages()
        })
    except Exception:
        app.logger.exception("Could not load languages")
        return jsonify({
            "error": "Unable to load languages. Check your internet connection."
        }), 500


@app.route("/api/upload", methods=["POST"])
def upload_pdf():

    if "file" not in request.files:
        return jsonify({"error": "No PDF file selected"}), 400

    file = request.files["file"]

    if not file.filename:
        return jsonify({"error": "Please select a file"}), 400

    filename = secure_filename(file.filename)

    if not filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    header = file.stream.read(5)
    file.stream.seek(0)

    if header != b"%PDF-":
        return jsonify({"error": "Invalid PDF file"}), 400

    file_id = uuid.uuid4().hex
    file_path = UPLOAD_DIR / f"{file_id}.pdf"

    try:
        file.save(file_path)

        extracted = extract_pdf_text(file_path)

        if not extracted["full_text"].strip():
            file_path.unlink(missing_ok=True)
            return jsonify({
                "error": "No selectable text found. This PDF may need OCR."
            }), 400

        return jsonify({
            "success": True,
            "message": "PDF uploaded and text extracted successfully!",
            "file_id": file_id,
            "filename": filename,
            "total_pages": extracted["total_pages"],
            "total_characters": extracted["total_characters"],
            "scanned_pages": extracted["scanned_pages"],
            "preview": extracted["full_text"][:1500]
        })

    except Exception:
        file_path.unlink(missing_ok=True)
        app.logger.exception("PDF upload failed")

        return jsonify({
            "error": "Unable to process this PDF."
        }), 500


@app.route("/api/translate", methods=["POST"])
def translate_pdf():

    data = request.get_json(silent=True) or {}

    file_id = data.get("file_id", "")
    source_code = data.get("source_language", "auto")
    target_code = data.get("target_language", "")

    if not file_id or not all(c in "0123456789abcdef" for c in file_id):
        return jsonify({"error": "Invalid or missing uploaded file ID."}), 400

    if len(file_id) != 32:
        return jsonify({"error": "Invalid uploaded file ID."}), 400

    if not target_code:
        return jsonify({"error": "Please select a target language."}), 400

    upload_path = UPLOAD_DIR / f"{file_id}.pdf"

    if not upload_path.exists():
        return jsonify({
            "error": "Uploaded PDF not found. Please upload it again."
        }), 404

    try:
        available = get_languages()
        valid_codes = {item["code"] for item in available}

        if source_code != "auto" and source_code not in valid_codes:
            return jsonify({"error": "Invalid source language."}), 400

        if target_code not in valid_codes:
            return jsonify({"error": "Invalid target language."}), 400

        extracted = extract_pdf_text(upload_path)

        translated_pages = []

        for page in extracted["pages"]:
            page_text = page["text"]

            if page_text.strip():
                translated = translate_text(
                    page_text,
                    source_code,
                    target_code
                )
            else:
                translated = ""

            translated_pages.append(translated)

        output_id = uuid.uuid4().hex
        output_filename = f"translated_{output_id}.pdf"
        output_path = OUTPUT_DIR / output_filename

        generate_pdf(
            translated_pages,
            output_path,
            target_language=target_code
        )

        return jsonify({
            "success": True,
            "message": "Translation completed!",
            "download_url": f"/api/download/{output_filename}",
            "filename": output_filename,
            "total_pages": len(translated_pages)
        })

    except Exception as error:
        app.logger.exception("PDF translation failed")

        return jsonify({
        "error": f"Translation failed: {str(error)}"
    }), 500


@app.route("/api/download/<filename>")
def download_pdf(filename):

    if not filename.startswith("translated_") or not filename.endswith(".pdf"):
        return jsonify({"error": "Invalid download filename."}), 400

    return send_from_directory(
        OUTPUT_DIR,
        filename,
        as_attachment=True
    )


@app.errorhandler(413)
def file_too_large(error):
    return jsonify({
        "error": "File is too large. Maximum size is 20 MB."
    }), 413


if __name__ == "__main__":
    app.run(debug=True)