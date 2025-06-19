"""
OTP Service - Core Business Logic
Integrates Twilio, ElevenLabs, and Telegram services for OTP operations
"""

import logging
import random
import string
from datetime import datetime
from typing import Dict, Any, Optional
from config.settings import Config
from services.twilio_service import TwilioService
from services.elevenlabs_service import ElevenLabsService
from services.telegram_service import TelegramService

logger = logging.getLogger(__name__)

class OTPService:
    """Core service for OTP operations"""

    def __init__(self):
        """Initialize OTP service with all dependencies"""
        self.twilio_service = TwilioService()
        self.elevenlabs_service = ElevenLabsService()
        self.telegram_service = TelegramService()

        # Load script configurations
        self.scripts = Config.load_scripts_config()
        self.settings = Config.load_settings_config()

        logger.info("OTP service initialized")

    def generate_otp_code(self, length: int = 6) -> str:
        """
        Generate a random OTP code

        Args:
            length: Length of the OTP code

        Returns:
            Generated OTP code as string
        """
        return ''.join(random.choices(string.digits, k=length))

    async def create_voice_otp(self, phone_number: str, script_name: str = "default",
                              user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create and send voice OTP

        Args:
            phone_number: Target phone number
            script_name: Script type to use
            user_id: Telegram user ID (optional)

        Returns:
            Dict containing operation result
        """
        try:
            # Generate OTP code
            otp_code = self.generate_otp_code()

            # Get voice settings from script config
            voice_config = self._get_voice_config(script_name)

            # Generate speech text
            speech_text = self.elevenlabs_service.generate_otp_message(otp_code, script_name)

            # Convert text to speech
            tts_result = self.elevenlabs_service.text_to_speech(
                text=speech_text,
                voice_name=voice_config.get('voice', 'Rachel')
            )

            if not tts_result['success']:
                return {
                    'success': False,
                    'error': f"TTS generation failed: {tts_result['error']}",
                    'otp_code': otp_code
                }

            # Upload audio file (in a real implementation, you'd upload to a CDN)
            audio_url = self._upload_audio_file(tts_result['file_path'])

            # Generate TwiML for the call
            twiml = self.twilio_service.generate_twiml_url(audio_url)

            # Create a temporary endpoint for TwiML (in real implementation)
            twiml_url = f"{Config.NGROK_URL}/voice/twiml/{otp_code}"

            # Make the voice call
            call_result = self.twilio_service.make_voice_call(
                to_number=phone_number,
                twiml_url=twiml_url,
                from_number=Config.DEFAULT_SPOOF_NUMBER
            )

            # Prepare result
            result = {
                'success': call_result['success'],
                'otp_code': otp_code,
                'phone_number': phone_number,
                'script_name': script_name,
                'user_id': user_id,
                'call_sid': call_result.get('call_sid'),
                'voice': voice_config.get('voice', 'Rachel'),
                'timestamp': datetime.now().isoformat(),
                'audio_file': tts_result['file_path'],
                'twiml_url': twiml_url
            }

            if not call_result['success']:
                result['error'] = call_result['error']

            # Send result to Telegram if configured
            if self.telegram_service and user_id:
                await self.telegram_service.send_otp_result(result)

            # Clean up temporary audio file
            self.elevenlabs_service.cleanup_temp_file(tts_result['file_path'])

            logger.info(f"OTP operation completed for {phone_number}: {result['success']}")

            return result

        except Exception as e:
            logger.error(f"Error in create_voice_otp: {e}")
            return {
                'success': False,
                'error': str(e),
                'phone_number': phone_number,
                'script_name': script_name,
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            }

    def _get_voice_config(self, script_name: str) -> Dict[str, Any]:
        """
        Get voice configuration for a script

        Args:
            script_name: Name of the script

        Returns:
            Voice configuration dict
        """
        # Search in loaded scripts
        for script in self.scripts:
            if script.get('ScriptNAME', '').lower() == script_name.lower():
                return {
                    'voice': self._convert_azure_voice_to_elevenlabs(script.get('Voice', 'Rachel')),
                    'script_id': script.get('ScriptID'),
                    'user_id': script.get('userid')
                }

        # Default configuration
        return {
            'voice': 'Rachel',
            'script_id': None,
            'user_id': None
        }

    def _convert_azure_voice_to_elevenlabs(self, azure_voice: str) -> str:
        """
        Convert Azure voice names to ElevenLabs voice names

        Args:
            azure_voice: Azure TTS voice name

        Returns:
            ElevenLabs voice name
        """
        voice_mapping = {
            'fr-FR-BrigitteNeural': 'Sarah',  # French voice
            'en-US-JennyMultilingualNeural': 'Rachel',  # English voice
            'en-US-AriaNeural': 'Emily',
            'en-US-DavisNeural': 'Adam',
            'en-US-GuyNeural': 'Paul',
            'en-US-JaneNeural': 'Dorothy',
            'en-US-JasonNeural': 'Josh',
            'en-US-NancyNeural': 'Elli',
            'en-US-TonyNeural': 'Antoni'
        }

        return voice_mapping.get(azure_voice, 'Rachel')

    def _upload_audio_file(self, file_path: str) -> str:
        """
        Upload audio file and return public URL
        In a real implementation, this would upload to a CDN

        Args:
            file_path: Local path to audio file

        Returns:
            Public URL to audio file
        """
        # For now, return a placeholder URL
        # In production, you'd upload to AWS S3, Google Cloud Storage, etc.
        filename = file_path.split('/')[-1]
        return f"{Config.NGROK_URL}/static/audio/{filename}"

    async def get_call_status(self, call_sid: str) -> Dict[str, Any]:
        """
        Get status of a voice call

        Args:
            call_sid: Twilio call SID

        Returns:
            Call status information
        """
        return self.twilio_service.get_call_status(call_sid)

    def get_available_scripts(self) -> list:
        """
        Get list of available scripts

        Returns:
            List of script configurations
        """
        return self.scripts

    def get_available_voices(self) -> list:
        """
        Get list of available voices

        Returns:
            List of available voice names
        """
        return self.elevenlabs_service.get_available_voices()

    async def validate_phone_number(self, phone_number: str) -> Dict[str, Any]:
        """
        Validate phone number format (basic validation)

        Args:
            phone_number: Phone number to validate

        Returns:
            Validation result
        """
        import re

        # Basic phone number validation
        phone_pattern = r'^\+?1?[2-9]\d{2}[2-9]\d{2}\d{4}$|^\+?[1-9]\d{1,14}$'

        is_valid = bool(re.match(phone_pattern, phone_number.replace(' ', '').replace('-', '')))

        return {
            'valid': is_valid,
            'phone_number': phone_number,
            'formatted': phone_number.replace(' ', '').replace('-', '')
        }

    async def send_sms_otp(self, phone_number: str, script_name: str = "default",
                          user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Send OTP via SMS as backup option

        Args:
            phone_number: Target phone number
            script_name: Script type to use
            user_id: Telegram user ID (optional)

        Returns:
            Dict containing operation result
        """
        try:
            # Generate OTP code
            otp_code = self.generate_otp_code()

            # Create SMS message
            message = f"Your verification code is: {otp_code}. This code will expire in 10 minutes. Do not share this code with anyone."

            # Send SMS
            sms_result = self.twilio_service.send_sms(
                to_number=phone_number,
                message=message,
                from_number=Config.DEFAULT_SPOOF_NUMBER
            )

            # Prepare result
            result = {
                'success': sms_result['success'],
                'otp_code': otp_code,
                'phone_number': phone_number,
                'script_name': script_name,
                'user_id': user_id,
                'message_sid': sms_result.get('message_sid'),
                'timestamp': datetime.now().isoformat(),
                'method': 'sms'
            }

            if not sms_result['success']:
                result['error'] = sms_result['error']

            # Send result to Telegram if configured
            if self.telegram_service and user_id:
                await self.telegram_service.send_otp_result(result)

            logger.info(f"SMS OTP operation completed for {phone_number}: {result['success']}")

            return result

        except Exception as e:
            logger.error(f"Error in send_sms_otp: {e}")
            return {
                'success': False,
                'error': str(e),
                'phone_number': phone_number,
                'script_name': script_name,
                'user_id': user_id,
                'timestamp': datetime.now().isoformat(),
                'method': 'sms'
            }
