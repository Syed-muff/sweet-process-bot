runtime_data = {
    "gemini_files": [],
    "current_pdf_filename": None,
    "chat_history": [],
}

def reset_runtime_data():
    global runtime_data
    runtime_data = {
        "gemini_files": [],
        "current_pdf_filename": None,
        "chat_history": [],
    }
    print("[RUNTIME] Runtime data has been reset.")

def print_runtime_data():
    print("[RUNTIME] Current runtime data:")
    for key, value in runtime_data.items():
        print(f"    {key}: {value}")

print_runtime_data()
