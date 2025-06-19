"""
Environment utility functions for OTP Voice App
Handles .env file updates and configuration reloading
"""

import logging
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)

def update_env_file(file_path: str, updates: dict) -> dict:
    """
    Update .env file with new values

    Args:
        file_path: Path to .env file
        updates: Dict of key-value pairs to update

    Returns:
        Dict with success status and optional error message
    """
    try:
        # Read existing .env file
        env_lines = []

        try:
            with open(file_path, 'r') as f:
                env_lines = f.readlines()
        except FileNotFoundError:
            # File doesn't exist, create it
            logger.info(f"Creating new .env file at {file_path}")

        # Create a dict of existing variables
        existing_vars = {}
        for i, line in enumerate(env_lines):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                existing_vars[key] = {'value': value, 'line_index': i}

        # Update existing variables or add new ones
        for key, value in updates.items():
            if key in existing_vars:
                # Update existing line
                env_lines[existing_vars[key]['line_index']] = f"{key}={value}\n"
                logger.info(f"Updated existing variable: {key}")
            else:
                # Add new line
                env_lines.append(f"{key}={value}\n")
                logger.info(f"Added new variable: {key}")

        # Write back to file
        with open(file_path, 'w') as f:
            f.writelines(env_lines)

        logger.info(f"Successfully updated .env file with {len(updates)} variables")
        return {'success': True}

    except Exception as e:
        error_msg = f"Error updating .env file: {str(e)}"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg}

def reload_configuration():
    """
    Reload configuration after updating .env file
    """
    try:
        from dotenv import load_dotenv

        # Reload environment variables
        load_dotenv(override=True)

        # Reload configuration class
        from config.settings import Config

        # Update Config class attributes
        Config.TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
        Config.TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
        Config.TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
        Config.ELEVENLABS_API_KEY = os.environ.get('ELEVENLABS_API_KEY')
        Config.ELEVENLABS_DEFAULT_VOICE = os.environ.get('ELEVENLABS_DEFAULT_VOICE', 'Rachel')
        Config.TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
        Config.TELEGRAM_PUBLIC_CHAT = os.environ.get('TELEGRAM_PUBLIC_CHAT')
        Config.NGROK_URL = os.environ.get('NGROK_URL')
        Config.WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', 'webhook-secret-2025')
        Config.DEFAULT_SPOOF_NUMBER = os.environ.get('DEFAULT_SPOOF_NUMBER', '+12109647678')

        logger.info("Configuration reloaded successfully")

    except Exception as e:
        logger.error(f"Error reloading configuration: {e}")

def get_env_variable(key: str, default: str = None) -> str:
    """
    Get environment variable with fallback

    Args:
        key: Environment variable key
        default: Default value if not found

    Returns:
        Environment variable value or default
    """
    return os.environ.get(key, default)

def validate_configuration() -> Dict[str, Any]:
    """
    Validate current configuration and return status

    Returns:
        Dict with validation results for each service
    """
    try:
        from config.settings import Config

        validation_results = {
            'twilio': {
                'valid': bool(
                    Config.TWILIO_ACCOUNT_SID and
                    Config.TWILIO_AUTH_TOKEN and
                    Config.TWILIO_PHONE_NUMBER and
                    Config.TWILIO_ACCOUNT_SID != 'your-twilio-account-sid' and
                    Config.TWILIO_AUTH_TOKEN != 'your-twilio-auth-token'
                ),
                'missing_fields': []
            },
            'elevenlabs': {
                'valid': bool(
                    Config.ELEVENLABS_API_KEY and
                    Config.ELEVENLABS_API_KEY != 'your-elevenlabs-api-key'
                ),
                'missing_fields': []
            },
            'telegram': {
                'valid': bool(Config.TELEGRAM_BOT_TOKEN),
                'missing_fields': []
            },
            'ngrok': {
                'valid': bool(Config.NGROK_URL and 'ngrok' in Config.NGROK_URL),
                'missing_fields': []
            }
        }

        # Check for missing fields
        if not validation_results['twilio']['valid']:
            missing = []
            if not Config.TWILIO_ACCOUNT_SID or Config.TWILIO_ACCOUNT_SID == 'your-twilio-account-sid':
                missing.append('TWILIO_ACCOUNT_SID')
            if not Config.TWILIO_AUTH_TOKEN or Config.TWILIO_AUTH_TOKEN == 'your-twilio-auth-token':
                missing.append('TWILIO_AUTH_TOKEN')
            if not Config.TWILIO_PHONE_NUMBER:
                missing.append('TWILIO_PHONE_NUMBER')
            validation_results['twilio']['missing_fields'] = missing

        if not validation_results['elevenlabs']['valid']:
            validation_results['elevenlabs']['missing_fields'] = ['ELEVENLABS_API_KEY']

        if not validation_results['telegram']['valid']:
            validation_results['telegram']['missing_fields'] = ['TELEGRAM_BOT_TOKEN']

        if not validation_results['ngrok']['valid']:
            validation_results['ngrok']['missing_fields'] = ['NGROK_URL']

        return validation_results

    except Exception as e:
        logger.error(f"Error validating configuration: {e}")
        return {}

def backup_env_file(file_path: str) -> bool:
    """
    Create a backup of the .env file

    Args:
        file_path: Path to .env file

    Returns:
        True if backup was created successfully
    """
    try:
        import shutil
        from datetime import datetime

        if not os.path.exists(file_path):
            return False

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{file_path}.backup_{timestamp}"

        shutil.copy2(file_path, backup_path)
        logger.info(f"Created backup: {backup_path}")

        return True

    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return False

def restore_env_backup(backup_path: str, target_path: str = '.env') -> bool:
    """
    Restore .env file from backup

    Args:
        backup_path: Path to backup file
        target_path: Target .env file path

    Returns:
        True if restore was successful
    """
    try:
        import shutil

        if not os.path.exists(backup_path):
            logger.error(f"Backup file not found: {backup_path}")
            return False

        shutil.copy2(backup_path, target_path)
        logger.info(f"Restored from backup: {backup_path}")

        # Reload configuration after restore
        reload_configuration()

        return True

    except Exception as e:
        logger.error(f"Error restoring backup: {e}")
        return False
