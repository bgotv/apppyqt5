#!/usr/bin/env python3
"""
Aplicativo de Análise de Notas Técnicas de Geração Distribuída (GD)
Versão Reestruturada e Aprimorada

Autor: Bruno Gobbi
Versão: 2.0.0
"""

import sys
import os
import logging
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont

# Adiciona o diretório do projeto ao path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import AppSettings
from src.core.application import GDAnalysisApp
from src.utils.logger import setup_logging, get_logger
from src.utils.performance_tracker import PerformanceTracker
from src.utils.error_handler import setup_exception_handling

# Configuração de logging
setup_logging()
logger = get_logger(__name__)

def create_splash_screen():
    """Cria a tela de splash da aplicação."""
    splash_pixmap = QPixmap(400, 300)
    splash_pixmap.fill(Qt.white)
    
    splash = QSplashScreen(splash_pixmap)
    splash.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.SplashScreen)
    
    # Adiciona texto à tela de splash
    splash.showMessage(
        "Carregando Análise GD v2.0.0...\nPor favor aguarde.",
        Qt.AlignCenter | Qt.AlignBottom,
        Qt.black
    )
    
    return splash

def main():
    """Função principal da aplicação."""
    # Inicia medição de performance da inicialização
    with PerformanceTracker("application_startup") as tracker:
        try:
            # Configura tratamento de exceções
            setup_exception_handling()
            
            # Cria aplicação Qt
            app = QApplication(sys.argv)
            app.setApplicationName(AppSettings.APP_NAME)
            app.setApplicationVersion(AppSettings.APP_VERSION)
            app.setOrganizationName("CPFL Energia")
            app.setOrganizationDomain("cpfl.com.br")
            
            # Define estilo da aplicação
            app.setStyle(AppSettings.UI_STYLE)
            
            # Cria e exibe splash screen
            splash = create_splash_screen()
            splash.show()
            app.processEvents()
            
            logger.info(f"Iniciando {AppSettings.APP_NAME} v{AppSettings.APP_VERSION}")
            
            # Simula tempo de carregamento
            QTimer.singleShot(1500, splash.close)
            
            # Cria aplicação principal
            main_app = GDAnalysisApp()
            
            # Registra detalhes de performance
            tracker.add_detail("components_loaded", len(main_app.get_components()))
            tracker.add_detail("modules_count", len(sys.modules))
            
            # Exibe janela principal
            main_app.show()
            splash.finish(main_app)
            
            logger.info("Aplicação iniciada com sucesso")
            
            # Executa aplicação
            exit_code = app.exec_()
            
            logger.info(f"Aplicação finalizada com código: {exit_code}")
            return exit_code
            
        except Exception as e:
            logger.critical(f"Erro crítico durante inicialização: {e}", exc_info=True)
            return 1

if __name__ == "__main__":
    sys.exit(main())