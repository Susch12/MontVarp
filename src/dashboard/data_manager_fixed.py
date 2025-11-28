# Agregar este método justo después de __init__ en la clase DataManager

    def _ensure_connection(self):
        """Asegura que la conexión y canal estén activos."""
        try:
            # Verificar si necesitamos reconectar
            need_reconnect = False
            
            if self.client.connection is None or self.client.connection.is_closed:
                logger.warning("Conexión cerrada, reconectando...")
                need_reconnect = True
            elif self.client.channel is None or self.client.channel.is_closed:
                logger.warning("Canal cerrado, recreando...")
                need_reconnect = True
            
            if need_reconnect:
                try:
                    # Desconectar si hay algo abierto
                    if self.client.connection and not self.client.connection.is_closed:
                        try:
                            self.client.disconnect()
                        except:
                            pass
                    
                    # Reconectar
                    self.client.connect()
                    logger.info("Reconexión exitosa")
                    return True
                except Exception as e:
                    logger.error(f"Error reconectando: {e}")
                    return False
            
            return False
        except Exception as e:
            logger.error(f"Error en _ensure_connection: {e}")
            return False
