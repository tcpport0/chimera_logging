"""
Chimera Logger - A structured logging client for AWS Kinesis Firehose

This package provides a robust, non-blocking logging solution with support for:
- Asynchronous logging to AWS Kinesis Firehose
- Local logging with rich context
- Environment-based configuration
- Container and host information collection
- Full exception chain capture
"""

from dotenv import load_dotenv

# Load environment variables but never fail if .env doesn't exist
try:
    load_dotenv()
except Exception:
    pass

from .logger import create_logger, ChimeraLogger
from .config import ChimeraConfig

__all__ = [
    'create_logger',
    'ChimeraLogger',
    'ChimeraConfig'
]

__version__ = '1.0.0'
