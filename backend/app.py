
from flask import Flask, send_from_directory, jsonify, request
from pathlib import Path
from werkzeug.utils import secure_filename
import uuid

from backend.pdf_processor import extract_pdf_text

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
UPLOAD_DIR = BASE_DIR / "uploads"

UPLOAD_DIR.mkdir(exist_ok=True)

app = Flask(
    __name__,
    static_folder=str(FRONTEND_DIR),
    static_url_path="/static"
)

# Maximum upload size: 20 MB
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


@app.route("/api/upload", methods=["POST"])
def upload_pdf():

    if "file" not in request.files:
        return jsonify({
            "error": "No PDF file selected"
        }), 400

    file = request.files["file"]

    if not file.filename:
        return jsonify({
            "error": "Please select a file"
        }), 400

    filename = secure_filename(file.filename)

    if not filename.lower().endswith(".pdf"):
        return jsonify({
            "error": "Only PDF files are allowed"
        }), 400

    # Check the actual PDF signature
    header = file.stream.read(5)
    file.stream.seek(0)

    if header != b"%PDF-":
        return jsonify({
            "error": "Invalid PDF file"
        }), 400

    # Generate a unique server-side filename
    unique_name = f"{uuid.uuid4().hex}.pdf"
    file_path = UPLOAD_DIR / unique_name

    try:
        file.save(file_path)

        result = extract_pdf_text(file_path)

        return jsonify({
            "success": True,
            "message": "PDF uploaded and processed successfully!",
            "filename": filename,
            "total_pages": result["total_pages"],
            "total_characters": result["total_characters"],
            "scanned_pages": result["scanned_pages"],
            "preview": result["full_text"][:2000]
        })

    except Exception as error:

        if file_path.exists():
            file_path.unlink()

        app.logger.exception("PDF processing failed")

        return jsonify({
            "error": "Unable to process this PDF. Please check the file."
        }), 500


@app.errorhandler(413)
def file_too_large(error):
    return jsonify({
        "error": "File is too large. Maximum size is 20 MB."
    }), 413


if __name__ == "__main__":
    app.run(debug=True)
