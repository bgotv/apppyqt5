"""
Módulo principal da aplicação com as correções solicitadas.
"""
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from app.config import settings
from app.ui import MainWindow
from app.core.flags_manager import FlagsManager
from app.core.note_lock_manager import NoteLockManager
from app.core.decision_tree import DecisionTree
from app.core.report_generator import ReportGenerator
from app.ui.web_automation_manager import WebAutomationManager
from app.ui.notes_lock_view import NotesTreeView, NotesLockPanel
from app.utils.logger import log_action


def main():
    """Função principal da aplicação."""
    # Registra o início da aplicação
    log_action('application_start', {
        'version': settings.APP_VERSION
    })
    
    # Configura o Oracle Client
    lib_path = settings.configure_oracle_client()
    
    # Cria a aplicação Qt
    app = QApplication(sys.argv)
    app.setStyle(settings.APP_STYLE)
    
    # Cria os componentes principais
    flags_manager = FlagsManager()
    lock_manager = NoteLockManager()
    decision_tree = DecisionTree(flags_manager)
    report_generator = ReportGenerator(flags_manager)
    web_automation = WebAutomationManager()
    
    # Cria e exibe a janela principal
    main_window = MainWindow(
        flags_manager=flags_manager,
        lock_manager=lock_manager,
        decision_tree=decision_tree,
        report_generator=report_generator,
        web_automation=web_automation
    )
    main_window.show()
    
    # Executa a aplicação
    exit_code = app.exec_()
    
    # Desbloqueia todas as notas do usuário atual ao sair
    lock_manager.unlock_all_my_notes()
    
    # Registra o encerramento da aplicação
    log_action('application_exit', {
        'exit_code': exit_code
    })
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
