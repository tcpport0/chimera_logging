"""Basic usage example for Chimera Logger"""

import os
from chimera_logging import create_logger

# Optional: Set environment variables for configuration
os.environ['CHIMERA_LOG_LEVEL'] = 'DEBUG'  # Set to DEBUG for development
os.environ['ENVIRONMENT'] = 'dev'

# Create a logger with a tag
logger = create_logger("myapp.example")

# Basic logging
logger.info("Application started")
logger.debug("Debug information")
logger.warning("Warning message")

# Logging with additional context
logger.info(
    "User logged in",
    additional_meta={'source': 'auth_service'},
    additional_fields={'user_id': 123, 'login_method': 'oauth'}
)

# Error logging with exception information
try:
    result = 1 / 0
except Exception as e:
    logger.exception(
        "Division by zero error",
        exc_info=e,
        additional_fields={'operation': 'calculation'}
    )

# Logging with different levels and contexts
logger.error(
    "Database connection failed",
    additional_meta={'component': 'database'},
    additional_fields={
        'host': 'db.example.com',
        'port': 5432,
        'retry_count': 3
    }
)
