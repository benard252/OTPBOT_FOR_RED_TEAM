"""
Configuration settings for OTP Voice App
"""

import os
import json
from typing import Dict, Any

class Config:
    """Base configuration class"""

    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

    # Telegram Bot settings
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '7905681450:AAGuWHoJgNgn-y22Sy_YzwtoyJ27nktlSRQ')
    TELEGRAM_PUBLIC_CHAT = os.environ.get('TELEGRAM_PUBLIC_CHAT', '-1002216623779')

    # Ngrok settings
    NGROK_URL = os.environ.get('NGROK_URL', 'https://56ac-158-51-123-196.ngrok-free.app')

    # Twilio settings (replacing Telnyx)
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')

    # ElevenLabs settings (replacing Azure TTS)
    ELEVENLABS_API_KEY = os.environ.get('ELEVENLABS_API_KEY')
    ELEVENLABS_DEFAULT_VOICE = os.environ.get('ELEVENLABS_DEFAULT_VOICE', 'Rachel')

    # Spoof settings (for educational simulation)
    DEFAULT_SPOOF_NUMBER = os.environ.get('DEFAULT_SPOOF_NUMBER', '12109647678')

    # Webhook settings
    WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', 'your-webhook-secret')

    @staticmethod
    def load_scripts_config(file_path: str = 'config/scripts.json') -> Dict[str, Any]:
        """Load scripts configuration from JSON file"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    @staticmethod
    def load_settings_config(file_path: str = 'config/settings.json') -> Dict[str, Any]:
        """Load additional settings from JSON file"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
