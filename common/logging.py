"""
Centralized logging configuration.

This module provides a consistent logging setup across all Lambda functions
in the Obsidian AI Assistant application, with support for structured logging.
"""

import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, Union

# Configure logging level based on environment
LOG_LEVEL: str = os.environ.get('LOG_LEVEL', 'INFO')

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: The name of the logger (defaults to 'obsidian-ai-assistant')
        
    Returns:
        A configured logger instance
    """
    logger = logging.getLogger(name or 'obsidian-ai-assistant')
    
    # Set log level
    level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers = []
    
    # Add handler if not already present
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

class JsonFormatter(logging.Formatter):
    """
    Format logs as JSON for better parsing in CloudWatch.
    
    This formatter converts log records to JSON objects with standardized fields,
    making them easier to query and analyze in CloudWatch Logs.
    """
    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record as a JSON string.
        
        Args:
            record: The log record to format
            
        Returns:
            A JSON string representation of the log record
        """
        log_record: Dict[str, Any] = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)
        
        # Add custom fields if present
        if hasattr(record, 'custom_fields') and isinstance(record.custom_fields, dict):
            for key, value in record.custom_fields.items():
                log_record[key] = value
        
        return json.dumps(log_record)

def setup_json_logging(name: Optional[str] = None) -> logging.Logger:
    """
    Set up a logger with JSON formatting for CloudWatch.
    
    Args:
        name: The name of the logger (defaults to 'obsidian-ai-assistant')
        
    Returns:
        A configured logger instance with JSON formatting
    """
    logger = logging.getLogger(name or 'obsidian-ai-assistant')
    
    # Set log level
    level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers = []
    
    # Add handler with JSON formatter
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = JsonFormatter()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger 