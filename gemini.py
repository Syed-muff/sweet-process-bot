import time
import google.generativeai as genai
import os

api_key = os.getenv("GOOGLE_API_KEY", "")
genai.configure(api_key)
generation_config = {
    "temperature": 0.0,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 4096,
    "response_mime_type": "text/plain",
}

def upload_to_gemini(path, mime_type=None):
    try:
        file = genai.upload_file(path, mime_type=mime_type)
        print(f"[GEMINI] Uploaded file '{file.display_name}' with URI: {file.uri}")
        return file
    except Exception as e:
        print(f"[GEMINI] Error uploading file: {e}")
        return None

def wait_for_files_active(files, timeout=60, interval=5):
    start_time = time.time()
    while True:
        all_active = True
        for file in files:
            try:
                status = genai.get_file(file.name).status
                print(f"[GEMINI] Checking status for '{file.name}': {status}")
            except Exception as e:
                print(f"[GEMINI] Error checking file status for '{file.name}': {e}")
                all_active = False
                break
            if status != "active":
                all_active = False
                break
        if all_active:
            print("[GEMINI] All files are active.")
            break
        if time.time() - start_time > timeout:
            raise TimeoutError("[GEMINI] Files did not become active within the timeout period.")
        print("[GEMINI] Waiting for files to become active...")
        time.sleep(interval)

def generate_recommended_questions(user_query, model, gemini_uri=None):
    try:
        if gemini_uri:
            prompt = (
                f"Based on the user's query: \"{user_query}\" and the document located at \"{gemini_uri}\",\n"
                "provide 3–5 relevant follow-up questions that the user might ask next.\n"
                "Respond with each question on a new line."
            )
        else:
            prompt = (
                f"Based on the user's query: \"{user_query}\" and the provided document,\n"
                "provide 3–5 relevant follow-up questions that the user might ask next.\n"
                "Respond with each question on a new line."
            )
        print(f"[GEMINI] Sending prompt for recommended questions:\n{prompt}")
        response = model.start_chat(history=[{"role": "user", "parts": [prompt]}]).send_message(prompt)
        response.resolve()
        recommended_questions = response.text.strip().split("\n")
        questions = [q.strip() for q in recommended_questions if q.strip()]
        print(f"[GEMINI] Recommended questions generated: {questions}")
        return questions
    except Exception as e:
        print(f"[GEMINI] Error generating recommended questions: {e}")
        return []

def log_gemini_configuration():
    print("[GEMINI] Generation configuration:")
    for key, value in generation_config.items():
        print(f"    {key}: {value}")

log_gemini_configuration()
