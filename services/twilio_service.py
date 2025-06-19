"""
Twilio Voice Service - Replacing Telnyx
Handles voice calls and telephony features for OTP delivery
"""

import logging
from typing import Optional, Dict, Any
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from config.settings import Config

logger = logging.getLogger(__name__)

class TwilioService:
    """Service for handling Twilio voice calls and SMS"""

    def __init__(self):
        """Initialize Twilio client"""
        self.account_sid = Config.TWILIO_ACCOUNT_SID
        self.auth_token = Config.TWILIO_AUTH_TOKEN
        self.phone_number = Config.TWILIO_PHONE_NUMBER

        if not all([self.account_sid, self.auth_token, self.phone_number]):
            logger.warning("Twilio credentials not fully configured")
            self.client = None
        else:
            try:
                self.client = Client(self.account_sid, self.auth_token)
                logger.info("Twilio client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
                self.client = None

    def make_voice_call(self, to_number: str, twiml_url: str, from_number: Optional[str] = None) -> Dict[str, Any]:
        """
        Make a voice call using Twilio

        Args:
            to_number: Phone number to call
            twiml_url: URL returning TwiML for the call
            from_number: Optional from number (uses default if not provided)

        Returns:
            Dict containing call status and details
        """
        if not self.client:
            return {
                'success': False,
                'error': 'Twilio client not initialized',
                'call_sid': None
            }

        try:
            from_num = from_number or self.phone_number

            call = self.client.calls.create(
                to=to_number,
                from_=from_num,
                url=twiml_url,
                method='POST'
            )

            logger.info(f"Voice call initiated: {call.sid} to {to_number}")

            return {
                'success': True,
                'call_sid': call.sid,
                'status': call.status,
                'to': to_number,
                'from': from_num
            }

        except TwilioException as e:
            logger.error(f"Twilio error making call: {e}")
            return {
                'success': False,
                'error': str(e),
                'call_sid': None
            }
        except Exception as e:
            logger.error(f"Unexpected error making call: {e}")
            return {
                'success': False,
                'error': str(e),
                'call_sid': None
            }

    def send_sms(self, to_number: str, message: str, from_number: Optional[str] = None) -> Dict[str, Any]:
        """
        Send SMS using Twilio

        Args:
            to_number: Phone number to send SMS to
            message: SMS message content
            from_number: Optional from number (uses default if not provided)

        Returns:
            Dict containing SMS status and details
        """
        if not self.client:
            return {
                'success': False,
                'error': 'Twilio client not initialized',
                'message_sid': None
            }

        try:
            from_num = from_number or self.phone_number

            message = self.client.messages.create(
                body=message,
                from_=from_num,
                to=to_number
            )

            logger.info(f"SMS sent: {message.sid} to {to_number}")

            return {
                'success': True,
                'message_sid': message.sid,
                'status': message.status,
                'to': to_number,
                'from': from_num
            }

        except TwilioException as e:
            logger.error(f"Twilio error sending SMS: {e}")
            return {
                'success': False,
                'error': str(e),
                'message_sid': None
            }
        except Exception as e:
            logger.error(f"Unexpected error sending SMS: {e}")
            return {
                'success': False,
                'error': str(e),
                'message_sid': None
            }

    def get_call_status(self, call_sid: str) -> Dict[str, Any]:
        """
        Get the status of a call

        Args:
            call_sid: Twilio call SID

        Returns:
            Dict containing call status information
        """
        if not self.client:
            return {
                'success': False,
                'error': 'Twilio client not initialized'
            }

        try:
            call = self.client.calls(call_sid).fetch()

            return {
                'success': True,
                'call_sid': call.sid,
                'status': call.status,
                'duration': call.duration,
                'start_time': str(call.start_time) if call.start_time else None,
                'end_time': str(call.end_time) if call.end_time else None
            }

        except TwilioException as e:
            logger.error(f"Error fetching call status: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def generate_twiml_url(self, audio_url: str) -> str:
        """
        Generate TwiML for playing audio

        Args:
            audio_url: URL of audio file to play

        Returns:
            TwiML string for Twilio
        """
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play>{audio_url}</Play>
    <Pause length="1"/>
    <Hangup/>
</Response>"""
        return twiml
