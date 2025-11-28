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
        from src.dashboard.app import create_dashboard
        from src.common.rabbitmq_client import RabbitMQClient
        
        logger.info("=" * 50)
        logger.info("INICIANDO DASHBOARD VARP MONTE CARLO")
        logger.info("=" * 50)
        
        host = os.getenv('DASHBOARD_HOST', '0.0.0.0')
        port = int(os.getenv('DASHBOARD_PORT', '8050'))
        refresh_interval = int(os.getenv('DASHBOARD_REFRESH_INTERVAL', '2000'))
        debug = os.getenv('DASHBOARD_DEBUG', 'False').lower() == 'true'
        
        logger.info(f"Host: {host}, Port: {port}, Refresh: {refresh_interval}ms")
        
        logger.info("Conectando a RabbitMQ...")
        rabbitmq_client = RabbitMQClient()
        rabbitmq_client.connect()
        logger.info("✓ Conectado a RabbitMQ")
        
        logger.info("Creando dashboard...")
        dashboard = create_dashboard(
            rabbitmq_client=rabbitmq_client,
            update_interval=refresh_interval
        )
        
        logger.info("=" * 50)
        logger.info("✓ DASHBOARD INICIADO")
        logger.info(f"📊 URL: http://{host}:{port}")
        logger.info("=" * 50)
        
        dashboard.start(host=host, port=port, debug=debug)
        
    except Exception as e:
        logger.error(f"❌ ERROR: {e}", exc_info=True)
        sys.exit(1)
