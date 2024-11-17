"""Utility functions for Chimera Logger"""

import os
import socket
import inspect
from typing import Dict, Any, Optional

def get_host_info() -> str:
    """Get host information with fallbacks"""
    try:
        for env_var in ['HOST_NAME', 'HOSTNAME']:
            host = os.getenv(env_var)
            if host:
                return host
        
        try:
            return socket.gethostname()
        except Exception:
            pass
        
        container_id = os.getenv('CONTAINER_ID')
        if not container_id:
            try:
                with open('/proc/self/cgroup', 'r') as f:
                    for line in f:
                        if 'docker' in line:
                            container_id = line.split('/')[-1].strip()
                            if container_id:
                                return f"container_{container_id[:12]}"
            except Exception:
                pass
        
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            pass
        
        return "unknown_host"
        
    except Exception:
        return "unknown_host"

def get_container_info() -> Optional[Dict[str, str]]:
    """Collect container information if available"""
    try:
        container_id = os.getenv('CONTAINER_ID')
        
        if not container_id:
            try:
                with open('/proc/self/cgroup', 'r') as f:
                    for line in f:
                        if 'docker' in line:
                            container_id = line.split('/')[-1].strip()
                            break
            except Exception:
                return None
                
        if container_id:
            info = {
                'id': container_id,
                'tag': os.getenv('CONTAINER_TAG'),
                'version': os.getenv('CONTAINER_VERSION')
            }
            return {k: v for k, v in info.items() if v is not None}
        return None
    except Exception:
        return None

def get_caller_info() -> Dict[str, Any]:
    """Get information about the calling code"""
    try:
        stack = inspect.stack()
        
        caller_frame = None
        for frame_info in stack[1:]:
            module = inspect.getmodule(frame_info.frame)
            if module:
                module_name = module.__name__
                if (not module_name.startswith('chimera_logging') and 
                    not module_name.startswith('logging')):
                    caller_frame = frame_info
                    break
        
        if caller_frame:
            module = inspect.getmodule(caller_frame.frame)
            return {
                "module": module.__name__ if module else "unknown_module",
                "function": caller_frame.function,
                "line": caller_frame.lineno,
                "file": os.path.basename(caller_frame.filename)
            }
    except Exception:
        pass
    
    return {
        "module": "unknown_module",
        "function": "unknown_function",
        "line": 0,
        "file": "unknown_file"
    }

def remove_none_values(d: Dict) -> Dict:
    """Recursively remove None values from dictionary"""
    try:
        return {
            k: remove_none_values(v) if isinstance(v, dict) else v
            for k, v in d.items()
            if v is not None
        }
    except Exception:
        return d
