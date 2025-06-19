"""
Logging utility for OTP Voice App
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

def setup_logging(log_level=logging.INFO, log_file='logs/app.log', max_bytes=10485760, backup_count=5):
    """
    Setup logging configuration for the application

    Args:
        log_level: Logging level (default: INFO)
        log_file: Log file path (default: 'logs/app.log')
        max_bytes: Maximum file size before rotation (default: 10MB)
        backup_count: Number of backup files to keep (default: 5)
    """

    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers = []

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler with rotation
    try:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"Could not setup file logging: {e}")

    # Set specific loggers to appropriate levels
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.INFO)
    logging.getLogger('twilio').setLevel(logging.INFO)
    logging.getLogger('elevenlabs').setLevel(logging.INFO)

    logging.info("Logging setup complete")

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)

class ContextFilter(logging.Filter):
    """
    Custom filter to add context information to log records
    """

    def __init__(self, user_id=None, session_id=None):
        super().__init__()
        self.user_id = user_id
        self.session_id = session_id

    def filter(self, record):
        if self.user_id:
            record.user_id = self.user_id
        if self.session_id:
            record.session_id = self.session_id
        return True

class SecurityLogger:
    """
    Special logger for security-related events
    """

    def __init__(self):
        self.logger = logging.getLogger('security')

        # Create logs directory if it doesn't exist
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Create security log file handler
        try:
            security_handler = RotatingFileHandler(
                'logs/security.log',
                maxBytes=5242880,  # 5MB
                backupCount=10
            )
        except Exception as e:
            # Fallback to console logging if file logging fails
            security_handler = logging.StreamHandler()
            print(f"Warning: Could not create security log file: {e}")

        security_formatter = logging.Formatter(
            '%(asctime)s - SECURITY - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        security_handler.setFormatter(security_formatter)
        self.logger.addHandler(security_handler)
        self.logger.setLevel(logging.INFO)

    def log_otp_request(self, user_id: str, phone_number: str, script_name: str, ip_address: str = None):
        """Log OTP request for security monitoring"""
        self.logger.info(
            f"OTP_REQUEST - User: {user_id}, Phone: {phone_number[:3]}***{phone_number[-3:]}, "
            f"Script: {script_name}, IP: {ip_address or 'Unknown'}"
        )

    def log_otp_success(self, user_id: str, phone_number: str, call_sid: str = None):
        """Log successful OTP delivery"""
        self.logger.info(
            f"OTP_SUCCESS - User: {user_id}, Phone: {phone_number[:3]}***{phone_number[-3:]}, "
            f"CallSID: {call_sid or 'N/A'}"
        )

    def log_otp_failure(self, user_id: str, phone_number: str, error: str):
        """Log OTP delivery failure"""
        self.logger.warning(
            f"OTP_FAILURE - User: {user_id}, Phone: {phone_number[:3]}***{phone_number[-3:]}, "
            f"Error: {error}"
        )

    def log_suspicious_activity(self, user_id: str, activity: str, details: str = None):
        """Log suspicious activity"""
        self.logger.warning(
            f"SUSPICIOUS_ACTIVITY - User: {user_id}, Activity: {activity}, "
            f"Details: {details or 'None'}"
        )

    def log_rate_limit_exceeded(self, user_id: str, ip_address: str = None):
        """Log rate limit violations"""
        self.logger.warning(
            f"RATE_LIMIT_EXCEEDED - User: {user_id}, IP: {ip_address or 'Unknown'}"
        )

# Global security logger instance
security_logger = SecurityLogger()
