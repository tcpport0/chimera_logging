"""Tests for utility functions"""

import os
import socket
import pytest
from unittest.mock import patch, mock_open
from chimera_logging.utils import (
    get_host_info,
    get_container_info,
    get_caller_info,
    remove_none_values
)

def test_get_host_info_from_env():
    """Test get_host_info when HOST_NAME is set"""
    with patch.dict(os.environ, {'HOST_NAME': 'test-host'}):
        assert get_host_info() == 'test-host'

def test_get_host_info_from_hostname_env():
    """Test get_host_info when HOSTNAME is set"""
    with patch.dict(os.environ, {'HOSTNAME': 'test-hostname'}):
        assert get_host_info() == 'test-hostname'

def test_get_host_info_from_socket():
    """Test get_host_info using socket.gethostname"""
    with patch.dict(os.environ, clear=True):
        with patch('socket.gethostname', return_value='socket-host'):
            assert get_host_info() == 'socket-host'

def test_get_host_info_from_container():
    """Test get_host_info with container ID from cgroup"""
    mock_cgroup_content = """
    11:devices:/docker/1234567890abcdef1234567890abcdef
    10:cpu,cpuacct:/docker/1234567890abcdef1234567890abcdef
    """
    with patch.dict(os.environ, clear=True):
        with patch('socket.gethostname', side_effect=Exception):
            with patch('builtins.open', mock_open(read_data=mock_cgroup_content)):
                assert get_host_info() == 'container_1234567890ab'

def test_get_host_info_fallback():
    """Test get_host_info fallback to unknown_host"""
    with patch.dict(os.environ, clear=True):
        with patch('socket.gethostname', side_effect=Exception):
            with patch('builtins.open', side_effect=Exception):
                assert get_host_info() == 'unknown_host'

def test_get_container_info_from_env():
    """Test get_container_info when environment variables are set"""
    container_env = {
        'CONTAINER_ID': '1234567890ab',
        'CONTAINER_TAG': 'latest',
        'CONTAINER_VERSION': '1.0.0'
    }
    with patch.dict(os.environ, container_env):
        container_info = get_container_info()
        assert container_info == {
            'id': '1234567890ab',
            'tag': 'latest',
            'version': '1.0.0'
        }

def test_get_container_info_from_cgroup():
    """Test get_container_info reading from cgroup"""
    mock_cgroup_content = """
    11:devices:/docker/1234567890abcdef1234567890abcdef
    10:cpu,cpuacct:/docker/1234567890abcdef1234567890abcdef
    """
    with patch.dict(os.environ, {'CONTAINER_TAG': 'latest'}):
        with patch('builtins.open', mock_open(read_data=mock_cgroup_content)):
            container_info = get_container_info()
            assert container_info == {
                'id': '1234567890abcdef1234567890abcdef',
                'tag': 'latest'
            }

def test_get_container_info_no_container():
    """Test get_container_info when not in container"""
    with patch.dict(os.environ, clear=True):
        with patch('builtins.open', side_effect=Exception):
            assert get_container_info() is None

def test_get_caller_info():
    """Test get_caller_info returns correct information"""
    caller_info = get_caller_info()
    assert isinstance(caller_info, dict)
    assert all(key in caller_info for key in ['module', 'function', 'line', 'file'])

def test_get_caller_info_exception():
    """Test get_caller_info handles exceptions gracefully"""
    with patch('inspect.stack', side_effect=Exception):
        caller_info = get_caller_info()
        assert caller_info == {
            "module": "unknown_module",
            "function": "unknown_function",
            "line": 0,
            "file": "unknown_file"
        }

@pytest.mark.parametrize("input_dict, expected", [
    (
        {"a": 1, "b": None, "c": {"d": None, "e": 2}},
        {"a": 1, "c": {"e": 2}}
    ),
    (
        {"a": None},
        {}
    ),
    (
        {"a": 1, "b": 2},
        {"a": 1, "b": 2}
    ),
    (
        {"a": {"b": {"c": None}}},
        {"a": {"b": {}}}
    )
])
def test_remove_none_values(input_dict, expected):
    """Test remove_none_values with various dictionary structures"""
    assert remove_none_values(input_dict) == expected

def test_remove_none_values_exception():
    """Test remove_none_values handles exceptions gracefully"""
    class BadDict(dict):
        def items(self):
            raise Exception("Bad dictionary")
    
    bad_dict = BadDict()
    assert remove_none_values(bad_dict) == bad_dict
