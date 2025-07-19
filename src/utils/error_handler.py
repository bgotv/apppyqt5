"""
Sistema avançado de tratamento de erros e exceções.
"""

import sys
import traceback
import logging
from typing import Dict, Any, Optional, Callable
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QMessageBox, QApplication

from src.utils.logger import get_logger, log_user_action

logger = get_logger(__name__)

class ErrorHandler(QObject):
    """Sistema centralizado de tratamento de erros."""
    
    error_occurred = pyqtSignal(str, str, dict)  # component, error, details
    
    def __init__(self):
        """Inicializa o tratador de erros."""
        super().__init__()
        self.error_callbacks = {}
        
    def handle_error(self, component: str, error: Exception, 
                    details: Optional[Dict[str, Any]] = None,
                    show_user: bool = True):
        """
        Trata um erro de forma centralizada.
        
        Args:
            component: Nome do componente onde ocorreu o erro
            error: Exceção ocorrida
            details: Detalhes adicionais do erro
            show_user: Se deve mostrar erro ao usuário
        """
        error_details = details or {}
        error_message = str(error)
        
        # Log do erro
        logger.error(f"Erro em {component}: {error_message}", 
                    exc_info=True, extra=error_details)
        
        # Registra para auditoria
        log_user_action("error_occurred", {
            "component": component,
            "error_type": type(error).__name__,
            "error_message": error_message,
            "details": error_details
        }, result="error")
        
        # Emite sinal
        self.error_occurred.emit(component, error_message, error_details)
        
        # Mostra ao usuário se solicitado
        if show_user and QApplication.instance():
            self._show_error_to_user(component, error_message)
        
        # Executa callback específico se houver
        if component in self.error_callbacks:
            try:
                self.error_callbacks[component](error, error_details)
            except Exception as callback_error:
                logger.error(f"Erro no callback de {component}: {callback_error}")
    
    def register_error_callback(self, component: str, callback: Callable):
        """
        Registra callback para erros de um componente específico.
        
        Args:
            component: Nome do componente
            callback: Função callback a ser chamada
        """
        self.error_callbacks[component] = callback
    
    def _show_error_to_user(self, component: str, error_message: str):
        """
        Mostra erro ao usuário via QMessageBox.
        
        Args:
            component: Nome do componente
            error_message: Mensagem de erro
        """
        try:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Erro na Aplicação")
            msg.setText(f"Ocorreu um erro no componente '{component}'")
            msg.setDetailedText(error_message)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        except Exception as e:
            logger.error(f"Erro ao mostrar mensagem de erro: {e}")

def setup_exception_handling():
    """Configura tratamento global de exceções não capturadas."""
    
    def handle_exception(exc_type, exc_value, exc_traceback):
        """Handler para exceções não capturadas."""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logger.critical(f"Exceção não capturada: {error_msg}")
        
        # Registra para auditoria
        log_user_action("uncaught_exception", {
            "exception_type": exc_type.__name__,
            "exception_message": str(exc_value),
            "traceback": error_msg
        }, result="critical_error")
    
    sys.excepthook = handle_exception