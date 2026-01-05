"""
CDC Consumer Worker

This is a standalone worker process that consumes CDC events from Redis
and pushes changes to SharePoint.

Entry point: python -m app.worker.cdc_consumer_worker
"""

import logging
import signal
import sys

from app.db.session import SessionLocal
from app.services.cdc_consumer import CDCConsumer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for CDC consumer worker."""
    logger.info("Starting CDC Consumer Worker...")

    # Create database session
    db = SessionLocal()

    # Create consumer
    consumer = CDCConsumer(db)

    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        # Consumer run loop should handle KeyboardInterrupt
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Run consumer (blocking loop)
        consumer.run()
    except KeyboardInterrupt:
        logger.info("CDC Consumer Worker stopped by user")
    except Exception as e:
        logger.error(f"CDC Consumer Worker failed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        db.close()
        logger.info("CDC Consumer Worker shutdown complete")


if __name__ == "__main__":
    main()
