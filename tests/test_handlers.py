"""Tests for log handlers"""

import json
import time
import pytest
import logging
import threading
from unittest.mock import patch, MagicMock, call
from chimera_logging.handlers import (
    LogBuffer,
    BaseHandler,
    FirehoseHandler,
    LocalHandler
)

@pytest.fixture
def log_entry():
    """Sample log entry fixture"""
    return {
        "meta": {
            "timestamp": time.time(),
            "tag": "test-tag"
        },
        "record": {
            "message": "test message",
            "level": "INFO"
        }
    }

class TestLogBuffer:
    """Tests for LogBuffer class"""
    
    def test_buffer_initialization(self):
        """Test buffer initialization"""
        buffer = LogBuffer(max_size=10, flush_interval=2.0)
        assert len(buffer.buffer) == 0
        assert buffer.max_size == 10
        assert buffer.flush_interval == 2.0
        
    def test_add_entry(self):
        """Test adding entry to buffer"""
        buffer = LogBuffer()
        entry = {"test": "entry"}
        should_flush = buffer.add(entry)
        
        assert len(buffer.buffer) == 1
        assert buffer.buffer[0] == entry
        assert not should_flush  # Shouldn't flush with just one entry
        
    def test_buffer_size_trigger(self):
        """Test buffer triggers flush on size"""
        buffer = LogBuffer(max_size=2)
        buffer.add({"test": "1"})
        should_flush = buffer.add({"test": "2"})
        
        assert should_flush  # Should flush when reaching max_size
        
    def test_buffer_time_trigger(self):
        """Test buffer triggers flush on time"""
        buffer = LogBuffer(flush_interval=0.1)
        buffer.add({"test": "1"})
        time.sleep(0.2)  # Wait longer than flush interval
        should_flush = buffer.add({"test": "2"})
        
        assert should_flush  # Should flush after interval
        
    def test_get_and_clear(self):
        """Test getting and clearing buffer"""
        buffer = LogBuffer()
        entries = [{"test": str(i)} for i in range(3)]
        for entry in entries:
            buffer.add(entry)
            
        result = buffer.get_and_clear()
        assert result == entries
        assert len(buffer.buffer) == 0

class TestBaseHandler:
    """Tests for BaseHandler class"""
    
    def test_base_handler_send(self):
        """Test BaseHandler send method raises NotImplementedError"""
        handler = BaseHandler()
        with pytest.raises(NotImplementedError):
            handler.send({"test": "entry"})

class TestFirehoseHandler:
    """Tests for FirehoseHandler class"""
    
    @pytest.fixture
    def mock_firehose(self):
        """Mock Firehose client fixture"""
        with patch('boto3.client') as mock_client:
            mock_firehose = MagicMock()
            mock_client.return_value = mock_firehose
            yield mock_firehose
            
    def test_initialization(self, mock_firehose):
        """Test FirehoseHandler initialization"""
        handler = FirehoseHandler(stream_name="test-stream")
        assert handler.stream_name == "test-stream"
        assert handler.client == mock_firehose
        assert isinstance(handler.buffer, LogBuffer)
        
    def test_initialization_error(self):
        """Test FirehoseHandler initialization with error"""
        with patch('boto3.client', side_effect=Exception("AWS Error")):
            handler = FirehoseHandler()
            assert handler.client is None
            
    def test_send_success(self, mock_firehose, log_entry):
        """Test successful log sending"""
        handler = FirehoseHandler()
        result = handler.send(log_entry)
        assert result is True
        
    def test_send_failure(self, log_entry):
        """Test log sending failure"""
        handler = FirehoseHandler()
        handler.client = None  # Simulate no client
        result = handler.send(log_entry)
        assert result is False
        
    def test_batch_send(self, mock_firehose, log_entry):
        """Test batch sending of logs"""
        handler = FirehoseHandler()
        mock_firehose.put_record_batch.return_value = {
            'FailedPutCount': 0
        }
        
        result = handler._send_batch([log_entry])
        assert result["sent"] == 1
        assert result["failed"] == 0
        
        # Verify correct format of records
        calls = mock_firehose.put_record_batch.call_args_list
        assert len(calls) == 1
        args, kwargs = calls[0]
        records = kwargs['Records']
        assert len(records) == 1
        assert 'Data' in records[0]
        # Verify JSON is properly formatted
        log_data = json.loads(records[0]['Data'].strip())
        assert log_data == log_entry

class TestLocalHandler:
    """Tests for LocalHandler class"""
    
    @pytest.fixture
    def handler(self):
        """LocalHandler fixture"""
        return LocalHandler()
        
    def test_initialization(self, handler):
        """Test LocalHandler initialization"""
        assert isinstance(handler.logger, logging.Logger)
        assert handler.logger.name == 'chimera'
        assert len(handler.logger.handlers) > 0
        assert isinstance(handler.queue, type(handler.queue))
        
    def test_send_success(self, handler, log_entry):
        """Test successful log sending"""
        result = handler.send(log_entry)
        assert result is True
        
        # Let the background thread process the log
        time.sleep(0.1)
        
    def test_send_failure(self, handler, log_entry):
        """Test log sending failure"""
        handler.queue = None  # Simulate broken queue
        result = handler.send(log_entry)
        assert result is False
        
    def test_log_entry_processing(self, handler, log_entry):
        """Test log entry processing"""
        with patch.object(handler.logger, 'log') as mock_log:
            handler._log_entry(log_entry)
            mock_log.assert_called_once()
            
    def test_log_entry_with_error(self, handler):
        """Test log entry processing with error information"""
        log_entry = {
            "record": {
                "message": "Error occurred",
                "level": "ERROR",
                "error": {
                    "message": "Test error",
                    "traceback": "Test traceback"
                }
            }
        }
        
        with patch.object(handler.logger, 'log') as mock_log:
            handler._log_entry(log_entry)
            mock_log.assert_called_once()
            # Verify error info is included in message
            args = mock_log.call_args[0]
            assert "Test error" in args[1]
            assert "Test traceback" in args[1]
            
    def test_cleanup(self, handler):
        """Test cleanup process"""
        test_entry = {"test": "cleanup"}
        handler.queue.put(test_entry)
        
        with patch.object(handler, '_log_entry') as mock_log:
            handler._cleanup()
            # Verify remaining logs are processed
            mock_log.assert_called_with(test_entry)
