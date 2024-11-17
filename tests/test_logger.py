"""Tests for main logger implementation"""

import sys
import pytest
from unittest.mock import patch, MagicMock
from chimera_logging.logger import ChimeraLogger, create_logger

@pytest.fixture
def mock_formatter():
    """Mock ChimeraFormatter fixture"""
    with patch('chimera_logging.logger.ChimeraFormatter') as mock:
        formatter = MagicMock()
        mock.return_value = formatter
        yield formatter

@pytest.fixture
def mock_firehose_handler():
    """Mock FirehoseHandler fixture"""
    with patch('chimera_logging.logger.FirehoseHandler') as mock:
        handler = MagicMock()
        mock.return_value = handler
        yield handler

@pytest.fixture
def mock_local_handler():
    """Mock LocalHandler fixture"""
    with patch('chimera_logging.logger.LocalHandler') as mock:
        handler = MagicMock()
        mock.return_value = handler
        yield handler

@pytest.fixture
def sample_log_entry():
    """Sample formatted log entry"""
    return {
        "meta": {
            "tag": "test-tag",
            "environment": "test"
        },
        "record": {
            "message": "test message",
            "level": "INFO"
        }
    }

class TestChimeraLogger:
    """Tests for ChimeraLogger class"""
    
    def test_initialization_with_firehose(self, mock_formatter, mock_firehose_handler):
        """Test logger initialization with Firehose handler"""
        with patch('chimera_logging.logger.ChimeraConfig.can_use_firehose', 
                  return_value=True):
            logger = ChimeraLogger(tag="test-tag")
            assert logger.formatter == mock_formatter
            assert logger.handler == mock_firehose_handler
            
    def test_initialization_with_local(self, mock_formatter, mock_local_handler):
        """Test logger initialization with local handler"""
        with patch('chimera_logging.logger.ChimeraConfig.can_use_firehose', 
                  return_value=False):
            logger = ChimeraLogger(tag="test-tag")
            assert logger.formatter == mock_formatter
            assert logger.handler == mock_local_handler
            
    def test_initialization_error(self):
        """Test logger initialization with error"""
        with patch('chimera_logging.logger.ChimeraFormatter') as mock_formatter:
            mock_formatter.side_effect = Exception("Formatter error")
            with patch('chimera_logging.logger.LocalHandler') as mock_local:
                handler = MagicMock()
                mock_local.return_value = handler
                
                logger = ChimeraLogger(tag="test-tag")
                # Should create a new formatter directly
                assert isinstance(logger.formatter, MagicMock)
                # Should fall back to local handler
                assert isinstance(logger.handler, MagicMock)
            
    def test_log_method(self, mock_formatter, mock_firehose_handler, sample_log_entry):
        """Test basic log method"""
        with patch('chimera_logging.logger.ChimeraConfig.can_use_firehose', 
                  return_value=True):
            logger = ChimeraLogger(tag="test-tag")
            mock_formatter.format_log.return_value = sample_log_entry
            
            result = logger.log("test message", "INFO")
            
            mock_formatter.format_log.assert_called_once_with(
                "test message", "INFO"
            )
            assert result == sample_log_entry
            
    def test_log_with_kwargs(self, mock_formatter, mock_firehose_handler, sample_log_entry):
        """Test log method with additional kwargs"""
        with patch('chimera_logging.logger.ChimeraConfig.can_use_firehose', 
                  return_value=True):
            logger = ChimeraLogger(tag="test-tag")
            mock_formatter.format_log.return_value = sample_log_entry
            
            additional_meta = {"request_id": "123"}
            additional_fields = {"correlation_id": "456"}
            
            logger.log(
                "test message",
                "INFO",
                additional_meta=additional_meta,
                additional_fields=additional_fields
            )
            
            mock_formatter.format_log.assert_called_once_with(
                "test message",
                "INFO",
                additional_meta=additional_meta,
                additional_fields=additional_fields
            )
            
    def test_log_error_handling(self, mock_formatter, mock_firehose_handler):
        """Test log method error handling"""
        with patch('chimera_logging.logger.ChimeraConfig.can_use_firehose', 
                  return_value=True):
            logger = ChimeraLogger(tag="test-tag")
            mock_formatter.format_log.side_effect = Exception("Format error")
            
            result = logger.log("test message")
            assert result == {}
            
    def test_info_method(self, mock_formatter, mock_firehose_handler, sample_log_entry):
        """Test info level logging"""
        with patch('chimera_logging.logger.ChimeraConfig.can_use_firehose', 
                  return_value=True):
            logger = ChimeraLogger(tag="test-tag")
            mock_formatter.format_log.return_value = sample_log_entry
            
            logger.info("test message")
            
            mock_formatter.format_log.assert_called_once_with(
                "test message", "INFO"
            )
            
    def test_warning_method(self, mock_formatter, mock_firehose_handler, sample_log_entry):
        """Test warning level logging"""
        with patch('chimera_logging.logger.ChimeraConfig.can_use_firehose', 
                  return_value=True):
            logger = ChimeraLogger(tag="test-tag")
            mock_formatter.format_log.return_value = sample_log_entry
            
            logger.warning("test message")
            
            mock_formatter.format_log.assert_called_once_with(
                "test message", "WARNING"
            )
            
    def test_error_method(self, mock_formatter, mock_firehose_handler, sample_log_entry):
        """Test error level logging"""
        with patch('chimera_logging.logger.ChimeraConfig.can_use_firehose', 
                  return_value=True):
            logger = ChimeraLogger(tag="test-tag")
            mock_formatter.format_log.return_value = sample_log_entry
            
            logger.error("test message")
            
            mock_formatter.format_log.assert_called_once_with(
                "test message", "ERROR"
            )
            
    def test_exception_method(self, mock_formatter, mock_firehose_handler, sample_log_entry):
        """Test exception logging"""
        with patch('chimera_logging.logger.ChimeraConfig.can_use_firehose', 
                  return_value=True):
            logger = ChimeraLogger(tag="test-tag")
            mock_formatter.format_log.return_value = sample_log_entry
            
            try:
                raise ValueError("Test error")
            except Exception as e:
                logger.exception("Error occurred", exc_info=e)
                
            mock_formatter.format_log.assert_called_once()
            args = mock_formatter.format_log.call_args[0]
            kwargs = mock_formatter.format_log.call_args[1]
            assert args[0] == "Error occurred"
            assert args[1] == "ERROR"
            assert isinstance(kwargs['exc_info'], ValueError)
            
    def test_exception_without_exc_info(self, mock_formatter, mock_firehose_handler):
        """Test exception logging without explicit exc_info"""
        with patch('chimera_logging.logger.ChimeraConfig.can_use_firehose', 
                  return_value=True):
            logger = ChimeraLogger(tag="test-tag")
            
            try:
                raise ValueError("Test error")
            except Exception:
                logger.exception("Error occurred")
                
            mock_formatter.format_log.assert_called_once()
            kwargs = mock_formatter.format_log.call_args[1]
            assert isinstance(kwargs['exc_info'], ValueError)

def test_create_logger():
    """Test create_logger factory function"""
    with patch('chimera_logging.logger.ChimeraLogger') as mock_logger:
        logger = create_logger(tag="test-tag")
        mock_logger.assert_called_once_with(tag="test-tag")
        assert logger == mock_logger.return_value
