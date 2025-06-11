import os
import uuid
import time
from flask import Blueprint, request, jsonify, render_template, send_from_directory, url_for
from werkzeug.utils import secure_filename
import google.generativeai as genai
from config import BASE_DIR, UPLOAD_FOLDER
from gemini import upload_to_gemini, wait_for_files_active, generate_recommended_questions, generation_config
from utils import allowed_file, find_relevant_page, log_event, y_helper
from runtime_data import runtime_data

main_routes = Blueprint('main_routes', __name__)
model = genai.GenerativeModel(model_name="gemini-1.5-flash", generation_config=generation_config)

@main_routes.route("/", methods=["GET"])
def index():
    log_event("Rendering index page.")
    y_helper()
    return render_template("index.html")

@main_routes.route("/uploads/<path:filename>")
def serve_uploaded_file(filename):
    filename = secure_filename(filename)
    log_event(f"Serving uploaded file: {filename}")
    return send_from_directory(UPLOAD_FOLDER, filename)

@main_routes.route("/api/upload", methods=["POST"])
def upload_pdf():
    log_event("Received request to upload a PDF.")
    if 'pdf' not in request.files:
        log_event("No 'pdf' key found in request files.")
        return jsonify({"error": "No file part in the request."}), 400

    file = request.files['pdf']
    if file.filename == '':
        log_event("Empty filename received.")
        return jsonify({"error": "No file selected for uploading."}), 400

    if file and allowed_file(file.filename):
        original_filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        try:
            file.save(filepath)
            runtime_data["current_pdf_filename"] = unique_filename
            log_event(f"File '{unique_filename}' uploaded successfully to '{filepath}'.")
        except Exception as e:
            log_event(f"Error saving file: {e}")
            return jsonify({"error": "Failed to save uploaded file."}), 500

        gemini_file = upload_to_gemini(filepath, mime_type="application/pdf")
        if not gemini_file:
            log_event("Gemini file upload failed.")
            return jsonify({"error": "Failed to upload document to Gemini."}), 500

        runtime_data["gemini_files"].append(gemini_file)
        log_event(f"Gemini file added: {gemini_file.name}")

        try:
            wait_for_files_active(runtime_data["gemini_files"])
        except TimeoutError as te:
            log_event(str(te))
            return jsonify({"error": "File processing timed out."}), 500

        return jsonify({
            "message": "File successfully uploaded.",
            "filename": unique_filename
        }), 200
    else:
        log_event("Uploaded file type is not allowed.")
        return jsonify({"error": "Allowed file types are pdf."}), 400

@main_routes.route("/api", methods=["POST"])
def handle_request():
    log_event("Received chat query request.")
    if request.json and "user_input" in request.json:
        user_input = request.json["user_input"]
        log_event(f"User query: '{user_input}'")
        pre_prompt = (
            "You are a query assistant. Your task is to answer the given queries strictly based on the provided document. "
            "Respond in plain text, without any formatting. Keep your answers concise and accurate."
        )
        if not runtime_data.get("chat_history"):
            runtime_data["chat_history"] = [{"role": "user", "parts": [pre_prompt]}]
            log_event("Chat history initialized with pre-prompt.")

        filename = runtime_data.get("current_pdf_filename")
        gemini_files = runtime_data.get("gemini_files", [])
        if filename:
            uploaded_pdf_path = os.path.join(UPLOAD_FOLDER, filename)
            if not os.path.exists(uploaded_pdf_path):
                log_event("Uploaded PDF file missing. Falling back to default PDF.")
                filename = None
        else:
            log_event("No uploaded PDF found. Using default PDF.")

        if filename:
            gemini_file = gemini_files[-1]
            pdf_path = uploaded_pdf_path
            gemini_uri = gemini_file.uri
        else:
            pdf_path = os.path.join(BASE_DIR, 'static', 'default.pdf')
            gemini_uri = None

        if not os.path.exists(pdf_path):
            log_event("PDF file not found (neither uploaded nor default).")
            return jsonify({"error": "No PDF uploaded and default PDF not found."}), 500

        relevant_page = find_relevant_page(pdf_path, user_input)
        log_event(f"Relevant page determined: {relevant_page}")

        if gemini_uri:
            full_query = [gemini_file, user_input]
        else:
            full_query = [user_input]

        try:
            chat_history = runtime_data.get("chat_history", [])
            chat_session = model.start_chat(history=chat_history)
            log_event("Chat session started with current history.")
            response = chat_session.send_message({"role": "user", "parts": full_query})
            response.resolve()
            recommended_questions = generate_recommended_questions(user_input, model, gemini_file.uri if gemini_uri else None)
            log_event(f"Recommended questions generated: {recommended_questions}")
            chat_history.append({"role": "user", "parts": full_query})
            chat_history.append({"role": "model", "parts": response.text})
            runtime_data["chat_history"] = chat_history
            log_event("Chat history updated with the latest query and response.")
            if filename:
                pdf_path_without_fragment = f"/uploads/{filename}"
            else:
                pdf_path_without_fragment = url_for('static', filename='default.pdf')
            log_event(f"PDF URL constructed: {pdf_path_without_fragment}")
            return jsonify({
                "answer": response.text,
                "pdf_path": pdf_path_without_fragment,
                "page": relevant_page,
                "recommended_questions": recommended_questions
            })
        except Exception as e:
            log_event(f"Error during chat processing: {e}")
            return jsonify({"error": str(e)}), 500

    log_event("Invalid request received at chat endpoint.")
    return jsonify({"error": "Invalid request."}), 400

@main_routes.route("/api/list_uploads", methods=["GET"])
def list_uploads():
    try:
        files = os.listdir(UPLOAD_FOLDER)
        log_event("Listing all uploaded files.")
        pdf_files = [f for f in files if f.lower().endswith('.pdf')]
        return jsonify({"files": pdf_files})
    except Exception as e:
        log_event(f"Error listing uploads: {e}")
        return jsonify({"error": "Unable to list uploads."}), 500

@main_routes.route("/api/clear_history", methods=["POST"])
def clear_history():
    runtime_data["chat_history"] = []
    log_event("Chat history cleared upon request.")
    return jsonify({"message": "Chat history cleared."})

@main_routes.route("/api/delete_file", methods=["POST"])
def delete_file():
    if request.json and "filename" in request.json:
        filename = request.json["filename"]
        filepath = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                log_event(f"Deleted file: {filename}")
                if runtime_data.get("current_pdf_filename") == filename:
                    runtime_data["current_pdf_filename"] = None
                return jsonify({"message": f"Deleted file: {filename}"})
            except Exception as e:
                log_event(f"Error deleting file: {e}")
                return jsonify({"error": "Error deleting file."}), 500
        else:
            log_event("File not found for deletion.")
            return jsonify({"error": "File not found."}), 404
    else:
        log_event("Filename not provided for deletion.")
        return jsonify({"error": "Filename not provided."}), 400

@main_routes.route("/api/debug", methods=["GET"])
def debug_info():
    log_event("Debug info endpoint called.")
    return jsonify(runtime_data)
