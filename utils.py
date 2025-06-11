from PyPDF2 import PdfReader
from rapidfuzz import fuzz
from config import ALLOWED_EXTENSIONS

def allowed_file(filename):
    extension_valid = '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    print(f"[UTILS] Checking if file '{filename}' is allowed: {extension_valid}")
    return extension_valid

def find_relevant_page(filepath, query):
    try:
        reader = PdfReader(filepath)
        highest_match = {"page": "Page not found", "score": 0}
        print(f"[UTILS] Starting PDF processing for file: {filepath}")
        for page_number, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text()
            if not page_text:
                print(f"[UTILS] Page {page_number} has no text. Skipping.")
                continue
            score = fuzz.partial_ratio(query.lower(), page_text.lower())
            print(f"[UTILS] Comparing query with page {page_number} (score: {score}).")
            if score > highest_match["score"]:
                highest_match = {"page": page_number, "score": score}
        if highest_match["score"] > 50:
            print(f"[UTILS] Relevant page found: {highest_match['page']} (score: {highest_match['score']}).")
            return highest_match["page"]
        else:
            print("[UTILS] No relevant page found with a sufficient match score.")
            return "Page not found"
    except Exception as e:
        print(f"[UTILS] Error processing PDF file '{filepath}': {e}")
        return "Page not found"

def log_event(event_message):
    from datetime import datetime
    current_time = datetime.now().isoformat()
    print(f"[LOG {current_time}] {event_message}")

def y_helper():
    log_event("y helper function called. No operation performed.")
