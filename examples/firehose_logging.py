"""Example demonstrating Firehose logging with test_logs tag"""
from chimera_logging import create_logger
from chimera_logging.config import ChimeraConfig

def send_test_logs():
    # Create logger with test_logs.{component} format
    logger = create_logger("test_logs.example")

    # Send some test logs
    log_entry = logger.info(
        "Test message",
        extra={"test_id": "123"}
    )
    print("\nLog entry that will be sent to Firehose:")
    print(log_entry)

    try:
        raise ValueError("Test error")
    except Exception as e:
        log_entry = logger.exception(
            "Test error occurred",
            exc_info=e,
            extra={"test_id": "123"}
        )
        print("\nError log entry that will be sent to Firehose:")
        print(log_entry)

if __name__ == "__main__":
    # Check logging configuration
    print(f"Using {'Firehose' if ChimeraConfig.can_use_firehose() else 'local'} logging")
    print(f"Stream: {ChimeraConfig.get_stream_name()}")
    print(f"Region: {ChimeraConfig.get_region()}")
    
    send_test_logs()
