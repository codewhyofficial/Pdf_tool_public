from flask import Flask
import os
from dotenv import load_dotenv
from .routes import main  # Import the main blueprint

load_dotenv()  # Load environment variables from .env file

class Config:
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'app', 'uploads')  # Ensure this matches where your uploads folder is located
    API_KEY = os.getenv('API_KEY')  # Get API key from environment variable

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.register_blueprint(main)  # Register the blueprint here
    return app

