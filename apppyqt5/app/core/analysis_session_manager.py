"""
Gerenciador de Sessão de Análise - Previne contaminação de dados entre análises.
Solução para o problema de dados remanescentes de análises anteriores.
"""

from typing import Dict, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import threading
import uuid

from app.utils.logger import log_action
# from app.utils.performance import measure_performance

logger = get_logger(__name__)

@dataclass
class AnalysisSession:
    """Representa uma sessão de análise de nota técnica."""
    
    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    note_id: str = ""
    user_id: str = ""
    start_time: float = field(default_factory=lambda: datetime.now().timestamp())
    
    # Dados da sessão
    note_data: Dict[str, Any] = field(default_factory=dict)
    uc_data: Dict[str, Any] = field(default_factory=dict)
    valores_site: Dict[str, Any] = field(default_factory=dict)
    downloads_folder: str = ""
    
    # Estado da árvore de decisão
    decision_history: Dict[str, str] = field(default_factory=dict)
    active_flags: Dict[str, Any] = field(default_factory=dict)
    current_question: Optional[str] = None
    
    # Estado da análise
    is_active: bool = True
    is_completed: bool = False
    analysis_stage: str = "initialized"
    
    def clear_all_data(self):
        """Limpa todos os dados da sessão."""
        self.note_data.clear()
        self.uc_data.clear()
        self.valores_site.clear()
        self.downloads_folder = ""
        self.decision_history.clear()
        self.active_flags.clear()
        self.current_question = None
        self.analysis_stage = "cleared"
        
        logger.info(f"Sessão {self.session_id} limpa completamente")

class AnalysisSessionManager:
    """
    Gerenciador de sessões de análise.
    Previne contaminação de dados entre diferentes análises.
    """
    
    def __init__(self):
        """Inicializa o gerenciador de sessões."""
        self._current_session: Optional[AnalysisSession] = None
        self._session_history: Dict[str, AnalysisSession] = {}
        self._lock = threading.Lock()
        
        logger.info("AnalysisSessionManager inicializado")
    
    def start_new_session(self, note_id: str, user_id: str, 
                         force_new: bool = True) -> AnalysisSession:
        """
        Inicia uma nova sessão de análise.
        
        Args:
            note_id: ID da nota a ser analisada
            user_id: ID do usuário
            force_new: Se deve forçar nova sessão mesmo se já existe uma ativa
            
        Returns:
            Nova sessão de análise
        """
        with self._lock:
            # Finaliza sessão atual se existir
            if self._current_session and (force_new or self._current_session.note_id != note_id):
                self._finalize_current_session(reason="new_session_started")
            
            # Cria nova sessão
            new_session = AnalysisSession(
                note_id=note_id,
                user_id=user_id
            )
            
            # Define como sessão atual
            self._current_session = new_session
            self._session_history[new_session.session_id] = new_session
            
            # Log da ação
            log_action("analysis_session_started", {
                "session_id": new_session.session_id,
                "note_id": note_id,
                "previous_session_cleared": force_new
            }, note_id=note_id)
            
            logger.info(f"Nova sessão iniciada: {new_session.session_id} para nota {note_id}")
            
            return new_session
    
    def get_current_session(self) -> Optional[AnalysisSession]:
        """
        Obtém a sessão atual.
        
        Returns:
            Sessão atual ou None se não houver
        """
        return self._current_session
    
    def ensure_clean_session(self, note_id: str, user_id: str) -> AnalysisSession:
        """
        Garante que existe uma sessão limpa para a nota especificada.
        
        Args:
            note_id: ID da nota
            user_id: ID do usuário
            
        Returns:
            Sessão limpa e pronta para uso
        """
        with self._lock:
            current = self._current_session
            
            # Se não há sessão atual ou é para nota diferente, cria nova
            if not current or current.note_id != note_id:
                return self.start_new_session(note_id, user_id, force_new=True)
            
            # Se é para a mesma nota, limpa dados contaminados
            if current.note_id == note_id:
                # Verifica se há dados de análise anterior que podem contaminar
                if current.decision_history or current.active_flags:
                    logger.warning(f"Dados remanescentes detectados na sessão {current.session_id}")
                    
                    # Limpa dados contaminados
                    current.clear_all_data()
                    current.analysis_stage = "reset"
                    
                    log_action("session_data_cleared", {
                        "session_id": current.session_id,
                        "note_id": note_id,
                        "reason": "contamination_prevention"
                    }, note_id=note_id)
            
            return current
    
    def update_session_data(self, note_data: Dict[str, Any] = None,
                          uc_data: Dict[str, Any] = None,
                          valores_site: Dict[str, Any] = None,
                          downloads_folder: str = None):
        """
        Atualiza dados da sessão atual.
        
        Args:
            note_data: Dados da nota
            uc_data: Dados da UC
            valores_site: Valores extraídos do site
            downloads_folder: Pasta de downloads
        """
        if not self._current_session:
            logger.warning("Tentativa de atualizar dados sem sessão ativa")
            return
        
        session = self._current_session
        
        if note_data:
            session.note_data.update(note_data)
        
        if uc_data:
            session.uc_data.update(uc_data)
        
        if valores_site:
            session.valores_site.update(valores_site)
        
        if downloads_folder:
            session.downloads_folder = downloads_folder
        
        session.analysis_stage = "data_loaded"
        
        logger.debug(f"Dados atualizados na sessão {session.session_id}")
    
    def update_decision_state(self, question_id: str, answer: str, 
                            flags_activated: Dict[str, Any] = None):
        """
        Atualiza estado da árvore de decisão.
        
        Args:
            question_id: ID da pergunta
            answer: Resposta selecionada
            flags_activated: Flags ativadas
        """
        if not self._current_session:
            logger.warning("Tentativa de atualizar decisão sem sessão ativa")
            return
        
        session = self._current_session
        session.decision_history[question_id] = answer
        session.current_question = question_id
        
        if flags_activated:
            session.active_flags.update(flags_activated)
        
        session.analysis_stage = "in_progress"
        
        logger.debug(f"Estado de decisão atualizado: {question_id} = {answer}")
    
    def complete_analysis(self, final_flags: Dict[str, Any] = None) -> bool:
        """
        Marca a análise como concluída.
        
        Args:
            final_flags: Flags finais da análise
            
        Returns:
            True se concluída com sucesso
        """
        if not self._current_session:
            logger.warning("Tentativa de completar análise sem sessão ativa")
            return False
        
        session = self._current_session
        session.is_completed = True
        session.analysis_stage = "completed"
        
        if final_flags:
            session.active_flags.update(final_flags)
        
        # Log da conclusão
        log_action("analysis_session_completed", {
            "session_id": session.session_id,
            "note_id": session.note_id,
            "questions_answered": len(session.decision_history),
            "flags_activated": len(session.active_flags),
            "duration": datetime.now().timestamp() - session.start_time
        }, note_id=session.note_id)
        
        logger.info(f"Análise concluída: sessão {session.session_id}")
        return True
    
    def abort_current_session(self, reason: str = "user_aborted"):
        """
        Aborta a sessão atual.
        
        Args:
            reason: Motivo do abort
        """
        if self._current_session:
            self._finalize_current_session(reason=reason)
    
    def _finalize_current_session(self, reason: str = "finalized"):
        """
        Finaliza a sessão atual.
        
        Args:
            reason: Motivo da finalização
        """
        if not self._current_session:
            return
        
        session = self._current_session
        session.is_active = False
        
        # Log da finalização
        log_action("analysis_session_finalized", {
            "session_id": session.session_id,
            "note_id": session.note_id,
            "reason": reason,
            "was_completed": session.is_completed,
            "duration": datetime.now().timestamp() - session.start_time
        }, note_id=session.note_id)
        
        logger.info(f"Sessão finalizada: {session.session_id} (motivo: {reason})")
        
        # Remove referência da sessão atual
        self._current_session = None
    
    def get_session_summary(self) -> Dict[str, Any]:
        """
        Obtém resumo da sessão atual.
        
        Returns:
            Resumo da sessão
        """
        if not self._current_session:
            return {"error": "Nenhuma sessão ativa"}
        
        session = self._current_session
        return {
            "session_id": session.session_id,
            "note_id": session.note_id,
            "user_id": session.user_id,
            "analysis_stage": session.analysis_stage,
            "is_active": session.is_active,
            "is_completed": session.is_completed,
            "questions_answered": len(session.decision_history),
            "flags_count": len(session.active_flags),
            "has_note_data": bool(session.note_data),
            "has_uc_data": bool(session.uc_data),
            "has_downloads": bool(session.downloads_folder),
            "duration": datetime.now().timestamp() - session.start_time
        }
    
    def validate_session_integrity(self) -> Dict[str, Any]:
        """
        Valida integridade da sessão atual.
        
        Returns:
            Relatório de validação
        """
        if not self._current_session:
            return {
                "valid": False,
                "issues": ["Nenhuma sessão ativa"],
                "recommendations": ["Inicie uma nova sessão"]
            }
        
        session = self._current_session
        issues = []
        recommendations = []
        
        # Verifica contaminação de dados
        if session.analysis_stage == "initialized" and (session.decision_history or session.active_flags):
            issues.append("Dados de análise anterior detectados em sessão nova")
            recommendations.append("Execute clear_all_data() na sessão")
        
        # Verifica consistência de dados
        if session.note_data and not session.note_data.get("NR_ATIVIDADE"):
            issues.append("Dados de nota incompletos")
            recommendations.append("Recarregue os dados da nota")
        
        # Verifica estado de análise
        if session.analysis_stage == "in_progress" and not session.current_question:
            issues.append("Análise em progresso mas sem pergunta atual")
            recommendations.append("Reinicie a árvore de decisão")
        
        return {
            "valid": len(issues) == 0,
            "session_id": session.session_id,
            "issues": issues,
            "recommendations": recommendations,
            "summary": self.get_session_summary()
        }

# Instância global do gerenciador
session_manager = AnalysisSessionManager()