"""Tests for log message formatting"""

import os
import time
import pytest
from unittest.mock import patch, MagicMock
from chimera_logging.formatters import ChimeraFormatter

@pytest.fixture
def formatter():
    """Basic formatter fixture"""
    return ChimeraFormatter(tag="test-tag")

@pytest.fixture
def full_formatter():
    """Formatter with all optional parameters"""
    return ChimeraFormatter(
        tag="test-tag",
        environment="test",
        host="test-host"
    )

def test_formatter_initialization():
    """Test basic formatter initialization"""
    formatter = ChimeraFormatter(tag="test-tag")
    assert formatter.tag == "test-tag"
    assert formatter.environment == "dev"  # Default value
    assert formatter._host is not None

def test_formatter_initialization_with_env():
    """Test formatter initialization with environment variables"""
    with patch.dict(os.environ, {
        'CHIMERA_TAG': 'env-tag',
        'ENVIRONMENT': 'production',
        'SERVICE_NAME': 'test-service'
    }):
        formatter = ChimeraFormatter()
        assert formatter.tag == 'env-tag'
        assert formatter.environment == 'production'
        assert formatter._service == 'test-service'

def test_formatter_initialization_error():
    """Test formatter initialization with error"""
    with patch.dict(os.environ, clear=True):
        with pytest.raises(ValueError, match="tag is required"):
            ChimeraFormatter()  # Should raise error when no tag provided

def test_format_log_basic(formatter):
    """Test basic log formatting"""
    log_entry = formatter.format_log("test message")
    
    assert isinstance(log_entry, dict)
    assert "meta" in log_entry
    assert "record" in log_entry
    
    meta = log_entry["meta"]
    assert meta["tag"] == "test-tag"
    assert meta["environment"] == "dev"
    assert isinstance(meta["timestamp"], float)
    assert meta["host"] is not None
    
    record = log_entry["record"]
    assert record["message"] == "test message"
    assert record["level"] == "INFO"
    assert "module" in record
    assert "function" in record
    assert "line" in record
    assert "file" in record

def test_format_log_with_meta(formatter):
    """Test log formatting with metadata"""
    meta = {
        "request_id": "123",
        "user_id": "456"
    }
    
    log_entry = formatter.format_log(
        "test message",
        meta=meta
    )
    
    meta_section = log_entry["meta"]
    assert meta_section["request_id"] == "123"
    assert meta_section["user_id"] == "456"

def test_format_log_with_extra(formatter):
    """Test log formatting with extra fields"""
    extra = {
        "correlation_id": "789",
        "duration_ms": 150
    }
    
    log_entry = formatter.format_log(
        "test message",
        extra=extra
    )
    
    record = log_entry["record"]
    assert record["correlation_id"] == "789"
    assert record["duration_ms"] == 150

def test_format_log_with_exception(formatter):
    """Test log formatting with exception information"""
    try:
        raise ValueError("Test error")
    except Exception as e:
        log_entry = formatter.format_log(
            "Error occurred",
            level="ERROR",
            exc_info=e
        )
        
        record = log_entry["record"]
        assert record["level"] == "ERROR"
        assert "error" in record
        error_info = record["error"]
        assert error_info["type"] == "ValueError"
        assert error_info["message"] == "Test error"
        assert "Traceback" in error_info["traceback"]
        assert "ValueError: Test error" in error_info["traceback"]

def test_format_log_with_container(formatter):
    """Test log formatting with container information"""
    container_info = {
        "id": "test-container",
        "tag": "latest",
        "version": "1.0.0"
    }
    
    with patch('chimera_logging.utils.get_container_info', return_value=container_info):
        formatter._container_info = container_info  # Set container info directly
        log_entry = formatter.format_log("test message")
        
        meta = log_entry["meta"]
        assert "container" in meta
        assert meta["container"] == container_info

def test_format_log_error_handling(formatter):
    """Test log formatting error handling"""
    with patch('chimera_logging.formatters.time.time', side_effect=Exception("Time error")):
        log_entry = formatter.format_log("test message")
        
        # Should still return a valid log entry with basic info
        assert isinstance(log_entry, dict)
        assert "meta" in log_entry
        assert "record" in log_entry
        assert log_entry["record"]["level"] == "ERROR"
        assert "Error formatting log" in log_entry["record"]["error"]

def test_format_log_with_service(formatter):
    """Test log formatting with service information"""
    with patch.dict(os.environ, {'SERVICE_NAME': 'test-service'}):
        formatter = ChimeraFormatter(tag="test-tag")
        log_entry = formatter.format_log("test message")
        
        meta = log_entry["meta"]
        assert meta["service"] == "test-service"

def test_format_log_none_values_removed(formatter):
    """Test that None values are removed from log entries"""
    meta = {
        "valid_field": "value",
        "none_field": None
    }
    
    log_entry = formatter.format_log(
        "test message",
        meta=meta
    )
    
    meta_section = log_entry["meta"]
    assert "valid_field" in meta_section
    assert "none_field" not in meta_section
