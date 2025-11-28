#!/usr/bin/env python3
import sys
import os
import logging

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        modelo_file = os.getenv('MODELO_FILE', 'modelos/ejemplo_simple.ini')
        num_escenarios = int(os.getenv('DEFAULT_NUM_ESCENARIOS', '1000'))
        
        logger.info("=" * 50)
        logger.info("INICIANDO PRODUCER VARP")
        logger.info(f"Modelo: {modelo_file}")
        logger.info(f"Escenarios: {num_escenarios}")
        logger.info("=" * 50)
        
        if not os.path.exists(modelo_file):
            logger.error(f"❌ Modelo no encontrado: {modelo_file}")
            sys.exit(1)
        
        from src.producer.producer import run_producer
        
        logger.info("Ejecutando producer...")
        run_producer(modelo_file, num_escenarios)
        
        logger.info("=" * 50)
        logger.info("✓ PRODUCER COMPLETADO")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"❌ ERROR: {e}", exc_info=True)
        sys.exit(1)
