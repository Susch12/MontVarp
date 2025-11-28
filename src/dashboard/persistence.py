"""
Sistema de persistencia para guardar y cargar simulaciones.
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import deque

logger = logging.getLogger(__name__)

class PersistenceManager:
    """Gestiona el guardado y carga de simulaciones."""
    
    def __init__(self, storage_dir: str = "/app/data/simulaciones"):
        """
        Inicializa el gestor de persistencia.
        
        Args:
            storage_dir: Directorio donde guardar las simulaciones (ruta absoluta)
        """
        self.storage_dir = Path(storage_dir)
        
        # Crear directorio si no existe
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directorio de persistencia: {self.storage_dir}")
        except Exception as e:
            logger.error(f"Error creando directorio de persistencia: {e}")
            raise
    
    def save_simulation(self, data_manager) -> Optional[Path]:
        """
        Guarda la simulación actual.
        
        Args:
            data_manager: Instancia de DataManager con los datos
            
        Returns:
            Path del archivo guardado o None si error
        """
        try:
            if len(data_manager.resultados) == 0:
                logger.warning("No hay resultados para guardar")
                return None
            
            # Generar nombre de archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            modelo_nombre = data_manager.modelo_info.get('nombre', 'desconocido')
            filename = f"{timestamp}_{modelo_nombre}.json"
            filepath = self.storage_dir / filename
            
            # Preparar datos
            data = {
                'metadata': {
                    'fecha': datetime.now().isoformat(),
                    'timestamp': timestamp,
                    'modelo': data_manager.modelo_info,
                    'num_resultados': len(data_manager.resultados)
                },
                'estadisticas': data_manager.estadisticas,
                'tests_normalidad': data_manager.tests_normalidad,
                'convergencia': list(data_manager.historico_convergencia),
                'resultados': list(data_manager.resultados),
                'stats_productor': data_manager.stats_productor,
                'stats_consumidores': data_manager.stats_consumidores
            }
            
            # Guardar
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Simulación guardada: {filepath} ({len(data_manager.resultados)} resultados)")
            return filepath
            
        except Exception as e:
            logger.error(f"Error guardando simulación: {e}", exc_info=True)
            return None
    
    def load_simulation(self, filename: str) -> Optional[Dict]:
        """
        Carga una simulación guardada.
        
        Args:
            filename: Nombre del archivo o path completo
            
        Returns:
            Diccionario con los datos o None si error
        """
        try:
            # Determinar path
            filepath = Path(filename)
            if not filepath.is_absolute():
                filepath = self.storage_dir / filename
            
            if not filepath.exists():
                logger.warning(f"Archivo no encontrado: {filepath}")
                return None
            
            # Cargar
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            logger.info(f"Simulación cargada: {filepath}")
            return data
            
        except Exception as e:
            logger.error(f"Error cargando simulación: {e}", exc_info=True)
            return None
    
    def list_simulations(self) -> List[Dict[str, Any]]:
        """
        Lista todas las simulaciones guardadas.
        
        Returns:
            Lista de diccionarios con info de cada simulación
        """
        simulations = []
        
        try:
            if not self.storage_dir.exists():
                return simulations
            
            for filepath in sorted(self.storage_dir.glob("*.json"), reverse=True):
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    
                    metadata = data.get('metadata', {})
                    simulations.append({
                        'filename': filepath.name,
                        'filepath': str(filepath),
                        'fecha': metadata.get('fecha', 'desconocida'),
                        'modelo_nombre': metadata.get('modelo', {}).get('nombre', 'desconocido'),
                        'num_resultados': metadata.get('num_resultados', 0),
                        'size_mb': filepath.stat().st_size / (1024 * 1024)
                    })
                except Exception as e:
                    logger.warning(f"Error leyendo {filepath.name}: {e}")
                    continue
            
            logger.info(f"Encontradas {len(simulations)} simulaciones")
            
        except Exception as e:
            logger.error(f"Error listando simulaciones: {e}", exc_info=True)
        
        return simulations
    
    def get_latest_simulation(self) -> Optional[Dict]:
        """
        Obtiene la última simulación guardada.
        
        Returns:
            Diccionario con los datos o None si no hay simulaciones
        """
        simulations = self.list_simulations()
        if not simulations:
            return None
        
        latest_file = simulations[0]['filename']
        return self.load_simulation(latest_file)
    
    def delete_simulation(self, filename: str) -> bool:
        """
        Elimina una simulación guardada.
        
        Args:
            filename: Nombre del archivo a eliminar
            
        Returns:
            True si se eliminó correctamente
        """
        try:
            filepath = self.storage_dir / filename
            if filepath.exists():
                filepath.unlink()
                logger.info(f"Simulación eliminada: {filename}")
                return True
            else:
                logger.warning(f"Archivo no encontrado: {filename}")
                return False
        except Exception as e:
            logger.error(f"Error eliminando simulación: {e}", exc_info=True)
            return False
