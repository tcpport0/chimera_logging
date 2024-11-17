"""Log message formatting and metadata collection"""

import os
import time
import logging
import traceback
import threading
from typing import Any, Dict, Optional
from .config import ChimeraConfig
from .utils import get_host_info, get_container_info, get_caller_info, remove_none_values

class ChimeraFormatter:
    """Handles log message formatting and metadata collection"""
    
    def __init__(
        self,
        tag: Optional[str] = None,
        environment: Optional[str] = None,
        host: Optional[str] = None
    ):
        # Get tag from environment or use provided tag
        self.tag = ChimeraConfig.get_tag() or tag
        if not self.tag:
            raise ValueError("tag is required either via environment variables or parameter")
            
        try:
            self.environment = environment or ChimeraConfig.get_environment()
            self._host = host or get_host_info()
            self._container_info = get_container_info()
            self._service = ChimeraConfig.get_service()  # May be None
        except Exception as e:
            logging.error(f"Error initializing ChimeraFormatter: {str(e)}")
            self.environment = "dev"
            self._host = host or "unknown_host"
            self._container_info = None
            self._service = None

    def format_log(
        self,
        message: str,
        level: str = "INFO",
        additional_meta: Optional[Dict[str, Any]] = None,
        additional_fields: Optional[Dict[str, Any]] = None,
        exc_info: Optional[BaseException] = None
    ) -> Dict[str, Any]:
        """Format a log message with metadata"""
        try:
            meta = {
                "timestamp": time.time(),
                "tag": self.tag,
                "environment": self.environment,
                "host": self._host
            }
            
            # Only add service if it's not None
            if self._service is not None:
                meta["service"] = self._service
            
            if self._container_info:
                meta["container"] = self._container_info
                
            if additional_meta:
                try:
                    meta.update(additional_meta)
                except Exception:
                    pass

            record = {
                "message": str(message),
                "level": level,
                **get_caller_info()
            }
            
            if additional_fields:
                try:
                    record.update(additional_fields)
                except Exception:
                    pass

            if exc_info:
                try:
                    record["error"] = {
                        "type": type(exc_info).__name__,
                        "message": str(exc_info),
                        "traceback": ''.join(traceback.format_exception(
                            type(exc_info),
                            exc_info,
                            exc_info.__traceback__,
                            limit=None,  # Include full traceback
                            chain=True   # Include cause chain
                        ))
                    }
                except Exception:
                    record["error"] = {
                        "message": "Error capturing exception details"
                    }

            return remove_none_values({
                "meta": meta,
                "record": record
            })
            
        except Exception as e:
            # Ensure we return a valid log entry even in case of errors
            try:
                timestamp = time.time()
            except Exception:
                timestamp = 0
                
            return {
                "meta": {
                    "timestamp": timestamp,
                    "tag": self.tag,
                    "environment": getattr(self, 'environment', 'dev'),
                    "host": getattr(self, '_host', 'unknown_host')
                },
                "record": {
                    "message": str(message),
                    "level": "ERROR",
                    "error": f"Error formatting log: {str(e)}",
                    **get_caller_info()
                }
            }
