"""
ElevenLabs Text-to-Speech Service - Replacing Azure TTS
Handles natural-sounding voice synthesis for OTP messages
"""

import logging
import requests
import os
import tempfile
from typing import Optional, Dict, Any, List
from elevenlabs import generate, Voice, VoiceSettings, set_api_key
from config.settings import Config

logger = logging.getLogger(__name__)

class ElevenLabsService:
    """Service for handling ElevenLabs text-to-speech"""

    def __init__(self):
        """Initialize ElevenLabs service"""
        self.api_key = Config.ELEVENLABS_API_KEY
        self.default_voice = Config.ELEVENLABS_DEFAULT_VOICE

        if not self.api_key:
            logger.warning("ElevenLabs API key not configured")
        else:
            try:
                set_api_key(self.api_key)
                logger.info("ElevenLabs service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize ElevenLabs service: {e}")

    def text_to_speech(self, text: str, voice_name: Optional[str] = None,
                      stability: float = 0.75, similarity_boost: float = 0.75) -> Dict[str, Any]:
        """
        Convert text to speech using ElevenLabs

        Args:
            text: Text to convert to speech
            voice_name: Voice to use (default: configured default voice)
            stability: Voice stability (0.0 to 1.0)
            similarity_boost: Voice similarity boost (0.0 to 1.0)

        Returns:
            Dict containing audio data and metadata
        """
        if not self.api_key:
            return {
                'success': False,
                'error': 'ElevenLabs API key not configured',
                'audio_data': None,
                'file_path': None
            }

        try:
            voice = voice_name or self.default_voice

            # Generate audio
            audio = generate(
                text=text,
                voice=Voice(
                    voice_id=self._get_voice_id(voice),
                    settings=VoiceSettings(
                        stability=stability,
                        similarity_boost=similarity_boost
                    )
                )
            )

            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            temp_file.write(audio)
            temp_file.close()

            logger.info(f"TTS generated successfully for voice: {voice}")

            return {
                'success': True,
                'audio_data': audio,
                'file_path': temp_file.name,
                'voice': voice,
                'text_length': len(text)
            }

        except Exception as e:
            logger.error(f"Error generating TTS: {e}")
            return {
                'success': False,
                'error': str(e),
                'audio_data': None,
                'file_path': None
            }

    def _get_voice_id(self, voice_name: str) -> str:
        """
        Get voice ID for a given voice name

        Args:
            voice_name: Name of the voice

        Returns:
            Voice ID string
        """
        # Common ElevenLabs voice mappings
        voice_mapping = {
            'Rachel': 'pNInz6obpgDQGcFmaJgB',
            'Drew': '29vD33N1CtxCmqQRPOHJ',
            'Clyde': '2EiwWnXFnvU5JabPnv8n',
            'Paul': '5Q0t7uMcjvnagumLfvZi',
            'Domi': 'AZnzlk1XvdvUeBnXmlld',
            'Dave': 'CYw3kZ02Hs0563khs1Fj',
            'Fin': 'D38z5RcWu1voky8WS1ja',
            'Sarah': 'EXAVITQu4vr4xnSDxMaL',
            'Antoni': 'ErXwobaYiN019PkySvjV',
            'Thomas': 'GBv7mTt0atIp3Br8iCZE',
            'Emily': 'LcfcDJNUP1GQjkzn1xUU',
            'Elli': 'MF3mGyEYCl7XYWbV9V6O',
            'Callum': 'N2lVS1w4EtoT3dr4eOWO',
            'Patrick': 'ODq5zmih8GrVes37Dizd',
            'Harry': 'SOYHLrjzK2X1ezoPC6cr',
            'Liam': 'TX3LPaxmHKxFdv7VOQHJ',
            'Dorothy': 'ThT5KcBeYPX3keUQqHPh',
            'Josh': 'TxGEqnHWrfWFTfGW9XjX',
            'Arnold': 'VR6AewLTigWG4xSOukaG',
            'Adam': 'pNInz6obpgDQGcFmaJgB',  # Default fallback
            'Sam': 'yoZ06aMxZJJ28mfd3POQ'
        }

        return voice_mapping.get(voice_name, voice_mapping['Rachel'])

    def generate_otp_message(self, otp_code: str, script_name: str = "default") -> str:
        """
        Generate OTP message text based on script

        Args:
            otp_code: The OTP code to include
            script_name: Script type to use

        Returns:
            Formatted message text
        """
        scripts = {
            'default': f"Your verification code is {' '.join(otp_code)}. Please enter this code to complete your authentication.",
            'microsoft': f"Hello, this is Microsoft Security. Your verification code is {' '.join(otp_code)}. Please enter this code in the verification field.",
            'otp france': f"Bonjour, votre code de vérification est {' '.join(otp_code)}. Veuillez saisir ce code pour continuer.",
            'bank': f"This is your bank calling. For security purposes, please confirm your identity with this verification code: {' '.join(otp_code)}.",
            'google': f"Hi, this is Google Security. Your verification code is {' '.join(otp_code)}. Do not share this code with anyone."
        }

        return scripts.get(script_name.lower(), scripts['default'])

    def get_available_voices(self) -> List[str]:
        """
        Get list of available voices

        Returns:
            List of available voice names
        """
        return [
            'Rachel', 'Drew', 'Clyde', 'Paul', 'Domi', 'Dave', 'Fin',
            'Sarah', 'Antoni', 'Thomas', 'Emily', 'Elli', 'Callum',
            'Patrick', 'Harry', 'Liam', 'Dorothy', 'Josh', 'Arnold', 'Adam', 'Sam'
        ]

    def cleanup_temp_file(self, file_path: str) -> bool:
        """
        Clean up temporary audio file

        Args:
            file_path: Path to the file to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                logger.info(f"Cleaned up temporary file: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error cleaning up file {file_path}: {e}")
            return False
