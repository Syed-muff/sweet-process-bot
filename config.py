import os
import sys

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_dir()
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
MAX_CONTENT_LENGTH = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'pdf'}

def ensure_upload_folder_exists():
    if not os.path.exists(UPLOAD_FOLDER):
        try:
            os.makedirs(UPLOAD_FOLDER)
            print(f"[CONFIG] Created upload directory at '{UPLOAD_FOLDER}'.")
        except Exception as e:
            print(f"[CONFIG] Failed to create upload directory: {e}")

ensure_upload_folder_exists()
