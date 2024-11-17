# Chimera Logger

A structured logging client that combines the power of local and cloud logging, much like the mythical Chimera that combined different creatures. It seamlessly formats logs and ships them to AWS Kinesis Firehose while providing automatic fallback to local logging when Firehose is unavailable.

## Features

- Structured logging with consistent JSON formatting
- Automatic metadata collection (host, environment, container info)
- Seamless AWS Kinesis Firehose integration
- Configurable via environment variables
- Automatic fallback to local logging when Firehose is unavailable
- Exception tracking with full stack traces
- Thread-safe batch logging support
- Concurrent logging in multi-threaded applications
- Zero-exception design - logging never breaks your application

## Installation

### Basic Installation
```bash
pip install chimera-logging
```

### Requirements
- Python 3.10 or higher
- AWS credentials (if using Firehose integration)
- boto3 (automatically installed)
- python-dotenv (automatically installed)

## Quick Start

```python
from chimera_logging import create_logger

# Create a logger with a tag
logger = create_logger("myapp.component")

# Or use environment variable for tag
# export CHIMERA_TAG="myapp.component"
logger = create_logger()  # Will use CHIMERA_TAG from environment

# Log messages at different levels
logger.info("Application started")
logger.warning("Resource running low", meta={"component": "memory"}, extra={"usage": 85})
logger.error("Operation failed", meta={"operation": "data_sync"})

# Log exceptions with full stack traces
try:
    raise ValueError("Invalid input")
except Exception as e:
    logger.exception("Error processing request", exc_info=e)
```

## Configuration

The logger can be configured using environment variables:

### Required for Firehose Logging
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key

### Optional Configuration
- `CHIMERA_TAG` or `LOG_TAG`: Default tag for all loggers. If set, you can create loggers without explicitly providing a tag.
- `CHIMERA_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Default: INFO
- `CHIMERA_STREAM_NAME`: Firehose stream name. Default: chimera-log-fh
- `AWS_REGION`: AWS region. Default: us-west-2
- `ENVIRONMENT`: Environment name (dev, prod, etc). Default: dev
- `CHIMERA_LOG_LOCAL`: Set to "true" to force local logging even if AWS credentials are available
- `HOST_NAME` or `HOSTNAME`: Host identifier
- `CONTAINER_ID`: Container ID (auto-detected if running in Docker)
- `CONTAINER_TAG`: Container image tag
- `CONTAINER_VERSION`: Container version
- `SERVICE_NAME` or `SERVICE`: Service name for additional context (also supports `APP_NAME`, `APPLICATION`)

## Local vs Firehose Logging

The logger automatically determines whether to use Firehose or local logging based on:

1. The presence of AWS credentials
2. The ability to connect to Firehose
3. The `CHIMERA_LOG_LOCAL` environment variable

If Firehose logging is not possible, it automatically falls back to local logging with the same API.

## Advanced Usage

### Tag Configuration

You can configure the logger's tag in two ways:

1. Via environment variable:
```bash
export CHIMERA_TAG="myapp.component"
logger = create_logger()  # Uses CHIMERA_TAG from environment
```

2. Via parameter:
```python
logger = create_logger("myapp.component")  # Explicitly set tag
```

If both are set, the parameter takes precedence over the environment variable.

### Additional Context

The logger supports two types of additional context:

1. `meta`: Override or add to the metadata section
```python
logger.info(
    "User action completed",
    meta={"source": "auth_service"}
)
```

2. `extra`: Add custom fields to the record section
```python
logger.info(
    "User action completed",
    extra={"user_id": 123, "action": "login"}
)
```

You can use both together:
```python
logger.info(
    "User action completed",
    meta={"source": "auth_service"},
    extra={"user_id": 123, "action": "login"}
)
```

### Batch Logging

```python
from chimera_logging import FirehoseHandler, ChimeraFormatter

formatter = ChimeraFormatter("myapp.batch")
handler = FirehoseHandler()

entries = [
    formatter.format_log("Message 1"),
    formatter.format_log("Message 2")
]

result = handler.send_batch(entries)
print(f"Sent: {result['sent']}, Failed: {result['failed']}")
```

### Thread-Safe Logging

The logger is designed to be thread-safe and can be used in multi-threaded applications:

```python
import threading
from chimera_logging import create_logger

logger = create_logger("myapp.worker")

def worker(thread_id):
    logger.info(
        "Worker started",
        extra={"thread_id": thread_id}
    )
    # ... do work ...
    logger.info(
        "Worker completed",
        extra={"thread_id": thread_id}
    )

# Create multiple threads
threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
for thread in threads:
    thread.start()
```

## Error Handling

The logger is designed to never raise exceptions during normal operation. If an error occurs:

1. For initialization errors: Safe defaults are used
2. For formatting errors: A minimal valid log entry is created
3. For delivery errors: The operation returns False but doesn't raise

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/mattpeters/chimera_logging.git
cd chimera_logging
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -e ".[dev]"
```

## Running Tests

The project uses pytest for testing. To run the tests:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=chimera_logging

# Run specific test file
pytest tests/test_logger.py
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes:

1. Fork the repository
2. Create a feature branch
3. Add tests for any new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
