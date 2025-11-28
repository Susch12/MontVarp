#!/usr/bin/env python3
import sys
import logging
import uuid

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        consumer_id = f"C-{uuid.uuid4().hex[:8]}"
        
        logger.info("=" * 50)
        logger.info(f"INICIANDO CONSUMER: {consumer_id}")
        logger.info("=" * 50)
        
        from src.consumer.consumer import run_consumer
        
        logger.info(f"Consumer {consumer_id} listo...")
        run_consumer(consumer_id)
        
        logger.info(f"✓ CONSUMER {consumer_id} FINALIZADO")
        
    except Exception as e:
        logger.error(f"❌ ERROR: {e}", exc_info=True)
        sys.exit(1)
