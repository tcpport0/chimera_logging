"""Main logger implementation"""

import sys
import logging
from typing import Any, Dict, Optional
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock
from .config import ChimeraConfig
from .formatters import ChimeraFormatter
from .handlers import FirehoseHandler, LocalHandler

# Global thread pool for async operations
_thread_pool = ThreadPoolExecutor(max_workers=2)

class ChimeraLogger:
    """Main logger class with async logging support"""
    
    def __init__(
        self,
        tag: Optional[str] = None,
        stream_name: Optional[str] = None,
        environment: Optional[str] = None,
        region: Optional[str] = None
    ):
        try:
            self.formatter = ChimeraFormatter(tag, environment)
            
            if ChimeraConfig.can_use_firehose():
                self.handler = FirehoseHandler(stream_name, region)
            else:
                self.handler = LocalHandler()
                
        except Exception as e:
            logging.error(f"Error initializing ChimeraLogger: {str(e)}")
            # Create a basic formatter and local handler for fallback
            try:
                self.formatter = ChimeraFormatter(tag or "unknown")
            except Exception:
                # If formatter creation fails again, use a mock formatter
                self.formatter = MagicMock()
                self.formatter.format_log.return_value = {}
            
            try:
                self.handler = LocalHandler()
            except Exception:
                # If handler creation fails, use a mock handler
                self.handler = MagicMock()
                self.handler.send.return_value = True
        
    def log(
        self,
        message: str,
        level: str = "INFO",
        **kwargs
    ) -> Dict[str, Any]:
        """Asynchronously log a message"""
        try:
            log_entry = self.formatter.format_log(message, level, **kwargs)
            _thread_pool.submit(self.handler.send, log_entry)
            return log_entry
        except Exception:
            return {}

    def info(self, message: str, **kwargs) -> Dict[str, Any]:
        """Send INFO level log"""
        return self.log(message, "INFO", **kwargs)

    def warning(self, message: str, **kwargs) -> Dict[str, Any]:
        """Send WARNING level log"""
        return self.log(message, "WARNING", **kwargs)

    def error(self, message: str, **kwargs) -> Dict[str, Any]:
        """Send ERROR level log"""
        return self.log(message, "ERROR", **kwargs)

    def exception(
        self,
        message: str,
        exc_info: Optional[BaseException] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Send ERROR level log with exception information"""
        try:
            if exc_info is None:
                exc_info = sys.exc_info()[1]
            return self.log(message, "ERROR", exc_info=exc_info, **kwargs)
        except Exception:
            return {}

def create_logger(tag: Optional[str] = None) -> ChimeraLogger:
    """Factory function to create a ChimeraLogger instance"""
    return ChimeraLogger(tag=tag)
