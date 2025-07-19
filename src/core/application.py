"""
Aplicação principal reestruturada com arquitetura modular aprimorada.
"""

import sys
import os
from typing import Dict, Any, List, Optional
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtCore import QTimer, pyqtSignal
import getpass

from src.config.settings import AppSettings, DatabaseSettings
from src.core.components import ComponentManager
from src.core.analysis_session_manager import session_manager
from src.core.decision_tree import DecisionTreeEngine
from src.core.flags_manager import FlagsManager
from src.core.note_manager import NoteManager
from src.core.report_generator import ReportGenerator
from src.database.database_manager import DatabaseManager
from src.automation.web_automation_manager import WebAutomationManager
from src.ui.main_window import ModernMainWindow
from src.utils.logger import get_logger, log_user_action
from src.utils.performance_tracker import performance_tracker, StageTracker
from src.utils.error_handler import ErrorHandler

logger = get_logger(__name__)

class GDAnalysisApp(QMainWindow):
    """
    Aplicação principal para análise de notas técnicas de GD.
    Versão reestruturada com melhor arquitetura e performance.
    """
    
    # Sinais da aplicação
    application_started = pyqtSignal()
    application_closing = pyqtSignal()
    component_error = pyqtSignal(str, str)  # component_name, error_message
    
    def __init__(self):
        """Inicializa a aplicação principal."""
        super().__init__()
        
        # Informações da sessão
        self.user_id = getpass.getuser()
        self.session_start_time = performance_tracker.session_start
        
        # Gerenciadores principais
        self.component_manager = ComponentManager()
        self.error_handler = ErrorHandler()
        self.database_manager = DatabaseManager()
        
        # Componentes de negócio
        self.flags_manager = None
        self.note_manager = None
        self.decision_tree = None
        self.report_generator = None
        self.web_automation = None
        
        # Interface do usuário
        self.main_window = None
        
        # Estado da aplicação
        self.is_initialized = False
        self.active_analysis = {}  # note_id -> StageTracker
        
        logger.info(f"Iniciando GDAnalysisApp para usuário: {self.user_id}")
        
        # Inicializa componentes
        self._initialize_components()
        
        # Configura interface
        self._setup_ui()
        
        # Conecta sinais
        self._connect_signals()
        
        # Registra inicialização
        log_user_action("application_initialized", {
            "user_id": self.user_id,
            "version": AppSettings.APP_VERSION
        })
        
        self.is_initialized = True
        self.application_started.emit()
    
    def _initialize_components(self):
        """Inicializa todos os componentes da aplicação."""
        with performance_tracker.track("initialize_components") as tracker:
            try:
                # Gerenciador de flags
                self.flags_manager = FlagsManager()
                self.component_manager.register_component("flags_manager", self.flags_manager)
                
                # Gerenciador de notas
                self.note_manager = NoteManager(self.database_manager)
                self.component_manager.register_component("note_manager", self.note_manager)
                
                # Árvore de decisão
                self.decision_tree = DecisionTreeEngine(self.flags_manager)
                self.component_manager.register_component("decision_tree", self.decision_tree)
                
                # Gerador de pareceres
                self.report_generator = ReportGenerator(self.flags_manager)
                self.component_manager.register_component("report_generator", self.report_generator)
                
                # Automação web
                self.web_automation = WebAutomationManager()
                self.component_manager.register_component("web_automation", self.web_automation)
                
                # Registra detalhes de performance
                tracker.add_detail("components_count", len(self.component_manager.get_components()))
                
                logger.info("Todos os componentes inicializados com sucesso")
                
            except Exception as e:
                logger.error(f"Erro ao inicializar componentes: {e}", exc_info=True)
                self.error_handler.handle_error("component_initialization", e)
                raise
    
    def _setup_ui(self):
        """Configura a interface do usuário."""
        with performance_tracker.track("setup_ui"):
            try:
                # Cria janela principal moderna
                self.main_window = ModernMainWindow(
                    flags_manager=self.flags_manager,
                    note_manager=self.note_manager,
                    decision_tree=self.decision_tree,
                    report_generator=self.report_generator,
                    web_automation=self.web_automation,
                    parent=self
                )
                
                # Configura janela principal
                self.setCentralWidget(self.main_window)
                self.setWindowTitle(f"{AppSettings.APP_NAME} v{AppSettings.APP_VERSION}")
                self.setMinimumSize(AppSettings.WINDOW_MIN_WIDTH, AppSettings.WINDOW_MIN_HEIGHT)
                
                # Registra componente UI
                self.component_manager.register_component("main_window", self.main_window)
                
                logger.info("Interface do usuário configurada")
                
            except Exception as e:
                logger.error(f"Erro ao configurar interface: {e}", exc_info=True)
                self.error_handler.handle_error("ui_setup", e)
                raise
    
    def _connect_signals(self):
        """Conecta sinais entre componentes."""
        try:
            # Sinais de erro
            self.error_handler.error_occurred.connect(self._on_error_occurred)
            
            # Sinais da árvore de decisão
            if hasattr(self.decision_tree, 'question_answered'):
                self.decision_tree.question_answered.connect(self._on_question_answered)
            
            if hasattr(self.decision_tree, 'analysis_completed'):
                self.decision_tree.analysis_completed.connect(self._on_analysis_completed)
            
            # Sinais do gerenciador de notas
            if hasattr(self.note_manager, 'note_loaded'):
                self.note_manager.note_loaded.connect(self._on_note_loaded)
            
            # Sinais de automação web
            if hasattr(self.web_automation, 'download_completed'):
                self.web_automation.download_completed.connect(self._on_download_completed)
            
            logger.info("Sinais conectados entre componentes")
            
        except Exception as e:
            logger.error(f"Erro ao conectar sinais: {e}", exc_info=True)
    
    def start_analysis(self, note_id: str) -> bool:
        """
        Inicia análise de uma nota técnica com sessão limpa.
        
        Args:
            note_id: ID da nota a ser analisada
            
        Returns:
            bool: True se a análise foi iniciada com sucesso
        """
        try:
            with performance_tracker.track(f"start_analysis_{note_id}") as tracker:
                # 🔥 NOVA FUNCIONALIDADE: Garante sessão limpa
                session = session_manager.ensure_clean_session(note_id, self.user_id)
                
                # Verifica se já existe análise ativa para esta nota
                if note_id in self.active_analysis:
                    logger.warning(f"Análise já ativa para nota {note_id} - limpando estado anterior")
                    # Remove análise anterior para evitar contaminação
                    del self.active_analysis[note_id]
                
                # Cria rastreador de etapas
                stage_tracker = StageTracker(note_id, self.user_id)
                self.active_analysis[note_id] = stage_tracker
                
                # Inicia primeira etapa
                stage_tracker.start_stage("loading_note")
                
                # Carrega dados da nota
                note_data = self.note_manager.load_note(note_id)
                if not note_data:
                    logger.error(f"Não foi possível carregar nota {note_id}")
                    session_manager.abort_current_session("note_load_failed")
                    return False
                
                # 🔥 Atualiza dados na sessão
                session_manager.update_session_data(note_data=note_data)
                
                stage_tracker.end_stage("loading_note")
                
                # Registra início da análise
                log_user_action("analysis_started", {
                    "note_id": note_id,
                    "session_id": session.session_id,
                    "note_data_keys": list(note_data.keys()) if note_data else [],
                    "session_cleaned": True
                }, note_id=note_id)
                
                tracker.add_detail("note_loaded", True)
                tracker.add_detail("note_data_size", len(note_data) if note_data else 0)
                tracker.add_detail("session_id", session.session_id)
                
                logger.info(f"Análise iniciada para nota {note_id} com sessão limpa {session.session_id}")
                return True
                
        except Exception as e:
            logger.error(f"Erro ao iniciar análise da nota {note_id}: {e}", exc_info=True)
            session_manager.abort_current_session("error_during_start")
            self.error_handler.handle_error("analysis_start", e, {"note_id": note_id})
            return False
    
    def complete_analysis(self, note_id: str) -> bool:
        """
        Completa análise de uma nota técnica e limpa a sessão.
        
        Args:
            note_id: ID da nota analisada
            
        Returns:
            bool: True se a análise foi completada com sucesso
        """
        try:
            if note_id not in self.active_analysis:
                logger.warning(f"Nenhuma análise ativa encontrada para nota {note_id}")
                return False
            
            # Obtém rastreador de etapas
            stage_tracker = self.active_analysis[note_id]
            
            # Finaliza etapa atual se houver
            if stage_tracker.current_stage:
                stage_tracker.end_stage(stage_tracker.current_stage)
            
            # Exporta dados das etapas
            stages_data = stage_tracker.export_stages()
            
            # 🔥 Completa a sessão no gerenciador
            current_session = session_manager.get_current_session()
            if current_session and current_session.note_id == note_id:
                session_manager.complete_analysis()
            
            # Remove da lista ativa
            del self.active_analysis[note_id]
            
            # Registra conclusão
            log_user_action("analysis_completed", {
                "note_id": note_id,
                "session_id": current_session.session_id if current_session else None,
                "total_time": stages_data["total_time"],
                "stage_count": stages_data["stage_count"],
                "stages": list(stages_data["stages"].keys())
            }, note_id=note_id)
            
            logger.info(f"Análise completada para nota {note_id} em {stages_data['total_time']:.2f}s")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao completar análise da nota {note_id}: {e}", exc_info=True)
            session_manager.abort_current_session("error_during_completion")
            self.error_handler.handle_error("analysis_complete", e, {"note_id": note_id})
            return False
    
    def get_active_analyses(self) -> List[str]:
        """
        Retorna lista de análises ativas.
        
        Returns:
            Lista de IDs de notas com análise ativa
        """
        return list(self.active_analysis.keys())
    
    def get_analysis_status(self, note_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém status de uma análise.
        
        Args:
            note_id: ID da nota
            
        Returns:
            Dicionário com status da análise ou None se não encontrada
        """
        if note_id not in self.active_analysis:
            return None
        
        stage_tracker = self.active_analysis[note_id]
        return {
            "note_id": note_id,
            "user_id": stage_tracker.user_id,
            "current_stage": stage_tracker.current_stage,
            "completed_stages": list(stage_tracker.stages.keys()),
            "total_time": stage_tracker.get_total_time(),
            "stage_count": len(stage_tracker.stages)
        }
    
    def get_components(self) -> Dict[str, Any]:
        """
        Retorna dicionário com todos os componentes registrados.
        
        Returns:
            Dicionário com componentes da aplicação
        """
        return self.component_manager.get_components()
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        Gera relatório de performance da aplicação.
        
        Returns:
            Relatório de performance
        """
        report = performance_tracker.generate_report()
        
        # Adiciona informações específicas da aplicação
        report["application"] = {
            "user_id": self.user_id,
            "session_duration": performance_tracker.session_start,
            "active_analyses": len(self.active_analysis),
            "components_count": len(self.component_manager.get_components()),
            "is_initialized": self.is_initialized
        }
        
        return report
    
    def export_performance_data(self, format: str = "parquet") -> str:
        """
        Exporta dados de performance.
        
        Args:
            format: Formato de exportação ("json" ou "parquet")
            
        Returns:
            Caminho do arquivo exportado
        """
        try:
            if format.lower() == "json":
                filepath = performance_tracker.export_to_json()
            else:
                filepath = performance_tracker.export_to_parquet()
            
            log_user_action("performance_exported", {
                "format": format,
                "filepath": str(filepath)
            })
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Erro ao exportar dados de performance: {e}", exc_info=True)
            return ""
    
    # Slots para sinais
    def _on_error_occurred(self, component: str, error: str, details: Dict[str, Any]):
        """Handler para erros de componentes."""
        logger.error(f"Erro em {component}: {error}", extra=details)
        self.component_error.emit(component, error)
    
    def _on_question_answered(self, question_id: str, answer: str, note_id: str):
        """Handler para resposta de pergunta na árvore de decisão."""
        # Registra resposta
        log_user_action("question_answered", {
            "question_id": question_id,
            "answer": answer
        }, note_id=note_id)
        
        # Atualiza etapa se houver análise ativa
        if note_id in self.active_analysis:
            stage_tracker = self.active_analysis[note_id]
            if stage_tracker.current_stage:
                stage_tracker.end_stage(stage_tracker.current_stage)
            stage_tracker.start_stage(f"question_{question_id}")
    
    def _on_analysis_completed(self, note_id: str):
        """Handler para conclusão de análise."""
        self.complete_analysis(note_id)
    
    def _on_note_loaded(self, note_id: str, note_data: Dict[str, Any]):
        """Handler para carregamento de nota."""
        logger.info(f"Nota {note_id} carregada com {len(note_data)} campos")
    
    def _on_download_completed(self, note_id: str, success: bool, files: List[str]):
        """Handler para conclusão de download."""
        log_user_action("download_completed", {
            "success": success,
            "files_count": len(files) if files else 0,
            "files": files[:10] if files else []  # Limita a 10 arquivos no log
        }, note_id=note_id)
    
    def closeEvent(self, event):
        """Handler para fechamento da aplicação."""
        try:
            # Emite sinal de fechamento
            self.application_closing.emit()
            
            # Completa análises ativas
            active_notes = list(self.active_analysis.keys())
            for note_id in active_notes:
                self.complete_analysis(note_id)
            
            # Exporta dados de performance
            if performance_tracker.enabled:
                self.export_performance_data("parquet")
            
            # Desbloqueia notas se houver gerenciador de bloqueio
            if hasattr(self.note_manager, 'unlock_all_user_notes'):
                unlocked_count = self.note_manager.unlock_all_user_notes(self.user_id)
                logger.info(f"Desbloqueadas {unlocked_count} notas do usuário {self.user_id}")
            
            # Registra encerramento
            session_duration = performance_tracker.session_start
            log_user_action("application_closed", {
                "session_duration": session_duration,
                "active_analyses_completed": len(active_notes)
            })
            
            logger.info(f"Aplicação encerrada após {session_duration:.2f}s")
            
        except Exception as e:
            logger.error(f"Erro durante fechamento da aplicação: {e}", exc_info=True)
        finally:
            event.accept()
    
    def show(self):
        """Exibe a janela principal."""
        super().show()
        
        # Timer para atualização periódica de performance
        self.performance_timer = QTimer()
        self.performance_timer.timeout.connect(self._update_performance_metrics)
        self.performance_timer.start(60000)  # A cada minuto
    
    def _update_performance_metrics(self):
        """Atualiza métricas de performance periodicamente."""
        try:
            # Exporta métricas se necessário
            if len(performance_tracker.metrics) > 1000:  # Exporta quando há muitas métricas
                self.export_performance_data("parquet")
                performance_tracker.clear_metrics()
                
        except Exception as e:
            logger.error(f"Erro ao atualizar métricas: {e}")

def create_application() -> GDAnalysisApp:
    """
    Cria e configura a aplicação principal.
    
    Returns:
        Instância da aplicação configurada
    """
    try:
        app = GDAnalysisApp()
        
        # Configurações adicionais
        app.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
        """)
        
        return app
        
    except Exception as e:
        logger.critical(f"Erro crítico ao criar aplicação: {e}", exc_info=True)
        raise