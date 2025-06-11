from flask import Flask
from flask_cors import CORS
from config import UPLOAD_FOLDER, MAX_CONTENT_LENGTH
from routes import main_routes
import logging
import os

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

app.register_blueprint(main_routes)

def additional_startup_checks():
    logging.debug("Performing additional startup checks...")
    static_dir = os.path.join(app.root_path, 'static')
    if not os.path.exists(static_dir):
        logging.debug(f"Static directory '{static_dir}' does not exist. Creating it.")
        os.makedirs(static_dir)
    else:
        logging.debug(f"Static directory '{static_dir}' already exists.")
    logging.debug("Additional startup checks complete.")

additional_startup_checks()

if __name__ == "__main__":
    logging.debug("Starting the Flask application in debug mode.")
    app.run(debug=True)
