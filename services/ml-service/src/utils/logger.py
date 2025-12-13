import logging
import json
import os
from datetime import datetime
from typing import Optional

class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs logs in JSON format for production."""

    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'service': 'ml-service',
            'module': record.module,
        }

        # Add request ID if available
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id

        # Add exception info if available
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        # Add any extra fields
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)

        return json.dumps(log_entry)


class ProductionFormatter(logging.Formatter):
    """Formatter for production environments - outputs JSON."""

    def format(self, record):
        formatter = StructuredFormatter()
        return formatter.format(record)


class DevelopmentFormatter(logging.Formatter):
    """Formatter for development environments - outputs human-readable format."""

    def format(self, record):
        timestamp = datetime.utcnow().isoformat()
        level = record.levelname
        module = record.module
        message = record.getMessage()

        log_line = f"{timestamp} [{level}] [{module}]: {message}"

        if hasattr(record, 'request_id'):
            log_line += f" (request_id={record.request_id})"

        if record.exc_info:
            log_line += f"\n{self.formatException(record.exc_info)}"

        return log_line


def setup_logger(name: str = 'ml-service', level: Optional[str] = None) -> logging.Logger:
    """
    Set up and configure a structured logger.

    Args:
        name: Logger name (default: 'ml-service')
        level: Log level (default: from LOG_LEVEL env var or 'INFO')

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Set log level from parameter, environment variable, or default to INFO
    log_level = level or os.getenv('LOG_LEVEL', 'INFO').upper()
    logger.setLevel(getattr(logging, log_level))

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    # Create console handler
    handler = logging.StreamHandler()

    # Use JSON formatter for production, human-readable for development
    if os.getenv('NODE_ENV') == 'production' or os.getenv('ENVIRONMENT') == 'production':
        handler.setFormatter(ProductionFormatter())
    else:
        handler.setFormatter(DevelopmentFormatter())

    logger.addHandler(handler)

    return logger


class LoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter for adding request ID and other context to log records.
    """

    def process(self, msg, kwargs):
        # Add extra fields from context
        if 'extra' not in kwargs:
            kwargs['extra'] = {}

        kwargs['extra'].update(self.extra)

        # Store extra fields in record for formatter access
        if self.extra:
            kwargs['extra']['extra_fields'] = self.extra

        return msg, kwargs


def get_logger_with_context(request_id: Optional[str] = None, **context) -> logging.LoggerAdapter:
    """
    Get a logger with request ID and additional context.

    Args:
        request_id: Request ID for tracking
        **context: Additional context fields

    Returns:
        LoggerAdapter with context
    """
    logger = setup_logger()

    extra = {}
    if request_id:
        extra['request_id'] = request_id
    extra.update(context)

    return LoggerAdapter(logger, extra)


# Default logger instance
logger = setup_logger()


# Example usage:
if __name__ == '__main__':
    # Basic usage
    logger.debug('This is a debug message')
    logger.info('This is an info message')
    logger.warning('This is a warning message')
    logger.error('This is an error message')

    # With context
    context_logger = get_logger_with_context(request_id='123-456-789', user_id='user-001')
    context_logger.info('Processing request')

    # With exception
    try:
        raise ValueError('Something went wrong')
    except Exception as e:
        logger.error('An error occurred', exc_info=True)
