"""
API Routes for OTP Voice App
RESTful endpoints for OTP operations
"""

import logging
import asyncio
from flask import Blueprint, request, jsonify
from datetime import datetime
from services.otp_service import OTPService
from utils.logger import security_logger
from utils.env_utils import update_env_file, reload_configuration

logger = logging.getLogger(__name__)
api_bp = Blueprint('api', __name__)

# Initialize OTP service
otp_service = OTPService()

@api_bp.route('/otp/voice', methods=['POST'])
def create_voice_otp():
    """
    Create and send voice OTP

    JSON Payload:
    {
        "phone_number": "+1234567890",
        "script_name": "microsoft",
        "user_id": "telegram_user_id"
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400

        phone_number = data.get('phone_number')
        script_name = data.get('script_name', 'default')
        user_id = data.get('user_id')

        if not phone_number:
            return jsonify({
                'success': False,
                'error': 'phone_number is required'
            }), 400

        # Validate phone number
        validation_result = asyncio.run(otp_service.validate_phone_number(phone_number))
        if not validation_result['valid']:
            return jsonify({
                'success': False,
                'error': 'Invalid phone number format'
            }), 400

        # Log security event
        security_logger.log_otp_request(
            user_id or 'anonymous',
            phone_number,
            script_name,
            request.remote_addr
        )

        # Create voice OTP
        result = asyncio.run(otp_service.create_voice_otp(
            phone_number=validation_result['formatted'],
            script_name=script_name,
            user_id=user_id
        ))

        # Log result
        if result['success']:
            security_logger.log_otp_success(
                user_id or 'anonymous',
                phone_number,
                result.get('call_sid')
            )
        else:
            security_logger.log_otp_failure(
                user_id or 'anonymous',
                phone_number,
                result.get('error', 'Unknown error')
            )

        # Remove sensitive information from response
        response = result.copy()
        if 'audio_file' in response:
            del response['audio_file']

        status_code = 200 if result['success'] else 500
        return jsonify(response), status_code

    except Exception as e:
        logger.error(f"Error in create_voice_otp: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'timestamp': datetime.now().isoformat()
        }), 500

@api_bp.route('/otp/sms', methods=['POST'])
def create_sms_otp():
    """
    Create and send SMS OTP as backup

    JSON Payload:
    {
        "phone_number": "+1234567890",
        "script_name": "default",
        "user_id": "telegram_user_id"
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400

        phone_number = data.get('phone_number')
        script_name = data.get('script_name', 'default')
        user_id = data.get('user_id')

        if not phone_number:
            return jsonify({
                'success': False,
                'error': 'phone_number is required'
            }), 400

        # Validate phone number
        validation_result = asyncio.run(otp_service.validate_phone_number(phone_number))
        if not validation_result['valid']:
            return jsonify({
                'success': False,
                'error': 'Invalid phone number format'
            }), 400

        # Log security event
        security_logger.log_otp_request(
            user_id or 'anonymous',
            phone_number,
            f"{script_name} (SMS)",
            request.remote_addr
        )

        # Create SMS OTP
        result = asyncio.run(otp_service.send_sms_otp(
            phone_number=validation_result['formatted'],
            script_name=script_name,
            user_id=user_id
        ))

        # Log result
        if result['success']:
            security_logger.log_otp_success(
                user_id or 'anonymous',
                phone_number,
                result.get('message_sid')
            )
        else:
            security_logger.log_otp_failure(
                user_id or 'anonymous',
                phone_number,
                result.get('error', 'Unknown error')
            )

        status_code = 200 if result['success'] else 500
        return jsonify(result), status_code

    except Exception as e:
        logger.error(f"Error in create_sms_otp: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'timestamp': datetime.now().isoformat()
        }), 500

@api_bp.route('/otp/status/<call_sid>', methods=['GET'])
def get_call_status(call_sid):
    """
    Get status of a voice call
    """
    try:
        result = asyncio.run(otp_service.get_call_status(call_sid))

        status_code = 200 if result['success'] else 404
        return jsonify(result), status_code

    except Exception as e:
        logger.error(f"Error getting call status: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@api_bp.route('/scripts', methods=['GET'])
def get_scripts():
    """
    Get available scripts
    """
    try:
        scripts = otp_service.get_available_scripts()
        return jsonify({
            'success': True,
            'scripts': scripts
        })

    except Exception as e:
        logger.error(f"Error getting scripts: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@api_bp.route('/voices', methods=['GET'])
def get_voices():
    """
    Get available voices
    """
    try:
        voices = otp_service.get_available_voices()
        return jsonify({
            'success': True,
            'voices': voices
        })

    except Exception as e:
        logger.error(f"Error getting voices: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@api_bp.route('/validate/phone', methods=['POST'])
def validate_phone_number():
    """
    Validate phone number format

    JSON Payload:
    {
        "phone_number": "+1234567890"
    }
    """
    try:
        data = request.get_json()

        if not data or 'phone_number' not in data:
            return jsonify({
                'success': False,
                'error': 'phone_number is required'
            }), 400

        result = asyncio.run(otp_service.validate_phone_number(data['phone_number']))

        return jsonify({
            'success': True,
            'validation': result
        })

    except Exception as e:
        logger.error(f"Error validating phone number: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@api_bp.route('/config', methods=['GET'])
def get_configuration():
    """
    Get current configuration status
    """
    try:
        from config.settings import Config

        config_status = {
            'success': True,
            'configuration': {
                'twilio': {
                    'account_sid': Config.TWILIO_ACCOUNT_SID[:8] + '...' if Config.TWILIO_ACCOUNT_SID and Config.TWILIO_ACCOUNT_SID != 'your-twilio-account-sid' else None,
                    'auth_token': '***' if Config.TWILIO_AUTH_TOKEN and Config.TWILIO_AUTH_TOKEN != 'your-twilio-auth-token' else None,
                    'phone_number': Config.TWILIO_PHONE_NUMBER if Config.TWILIO_PHONE_NUMBER != '+1234567890' else None,
                    'configured': bool(Config.TWILIO_ACCOUNT_SID and Config.TWILIO_AUTH_TOKEN and
                                     Config.TWILIO_ACCOUNT_SID != 'your-twilio-account-sid' and
                                     Config.TWILIO_AUTH_TOKEN != 'your-twilio-auth-token')
                },
                'elevenlabs': {
                    'api_key': '***' if Config.ELEVENLABS_API_KEY and Config.ELEVENLABS_API_KEY != 'your-elevenlabs-api-key' else None,
                    'default_voice': Config.ELEVENLABS_DEFAULT_VOICE,
                    'configured': bool(Config.ELEVENLABS_API_KEY and Config.ELEVENLABS_API_KEY != 'your-elevenlabs-api-key')
                },
                'telegram': {
                    'bot_token': '***' if Config.TELEGRAM_BOT_TOKEN else None,
                    'public_chat': Config.TELEGRAM_PUBLIC_CHAT,
                    'configured': bool(Config.TELEGRAM_BOT_TOKEN)
                },
                'ngrok': {
                    'url': Config.NGROK_URL,
                    'configured': bool(Config.NGROK_URL and 'ngrok' in Config.NGROK_URL)
                }
            }
        }

        return jsonify(config_status)

    except Exception as e:
        logger.error(f"Error getting configuration: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@api_bp.route('/config', methods=['POST'])
def update_configuration():
    """
    Update configuration settings

    JSON Payload:
    {
        "service": "twilio|elevenlabs|telegram|ngrok",
        "settings": {
            "account_sid": "...",
            "auth_token": "...",
            "phone_number": "..."
        }
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400

        service = data.get('service')
        settings = data.get('settings', {})

        if not service or not settings:
            return jsonify({
                'success': False,
                'error': 'service and settings are required'
            }), 400

        # Update environment file
        env_file_path = '.env'
        env_updates = {}

        if service == 'twilio':
            if 'account_sid' in settings:
                env_updates['TWILIO_ACCOUNT_SID'] = settings['account_sid']
            if 'auth_token' in settings:
                env_updates['TWILIO_AUTH_TOKEN'] = settings['auth_token']
            if 'phone_number' in settings:
                env_updates['TWILIO_PHONE_NUMBER'] = settings['phone_number']

        elif service == 'elevenlabs':
            if 'api_key' in settings:
                env_updates['ELEVENLABS_API_KEY'] = settings['api_key']
            if 'default_voice' in settings:
                env_updates['ELEVENLABS_DEFAULT_VOICE'] = settings['default_voice']

        elif service == 'telegram':
            if 'bot_token' in settings:
                env_updates['TELEGRAM_BOT_TOKEN'] = settings['bot_token']
            if 'public_chat' in settings:
                env_updates['TELEGRAM_PUBLIC_CHAT'] = settings['public_chat']

        elif service == 'ngrok':
            if 'url' in settings:
                env_updates['NGROK_URL'] = settings['url']
        else:
            return jsonify({
                'success': False,
                'error': f'Unknown service: {service}'
            }), 400

        # Update .env file
        result = update_env_file(env_file_path, env_updates)

        if result['success']:
            # Reload configuration
            reload_configuration()

            return jsonify({
                'success': True,
                'message': f'{service.title()} configuration updated successfully',
                'updated_keys': list(env_updates.keys())
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500

    except Exception as e:
        logger.error(f"Error updating configuration: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@api_bp.route('/config/test/<service>', methods=['POST'])
def test_configuration(service):
    """
    Test a specific service configuration
    """
    try:
        if service == 'twilio':
            from services.twilio_service import TwilioService
            twilio_service = TwilioService()

            if not twilio_service.client:
                return jsonify({
                    'success': False,
                    'error': 'Twilio client not initialized'
                })

            # Test by fetching account info
            try:
                account = twilio_service.client.api.account.fetch()
                return jsonify({
                    'success': True,
                    'message': 'Twilio configuration is valid',
                    'account_name': account.friendly_name,
                    'status': account.status
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Twilio test failed: {str(e)}'
                })

        elif service == 'elevenlabs':
            from services.elevenlabs_service import ElevenLabsService
            elevenlabs_service = ElevenLabsService()

            if not elevenlabs_service.api_key:
                return jsonify({
                    'success': False,
                    'error': 'ElevenLabs API key not configured'
                })

            # Test by getting available voices
            try:
                voices = elevenlabs_service.get_available_voices()
                return jsonify({
                    'success': True,
                    'message': 'ElevenLabs configuration is valid',
                    'available_voices': len(voices),
                    'default_voice': elevenlabs_service.default_voice
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'ElevenLabs test failed: {str(e)}'
                })

        elif service == 'telegram':
            from services.telegram_service import TelegramService
            telegram_service = TelegramService()

            if not telegram_service.bot:
                return jsonify({
                    'success': False,
                    'error': 'Telegram bot not initialized'
                })

            # Test by getting bot info
            try:
                import asyncio
                bot_info = asyncio.run(telegram_service.bot.get_me())
                return jsonify({
                    'success': True,
                    'message': 'Telegram bot configuration is valid',
                    'bot_username': bot_info.username,
                    'bot_name': bot_info.first_name
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Telegram test failed: {str(e)}'
                })

        elif service == 'ngrok':
            from config.settings import Config
            import requests

            if not Config.NGROK_URL or 'ngrok' not in Config.NGROK_URL:
                return jsonify({
                    'success': False,
                    'error': 'Ngrok URL not configured'
                })

            # Test by making a request to the health endpoint
            try:
                response = requests.get(f"{Config.NGROK_URL}/health", timeout=5)
                if response.status_code == 200:
                    return jsonify({
                        'success': True,
                        'message': 'Ngrok tunnel is accessible',
                        'url': Config.NGROK_URL
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Ngrok tunnel returned status {response.status_code}'
                    })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Ngrok test failed: {str(e)}'
                })
        else:
            return jsonify({
                'success': False,
                'error': f'Unknown service: {service}'
            }), 400

    except Exception as e:
        logger.error(f"Error testing {service} configuration: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500



@api_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    return jsonify({
        'success': True,
        'status': 'healthy',
        'service': 'OTP Voice API',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@api_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@api_bp.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return jsonify({
        'success': False,
        'error': 'Method not allowed'
    }), 405

@api_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500
