"""
Telegram Routes for OTP Voice App
Webhook endpoints for Telegram bot integration
"""

import logging
import asyncio
from flask import Blueprint, request, jsonify
from telegram import Update
from telegram.ext import Application
from services.telegram_service import TelegramService
from services.otp_service import OTPService
from config.settings import Config

logger = logging.getLogger(__name__)
telegram_bp = Blueprint('telegram', __name__)

# Initialize services
telegram_service = TelegramService()
otp_service = OTPService()

@telegram_bp.route('/webhook', methods=['POST'])
def telegram_webhook():
    """
    Handle Telegram webhook updates
    """
    try:
        # Verify webhook secret (basic security)
        webhook_secret = request.headers.get('X-Telegram-Bot-Api-Secret-Token')
        if webhook_secret != Config.WEBHOOK_SECRET:
            logger.warning(f"Invalid webhook secret from {request.remote_addr}")
            return '', 403

        # Get update data
        update_data = request.get_json()

        if not update_data:
            return '', 400

        # Process the update
        if telegram_service.application:
            update = Update.de_json(update_data, telegram_service.bot)
            asyncio.run(telegram_service.application.process_update(update))

        return '', 200

    except Exception as e:
        logger.error(f"Error processing Telegram webhook: {e}")
        return '', 500

@telegram_bp.route('/set_webhook', methods=['POST'])
def set_webhook():
    """
    Set webhook URL for Telegram bot

    JSON Payload:
    {
        "webhook_url": "https://your-domain.com/telegram/webhook"
    }
    """
    try:
        data = request.get_json()

        if not data or 'webhook_url' not in data:
            return jsonify({
                'success': False,
                'error': 'webhook_url is required'
            }), 400

        webhook_url = data['webhook_url']

        # Set the webhook
        result = asyncio.run(telegram_service.set_webhook(webhook_url))

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@telegram_bp.route('/send_message', methods=['POST'])
def send_message():
    """
    Send message to Telegram chat

    JSON Payload:
    {
        "chat_id": "chat_id_or_username",
        "message": "Message text"
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400

        chat_id = data.get('chat_id')
        message = data.get('message')

        if not chat_id or not message:
            return jsonify({
                'success': False,
                'error': 'chat_id and message are required'
            }), 400

        # Send the message
        result = asyncio.run(telegram_service.send_message(chat_id, message))

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@telegram_bp.route('/send_otp_result', methods=['POST'])
def send_otp_result():
    """
    Send OTP result to public chat

    JSON Payload:
    {
        "phone_number": "+1234567890",
        "script_name": "microsoft",
        "user_id": "123456789",
        "otp_code": "123456",
        "success": true,
        "status": "completed"
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400

        # Send OTP result
        result = asyncio.run(telegram_service.send_otp_result(data))

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error sending OTP result: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@telegram_bp.route('/process_otp_command', methods=['POST'])
def process_otp_command():
    """
    Process OTP command from Telegram (manual trigger)

    JSON Payload:
    {
        "user_id": "123456789",
        "phone_number": "+1234567890",
        "script_name": "microsoft"
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400

        user_id = data.get('user_id')
        phone_number = data.get('phone_number')
        script_name = data.get('script_name', 'default')

        if not user_id or not phone_number:
            return jsonify({
                'success': False,
                'error': 'user_id and phone_number are required'
            }), 400

        # Validate phone number
        validation_result = asyncio.run(otp_service.validate_phone_number(phone_number))
        if not validation_result['valid']:
            return jsonify({
                'success': False,
                'error': 'Invalid phone number format'
            }), 400

        # Create voice OTP
        result = asyncio.run(otp_service.create_voice_otp(
            phone_number=validation_result['formatted'],
            script_name=script_name,
            user_id=user_id
        ))

        # Send confirmation message to user
        if telegram_service.bot:
            try:
                if result['success']:
                    confirmation_msg = f"✅ OTP call initiated successfully!\n\n📞 Phone: {phone_number}\n🔢 OTP: {result['otp_code']}\n📝 Script: {script_name}"
                else:
                    confirmation_msg = f"❌ OTP call failed!\n\n📞 Phone: {phone_number}\n❗ Error: {result.get('error', 'Unknown error')}"

                asyncio.run(telegram_service.send_message(str(user_id), confirmation_msg))
            except Exception as e:
                logger.error(f"Error sending confirmation to user: {e}")

        # Remove sensitive information from response
        response = result.copy()
        if 'audio_file' in response:
            del response['audio_file']

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error processing OTP command: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@telegram_bp.route('/bot_info', methods=['GET'])
def get_bot_info():
    """
    Get Telegram bot information
    """
    try:
        if not telegram_service.bot:
            return jsonify({
                'success': False,
                'error': 'Telegram bot not initialized'
            }), 500

        # Get bot info
        bot_info = asyncio.run(telegram_service.bot.get_me())

        return jsonify({
            'success': True,
            'bot_info': {
                'id': bot_info.id,
                'username': bot_info.username,
                'first_name': bot_info.first_name,
                'is_bot': bot_info.is_bot,
                'can_join_groups': bot_info.can_join_groups,
                'can_read_all_group_messages': bot_info.can_read_all_group_messages,
                'supports_inline_queries': bot_info.supports_inline_queries
            }
        })

    except Exception as e:
        logger.error(f"Error getting bot info: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@telegram_bp.route('/webhook_info', methods=['GET'])
def get_webhook_info():
    """
    Get current webhook information
    """
    try:
        if not telegram_service.bot:
            return jsonify({
                'success': False,
                'error': 'Telegram bot not initialized'
            }), 500

        # Get webhook info
        webhook_info = asyncio.run(telegram_service.bot.get_webhook_info())

        return jsonify({
            'success': True,
            'webhook_info': {
                'url': webhook_info.url,
                'has_custom_certificate': webhook_info.has_custom_certificate,
                'pending_update_count': webhook_info.pending_update_count,
                'last_error_date': webhook_info.last_error_date.isoformat() if webhook_info.last_error_date else None,
                'last_error_message': webhook_info.last_error_message,
                'max_connections': webhook_info.max_connections,
                'allowed_updates': webhook_info.allowed_updates
            }
        })

    except Exception as e:
        logger.error(f"Error getting webhook info: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@telegram_bp.route('/status', methods=['GET'])
def telegram_status():
    """
    Get Telegram service status
    """
    return jsonify({
        'success': True,
        'status': 'healthy' if telegram_service.bot else 'unhealthy',
        'bot_configured': telegram_service.bot is not None,
        'application_configured': telegram_service.application is not None,
        'public_chat_configured': bool(telegram_service.public_chat_id),
        'service': 'Telegram Integration'
    })

@telegram_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'error': 'Telegram endpoint not found'
    }), 404

@telegram_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500
