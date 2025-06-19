"""
OTP Voice App - Main Flask Application
Educational OTP simulation system with voice capabilities
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import logging
import os
from dotenv import load_dotenv

# Import custom modules
from config.settings import Config
from routes.api_routes import api_bp
from routes.telegram_routes import telegram_bp
from routes.voice_routes import voice_bp
from services.telegram_service import TelegramService
from utils.logger import setup_logging

# Load environment variables
load_dotenv()

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # Setup CORS
    CORS(app)

    # Setup logging
    setup_logging()

    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(telegram_bp, url_prefix='/telegram')
    app.register_blueprint(voice_bp, url_prefix='/voice')

    # Main route
    @app.route('/')
    def index():
        return render_template('index.html')

    # Health check
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy', 'service': 'OTP Voice App'})

    return app

if __name__ == '__main__':
    app = create_app()

    # Initialize Telegram service
    telegram_service = TelegramService()

    # Run the app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
