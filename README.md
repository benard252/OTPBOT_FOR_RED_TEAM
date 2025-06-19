# 🎙️ OTP Voice App - Educational Platform

A comprehensive web application for educational demonstration of voice-based OTP (One-Time Password) systems. This project showcases the integration of modern telephony, text-to-speech, and messaging services.

## 🚨 Important Notice

**⚠️ EDUCATIONAL USE ONLY** - This application is designed for learning and testing purposes. Do not use for actual authentication systems or any malicious activities.

## 🌟 Features

- **Voice OTP Generation**: Generate and deliver OTP codes via voice calls
- **SMS Backup**: Fallback SMS delivery for OTP codes
- **Telegram Integration**: Bot interface for OTP operations
- **Web Interface**: Clean, modern web UI for testing and management
- **Multiple Voice Options**: Various voices and languages via ElevenLabs
- **Script Templates**: Customizable message templates for different scenarios
- **Real-time Status**: Monitor service health and call status
- **Webhook Support**: Handle Twilio and Telegram webhooks

## 🏗️ Architecture

### Services Replaced/Upgraded:
- **Telnyx → Twilio**: More reliable voice calling and SMS
- **Azure TTS → ElevenLabs**: Superior natural-sounding voices
- **Maintained**: Telegram bot integration for user interaction

### Project Structure:
```
otp-voice-app/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── config/
│   ├── settings.py       # Configuration management
│   ├── scripts.json      # Voice script configurations
│   └── settings.json     # Service settings
├── services/
│   ├── twilio_service.py      # Twilio voice/SMS integration
│   ├── elevenlabs_service.py  # ElevenLabs TTS integration
│   ├── telegram_service.py    # Telegram bot service
│   └── otp_service.py         # Core OTP business logic
├── routes/
│   ├── api_routes.py     # REST API endpoints
│   ├── telegram_routes.py     # Telegram webhook handlers
│   └── voice_routes.py   # Voice/TwiML endpoints
├── utils/
│   └── logger.py         # Logging utilities
└── templates/
    └── index.html        # Web interface
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or create the project directory
cd otp-voice-app

# Install Python dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

### 2. Configuration

Edit `.env` file with your service credentials:

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Twilio
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=+1234567890

# ElevenLabs
ELEVENLABS_API_KEY=your_elevenlabs_key

# Ngrok (for webhooks)
NGROK_URL=https://your-ngrok-url.ngrok-free.app
```

### 3. Service Setup

#### Twilio Setup:
1. Create account at [twilio.com](https://twilio.com)
2. Get Account SID and Auth Token
3. Purchase a phone number
4. Configure webhook URLs for voice status

#### ElevenLabs Setup:
1. Create account at [elevenlabs.io](https://elevenlabs.io)
2. Get API key from settings
3. Choose default voice (Rachel, Sarah, etc.)

#### Telegram Bot Setup:
1. Create bot with [@BotFather](https://t.me/botfather)
2. Get bot token
3. Set webhook URL: `/telegram/webhook`

### 4. Running the Application

```bash
# Start the Flask app
python app.py

# Or with gunicorn for production
gunicorn app:app --bind 0.0.0.0:5000
```

### 5. Ngrok Setup (for webhooks)

```bash
# Install ngrok
# Start tunnel
ngrok http 5000

# Update NGROK_URL in .env with the provided URL
```

## 📱 Usage

### Web Interface
Visit `http://localhost:5000` to access the web interface where you can:
- Generate voice OTP calls
- Send SMS backup codes
- Test phone number validation
- Monitor service status
- View Telegram bot information

### Telegram Bot Commands
```
/start - Welcome message
/help - Show available commands
/otp +1234567890 microsoft - Generate OTP call
/status - Check service status
```

### API Endpoints

#### Voice OTP
```bash
POST /api/otp/voice
{
  "phone_number": "+1234567890",
  "script_name": "microsoft",
  "user_id": "optional_user_id"
}
```

#### SMS OTP
```bash
POST /api/otp/sms
{
  "phone_number": "+1234567890",
  "script_name": "default"
}
```

#### Phone Validation
```bash
POST /api/validate/phone
{
  "phone_number": "+1234567890"
}
```

## 🎨 Available Scripts

The application supports multiple voice script templates:

- **default**: Standard verification message
- **microsoft**: Microsoft-style security message
- **otp france**: French language template
- **bank**: Banking security message
- **google**: Google-style verification

## 🎭 Available Voices

ElevenLabs voices supported:
- **Rachel**: Professional English (default)
- **Sarah**: French accent
- **Emily**: Warm English
- **Adam**: Male English
- **Paul**: Authoritative male
- **Drew**: Casual male
- **Antoni**: British accent

## 🔧 Configuration Files

### `config/scripts.json`
Defines voice script configurations with user mappings:
```json
[
  {
    "userid": "5291591455",
    "ScriptID": "64f7338f8d92e126ae676f9b",
    "ScriptNAME": "otp france",
    "Voice": "fr-FR-BrigitteNeural"
  }
]
```

### `config/settings.json`
Service configuration and API settings:
```json
{
  "bottoken": "telegram_bot_token",
  "ngrok": "webhook_url",
  "twilio": {
    "account_sid": "twilio_sid",
    "auth_token": "twilio_token"
  }
}
```

## 🔍 Monitoring & Logging

### Security Logging
The application includes comprehensive security logging:
- OTP request tracking
- Call success/failure monitoring
- Rate limiting detection
- Suspicious activity alerts

### Health Checks
Monitor service status via:
- `/health` - General application health
- `/api/health` - API service status
- `/telegram/status` - Telegram bot status
- `/voice/status` - Voice services status

## 🛡️ Security Features

- Phone number validation
- Webhook secret verification
- Request rate limiting
- Security event logging
- Educational use warnings

## 🚨 Troubleshooting

### Common Issues:

1. **Twilio Not Working**
   - Verify Account SID and Auth Token
   - Check phone number format (+1234567890)
   - Ensure webhook URLs are accessible

2. **ElevenLabs TTS Failing**
   - Verify API key in environment
   - Check account credits/usage limits
   - Try different voice options

3. **Telegram Bot Not Responding**
   - Verify bot token
   - Check webhook configuration
   - Ensure ngrok tunnel is active

4. **Audio Files Not Playing**
   - Check ngrok URL accessibility
   - Verify audio file permissions
   - Check Twilio TwiML endpoints

## 📚 Educational Resources

This project demonstrates:
- **Flask Web Framework**: Modern Python web development
- **API Integration**: Multiple third-party service integration
- **Webhook Handling**: Real-time event processing
- **Asynchronous Operations**: Handling voice/SMS delivery
- **Security Logging**: Monitoring and audit trails
- **Modular Architecture**: Clean, maintainable code structure

## 🤝 Contributing

This is an educational project. Contributions should focus on:
- Improving code documentation
- Adding new voice script templates
- Enhancing security features
- Better error handling
- Additional service integrations

## ⚠️ Legal Notice

This application is provided for educational purposes only. Users are responsible for:
- Complying with local laws and regulations
- Obtaining proper consent for voice calls/SMS
- Using legitimate phone numbers only
- Respecting privacy and data protection laws

**Do not use this application for:**
- Unauthorized access attempts
- Phishing or social engineering
- Harassment or unwanted communications
- Any illegal activities

## 📄 License

Educational use only. Not for commercial deployment.

## 🆘 Support

For educational support and questions:
1. Check the troubleshooting section
2. Review service documentation (Twilio, ElevenLabs)
3. Test with provided endpoints and examples

---

**Remember: This is an educational tool. Always use responsibly and ethically! 🎓**
