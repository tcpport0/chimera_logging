"""Log handlers for different output destinations"""

import json
import time
import logging
import threading
import queue
import atexit
import boto3
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor
from .config import ChimeraConfig

# Global thread pool for async operations
_thread_pool = ThreadPoolExecutor(max_workers=2)

class LogBuffer:
    """Thread-safe buffer for batching logs"""
    
    def __init__(self, max_size: int = 100, flush_interval: float = 1.0):
        self.buffer = []
        self.lock = threading.Lock()
        self.max_size = max_size
        self.flush_interval = flush_interval
        self.last_flush = time.time()
        
    def add(self, log_entry: Dict[str, Any]) -> bool:
        """Add log entry to buffer, return True if buffer should be flushed"""
        with self.lock:
            self.buffer.append(log_entry)
            should_flush = len(self.buffer) >= self.max_size or \
                          time.time() - self.last_flush >= self.flush_interval
            return should_flush
            
    def get_and_clear(self) -> List[Dict[str, Any]]:
        """Get all logs and clear buffer"""
        with self.lock:
            logs = self.buffer.copy()
            self.buffer.clear()
            self.last_flush = time.time()
            return logs

class BaseHandler:
    """Base class for log handlers"""
    
    def send(self, log_entry: Dict[str, Any]) -> bool:
        """Send a log entry"""
        raise NotImplementedError("Handlers must implement send method")
        
    def _cleanup(self):
        """Cleanup handler resources"""
        pass

class FirehoseHandler(BaseHandler):
    """Handles asynchronous sending of logs to AWS Kinesis Firehose"""
    
    def __init__(self, stream_name: Optional[str] = None, region: Optional[str] = None):
        try:
            self.stream_name = stream_name or ChimeraConfig.get_stream_name()
            self.client = boto3.client('firehose', region_name=region or ChimeraConfig.get_region())
            self.buffer = LogBuffer()
            self._start_background_thread()
        except Exception as e:
            logging.error(f"Error initializing FirehoseHandler: {str(e)}")
            self.client = None
            
    def _start_background_thread(self):
        """Start background thread for processing logs"""
        def flush_logs():
            while True:
                try:
                    time.sleep(0.1)  # Prevent tight loop
                    logs = self.buffer.get_and_clear()
                    if logs:
                        self._send_batch(logs)
                except Exception:
                    pass  # Never crash the background thread
                    
        thread = threading.Thread(target=flush_logs, daemon=True)
        thread.start()
        
        # Register cleanup on exit
        atexit.register(self._cleanup)
        
    def _cleanup(self):
        """Flush remaining logs on exit"""
        try:
            logs = self.buffer.get_and_clear()
            if logs:
                self._send_batch(logs)
        except Exception:
            pass

    def send(self, log_entry: Dict[str, Any]) -> bool:
        """Queue log entry for async sending"""
        if not self.client:
            return False
            
        try:
            should_flush = self.buffer.add(log_entry)
            if should_flush:
                _thread_pool.submit(self._send_batch, self.buffer.get_and_clear())
            return True
        except Exception:
            return False

    def _send_batch(self, log_entries: List[Dict[str, Any]]) -> Dict[str, int]:
        """Send batch of logs to Firehose"""
        if not self.client or not log_entries:
            return {"sent": 0, "failed": len(log_entries) if log_entries else 0}
            
        try:
            response = self.client.put_record_batch(
                DeliveryStreamName=self.stream_name,
                Records=[{'Data': json.dumps(entry) + '\n'} for entry in log_entries]
            )
            
            return {
                "sent": len(log_entries) - response.get('FailedPutCount', 0),
                "failed": response.get('FailedPutCount', 0)
            }
        except Exception:
            return {"sent": 0, "failed": len(log_entries)}

class LocalHandler(BaseHandler):
    """Handles local logging with async queue"""
    
    def __init__(self):
        self.logger = logging.getLogger('chimera')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        self.logger.setLevel(ChimeraConfig.get_numeric_log_level())
        self.queue = queue.Queue()
        self._start_background_thread()
        
    def _start_background_thread(self):
        """Start background thread for processing logs"""
        def process_logs():
            while True:
                try:
                    log_entry = self.queue.get()
                    if log_entry is None:  # Shutdown signal
                        break
                    self._log_entry(log_entry)
                except Exception:
                    pass  # Never crash the background thread
                    
        thread = threading.Thread(target=process_logs, daemon=True)
        thread.start()
        
        # Register cleanup on exit
        atexit.register(self._cleanup)
        
    def _cleanup(self):
        """Process remaining logs on exit"""
        try:
            self.queue.put(None)  # Signal shutdown
            while not self.queue.empty():
                log_entry = self.queue.get_nowait()
                if log_entry is not None:
                    self._log_entry(log_entry)
        except Exception:
            pass

    def send(self, log_entry: Dict[str, Any]) -> bool:
        """Queue log entry for async processing"""
        try:
            self.queue.put(log_entry)
            return True
        except Exception:
            return False

    def _log_entry(self, log_entry: Dict[str, Any]):
        """Process a single log entry"""
        try:
            level = getattr(logging, log_entry['record']['level'], logging.INFO)
            message = log_entry['record']['message']
            
            if 'error' in log_entry['record']:
                error_info = log_entry['record']['error']
                if isinstance(error_info, dict):
                    message += f"\nError: {error_info.get('message', '')}"
                    if 'traceback' in error_info:
                        message += f"\nTraceback:\n{error_info['traceback']}"
            
            context = {k: v for k, v in log_entry['record'].items() 
                      if k not in ['message', 'error', 'level']}
            if context:
                message += f"\nContext: {json.dumps(context, indent=2)}"
            
            self.logger.log(level, message)
        except Exception:
            pass
