"""
Gerenciador de componentes da aplicação.
"""

from typing import Dict, Any, Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)

class ComponentManager:
    """Gerencia componentes da aplicação de forma centralizada."""
    
    def __init__(self):
        """Inicializa o gerenciador de componentes."""
        self._components: Dict[str, Any] = {}
        logger.info("ComponentManager inicializado")
    
    def register_component(self, name: str, component: Any) -> bool:
        """
        Registra um componente.
        
        Args:
            name: Nome do componente
            component: Instância do componente
            
        Returns:
            bool: True se registrado com sucesso
        """
        try:
            self._components[name] = component
            logger.info(f"Componente '{name}' registrado: {type(component).__name__}")
            return True
        except Exception as e:
            logger.error(f"Erro ao registrar componente '{name}': {e}")
            return False
    
    def get_component(self, name: str) -> Optional[Any]:
        """
        Obtém um componente pelo nome.
        
        Args:
            name: Nome do componente
            
        Returns:
            Instância do componente ou None
        """
        return self._components.get(name)
    
    def get_components(self) -> Dict[str, Any]:
        """
        Retorna todos os componentes registrados.
        
        Returns:
            Dicionário com todos os componentes
        """
        return self._components.copy()
    
    def unregister_component(self, name: str) -> bool:
        """
        Remove um componente.
        
        Args:
            name: Nome do componente
            
        Returns:
            bool: True se removido com sucesso
        """
        if name in self._components:
            del self._components[name]
            logger.info(f"Componente '{name}' removido")
            return True
        return False
    
    def list_components(self) -> list:
        """
        Lista nomes de todos os componentes.
        
        Returns:
            Lista de nomes dos componentes
        """
        return list(self._components.keys())