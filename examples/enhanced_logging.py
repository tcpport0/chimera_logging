"""Example demonstrating enhanced logging features"""

import os
import time
import threading
from chimera_logging import create_logger

def setup_environment():
    """Setup environment variables for the example"""
    # Configure service and environment
    os.environ['SERVICE_NAME'] = 'example-service'
    os.environ['ENVIRONMENT'] = 'development'
    
    # Configure tag for first logger
    os.environ['CHIMERA_TAG'] = 'env.worker'

def simulate_work(logger, thread_id):
    """Simulate some work with logging"""
    try:
        # Log some info
        logger.info(f"Starting work in thread {thread_id}", 
                   extra={"thread_id": thread_id})
        
        # Simulate processing
        time.sleep(0.5)
        
        # Simulate some warnings
        if thread_id % 2 == 0:
            logger.warning(f"Process {thread_id} running slower than expected",
                         meta={"performance_impact": "medium"})
            
        # Simulate an error in some threads
        if thread_id % 3 == 0:
            raise ValueError(f"Simulated error in thread {thread_id}")
            
        logger.info(f"Work completed in thread {thread_id}")
        
    except Exception as e:
        # Log the exception with full stack trace
        logger.exception("Error during processing", 
                        exc_info=e,
                        extra={
                            "thread_id": thread_id,
                            "status": "failed"
                        })

def main():
    # Setup environment
    setup_environment()
    
    # Create first logger - uses tag from environment (env.worker)
    env_logger = create_logger(None)
    
    # Create second logger - uses explicit tag
    param_logger = create_logger("param.worker")
    
    # Log initial messages showing different tag sources
    env_logger.info("Starting logging with environment tag")
    param_logger.info("Starting logging with parameter tag")
    
    # Create multiple threads to demonstrate concurrent logging
    threads = []
    for i in range(5):
        # Alternate between loggers to demonstrate both
        logger = env_logger if i % 2 == 0 else param_logger
        thread = threading.Thread(
            target=simulate_work,
            args=(logger, i)
        )
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Log final status with both loggers
    env_logger.info("Environment tagged logger completed", 
                   meta={
                       "total_threads": len(threads) // 2,
                       "tag_source": "environment"
                   })
    
    param_logger.info("Parameter tagged logger completed",
                     meta={
                         "total_threads": len(threads) // 2,
                         "tag_source": "parameter"
                     })
    
    # Allow time for async logs to be processed
    time.sleep(1)

if __name__ == "__main__":
    main()
