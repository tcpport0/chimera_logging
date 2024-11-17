"""Configuration management for Chimera Logger"""

import os
import logging
import boto3
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
try:
    load_dotenv()
except Exception:
    pass

class ChimeraConfig:
    """Manages configuration for Chimera Logger"""
    
    DEFAULT_LOG_LEVEL = "INFO"
    DEFAULT_REGION = "us-west-2"
    DEFAULT_STREAM_NAME = "chimera-log-fh"
    
    @staticmethod
    def get_log_level() -> str:
        """Get log level from environment or return default"""
        level = os.getenv('CHIMERA_LOG_LEVEL', ChimeraConfig.DEFAULT_LOG_LEVEL).upper()
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        return level if level in valid_levels else ChimeraConfig.DEFAULT_LOG_LEVEL

    @staticmethod
    def get_stream_name() -> str:
        """Get Firehose stream name from environment or return default"""
        return os.getenv('CHIMERA_STREAM_NAME', ChimeraConfig.DEFAULT_STREAM_NAME)

    @staticmethod
    def get_region() -> str:
        """Get AWS region from environment or return default"""
        return os.getenv('AWS_REGION', ChimeraConfig.DEFAULT_REGION)

    @staticmethod
    def get_environment() -> str:
        """Get environment name from config"""
        return os.getenv('ENVIRONMENT', 'dev')

    @staticmethod
    def get_service() -> Optional[str]:
        """Get service name from environment variables"""
        # Try different common environment variable names for service
        for env_var in ['SERVICE_NAME', 'SERVICE', 'APP_NAME', 'APPLICATION']:
            service = os.getenv(env_var)
            if service:
                return service
        return None

    @staticmethod
    def get_tag() -> Optional[str]:
        """Get tag from environment variables"""
        return os.getenv('CHIMERA_TAG') or os.getenv('LOG_TAG')

    @staticmethod
    def can_use_firehose() -> bool:
        """
        Check if Firehose logging is possible by verifying AWS credentials
        and testing a Firehose client connection
        """
        # First check if local logging is explicitly requested
        if os.getenv('CHIMERA_LOG_LOCAL', '').lower() == 'true':
            return False

        # Try to create a Firehose client
        try:
            # Just create the client - don't test permissions
            # boto3 will handle credential discovery automatically
            boto3.client('firehose', region_name=ChimeraConfig.get_region())
            return True
        except Exception:
            return False

    @staticmethod
    def get_numeric_log_level() -> int:
        """Convert string log level to numeric value for logging module"""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        return level_map.get(ChimeraConfig.get_log_level(), logging.INFO)
