"""
Sistema avançado de logging e auditoria para a aplicação.
Inclui logs estruturados, auditoria detalhada e análise de ações.
"""

import logging
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import threading
from dataclasses import dataclass, asdict
import getpass
from enum import Enum

from src.config.settings import AppSettings

class LogLevel(Enum):
    """Níveis de log personalizados."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    AUDIT = "AUDIT"  # Nível especial para auditoria

@dataclass
class AuditEntry:
    """Entrada de auditoria estruturada."""
    timestamp: float
    user_id: str
    action: str
    details: Dict[str, Any]
    session_id: Optional[str] = None
    note_id: Optional[str] = None
    result: Optional[str] = None
    duration: Optional[float] = None
    
    def __post_init__(self):
        """Inicializa campos calculados."""
        if not self.user_id:
            self.user_id = getpass.getuser()
        
        if not self.session_id:
            self.session_id = threading.current_thread().name

class AuditLogger:
    """Logger especializado para auditoria de ações."""
    
    def __init__(self):
        """Inicializa o logger de auditoria."""
        self.audit_file = AppSettings.LOGS_DIR / "audit.jsonl"
        self.session_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.getpid()}"
        self.user_id = getpass.getuser()
        self._lock = threading.Lock()
        
        # Garante que o diretório existe
        self.audit_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log_action(self, action: str, details: Optional[Dict[str, Any]] = None, 
                   note_id: Optional[str] = None, result: Optional[str] = None,
                   duration: Optional[float] = None):
        """
        Registra uma ação de auditoria.
        
        Args:
            action: Nome da ação executada
            details: Detalhes adicionais da ação
            note_id: ID da nota relacionada (opcional)
            result: Resultado da ação (opcional)
            duration: Duração da ação em segundos (opcional)
        """
        entry = AuditEntry(
            timestamp=time.time(),
            user_id=self.user_id,
            action=action,
            details=details or {},
            session_id=self.session_id,
            note_id=note_id,
            result=result,
            duration=duration
        )
        
        with self._lock:
            with open(self.audit_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(asdict(entry), default=str) + '\n')
    
    def get_user_actions(self, user_id: Optional[str] = None, 
                        start_time: Optional[float] = None,
                        end_time: Optional[float] = None) -> List[AuditEntry]:
        """
        Obtém ações de um usuário específico.
        
        Args:
            user_id: ID do usuário (padrão: usuário atual)
            start_time: Timestamp de início (opcional)
            end_time: Timestamp de fim (opcional)
            
        Returns:
            Lista de entradas de auditoria
        """
        if not self.audit_file.exists():
            return []
        
        user_id = user_id or self.user_id
        entries = []
        
        with open(self.audit_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    entry = AuditEntry(**data)
                    
                    # Filtros
                    if entry.user_id != user_id:
                        continue
                    
                    if start_time and entry.timestamp < start_time:
                        continue
                    
                    if end_time and entry.timestamp > end_time:
                        continue
                    
                    entries.append(entry)
                    
                except (json.JSONDecodeError, TypeError):
                    continue
        
        return entries
    
    def get_note_history(self, note_id: str) -> List[AuditEntry]:
        """
        Obtém histórico completo de uma nota.
        
        Args:
            note_id: ID da nota
            
        Returns:
            Lista de entradas de auditoria para a nota
        """
        if not self.audit_file.exists():
            return []
        
        entries = []
        
        with open(self.audit_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    entry = AuditEntry(**data)
                    
                    if entry.note_id == note_id:
                        entries.append(entry)
                        
                except (json.JSONDecodeError, TypeError):
                    continue
        
        return sorted(entries, key=lambda x: x.timestamp)
    
    def generate_report(self, start_time: Optional[float] = None,
                       end_time: Optional[float] = None) -> Dict[str, Any]:
        """
        Gera relatório de auditoria.
        
        Args:
            start_time: Timestamp de início (opcional)
            end_time: Timestamp de fim (opcional)
            
        Returns:
            Relatório de auditoria
        """
        if not self.audit_file.exists():
            return {"error": "Arquivo de auditoria não encontrado"}
        
        entries = []
        users = set()
        actions = {}
        notes_analyzed = set()
        
        with open(self.audit_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    entry = AuditEntry(**data)
                    
                    # Filtros de tempo
                    if start_time and entry.timestamp < start_time:
                        continue
                    if end_time and entry.timestamp > end_time:
                        continue
                    
                    entries.append(entry)
                    users.add(entry.user_id)
                    
                    # Conta ações
                    if entry.action not in actions:
                        actions[entry.action] = 0
                    actions[entry.action] += 1
                    
                    # Notas analisadas
                    if entry.note_id:
                        notes_analyzed.add(entry.note_id)
                        
                except (json.JSONDecodeError, TypeError):
                    continue
        
        # Calcula estatísticas
        total_duration = sum(e.duration for e in entries if e.duration)
        avg_duration = total_duration / len(entries) if entries else 0
        
        return {
            "summary": {
                "total_entries": len(entries),
                "unique_users": len(users),
                "unique_actions": len(actions),
                "notes_analyzed": len(notes_analyzed),
                "total_duration": total_duration,
                "avg_duration": avg_duration,
                "period": {
                    "start": min(e.timestamp for e in entries) if entries else None,
                    "end": max(e.timestamp for e in entries) if entries else None
                }
            },
            "users": list(users),
            "actions": actions,
            "notes": list(notes_analyzed)
        }

class StructuredLogger:
    """Logger estruturado com suporte a contexto e metadados."""
    
    def __init__(self, name: str):
        """
        Inicializa logger estruturado.
        
        Args:
            name: Nome do logger
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.context = {}
        self._lock = threading.Lock()
    
    def set_context(self, **kwargs):
        """
        Define contexto para todas as mensagens subsequentes.
        
        Args:
            **kwargs: Pares chave-valor do contexto
        """
        with self._lock:
            self.context.update(kwargs)
    
    def clear_context(self):
        """Limpa o contexto atual."""
        with self._lock:
            self.context.clear()
    
    def _log(self, level: str, message: str, **kwargs):
        """
        Registra mensagem estruturada.
        
        Args:
            level: Nível do log
            message: Mensagem principal
            **kwargs: Dados adicionais
        """
        # Combina contexto com dados específicos
        log_data = {
            "timestamp": time.time(),
            "level": level,
            "message": message,
            "logger": self.name,
            "thread": threading.current_thread().name,
            "user": getpass.getuser()
        }
        
        # Adiciona contexto
        with self._lock:
            log_data.update(self.context)
        
        # Adiciona dados específicos
        log_data.update(kwargs)
        
        # Registra usando logger padrão
        getattr(self.logger, level.lower())(json.dumps(log_data, default=str))
    
    def debug(self, message: str, **kwargs):
        """Registra mensagem de debug."""
        self._log("DEBUG", message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Registra mensagem informativa."""
        self._log("INFO", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Registra mensagem de aviso."""
        self._log("WARNING", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Registra mensagem de erro."""
        self._log("ERROR", message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Registra mensagem crítica."""
        self._log("CRITICAL", message, **kwargs)

class DatabaseLogger:
    """Logger especializado para operações de banco de dados."""
    
    def __init__(self):
        """Inicializa logger de banco de dados."""
        self.logger = get_logger("database")
        self.query_log = AppSettings.LOGS_DIR / "database_queries.jsonl"
        self._lock = threading.Lock()
    
    def log_query(self, query: str, params: Optional[Dict] = None,
                  duration: Optional[float] = None, result_count: Optional[int] = None,
                  database: str = "unknown"):
        """
        Registra execução de query.
        
        Args:
            query: Query SQL executada
            params: Parâmetros da query (opcional)
            duration: Duração da execução (opcional)
            result_count: Número de resultados (opcional)
            database: Nome do banco de dados
        """
        entry = {
            "timestamp": time.time(),
            "user": getuser.getuser(),
            "database": database,
            "query": query,
            "params": params,
            "duration": duration,
            "result_count": result_count,
            "thread": threading.current_thread().name
        }
        
        # Log estruturado
        self.logger.info("Database query executed", **entry)
        
        # Log específico de queries
        with self._lock:
            with open(self.query_log, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, default=str) + '\n')
    
    def log_connection(self, database: str, status: str, error: Optional[str] = None):
        """
        Registra tentativa de conexão.
        
        Args:
            database: Nome do banco de dados
            status: Status da conexão (success/failed)
            error: Mensagem de erro (opcional)
        """
        self.logger.info(f"Database connection {status}", 
                        database=database, error=error)

# Instâncias globais
audit_logger = AuditLogger()
db_logger = DatabaseLogger()

def setup_logging():
    """Configura sistema de logging da aplicação."""
    # Cria diretório de logs
    AppSettings.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Configuração básica
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(AppSettings.LOGS_DIR / 'application.log'),
            logging.StreamHandler()
        ]
    )
    
    # Logger específico para erros
    error_handler = logging.FileHandler(AppSettings.LOGS_DIR / 'errors.log')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n%(exc_info)s'
    ))
    
    # Adiciona handler de erro a todos os loggers
    logging.getLogger().addHandler(error_handler)

def get_logger(name: str) -> StructuredLogger:
    """
    Obtém logger estruturado.
    
    Args:
        name: Nome do logger
        
    Returns:
        Logger estruturado
    """
    return StructuredLogger(name)

# Funções de conveniência para auditoria
def log_user_action(action: str, details: Optional[Dict[str, Any]] = None,
                   note_id: Optional[str] = None, result: Optional[str] = None):
    """
    Registra ação do usuário para auditoria.
    
    Args:
        action: Nome da ação
        details: Detalhes da ação
        note_id: ID da nota (opcional)
        result: Resultado da ação (opcional)
    """
    audit_logger.log_action(action, details, note_id, result)

def log_decision_tree_action(question_id: str, answer: str, flags_activated: List[str],
                           note_id: str, duration: Optional[float] = None):
    """
    Registra ação específica da árvore de decisão.
    
    Args:
        question_id: ID da pergunta
        answer: Resposta selecionada
        flags_activated: Lista de flags ativadas
        note_id: ID da nota
        duration: Duração da resposta (opcional)
    """
    details = {
        "question_id": question_id,
        "answer": answer,
        "flags_activated": flags_activated,
        "flags_count": len(flags_activated)
    }
    
    audit_logger.log_action("decision_tree_answer", details, note_id, duration=duration)

def log_report_generation(note_id: str, report_type: str, flags_used: List[str],
                         with_deadline: bool, deadline_days: Optional[int] = None):
    """
    Registra geração de parecer.
    
    Args:
        note_id: ID da nota
        report_type: Tipo do parecer (deferido/indeferido)
        flags_used: Lista de flags utilizadas
        with_deadline: Se incluiu prazo
        deadline_days: Dias de prazo (opcional)
    """
    details = {
        "report_type": report_type,
        "flags_used": flags_used,
        "flags_count": len(flags_used),
        "with_deadline": with_deadline,
        "deadline_days": deadline_days
    }
    
    audit_logger.log_action("report_generated", details, note_id, result=report_type)

def log_email_sent(note_id: str, recipient: str, success: bool, 
                  error: Optional[str] = None):
    """
    Registra envio de e-mail.
    
    Args:
        note_id: ID da nota
        recipient: Destinatário
        success: Se o envio foi bem-sucedido
        error: Mensagem de erro (opcional)
    """
    details = {
        "recipient": recipient,
        "success": success,
        "error": error
    }
    
    result = "success" if success else "failed"
    audit_logger.log_action("email_sent", details, note_id, result=result)

def log_database_operation(operation: str, database: str, duration: Optional[float] = None,
                          result_count: Optional[int] = None, error: Optional[str] = None):
    """
    Registra operação de banco de dados.
    
    Args:
        operation: Tipo de operação
        database: Nome do banco
        duration: Duração da operação (opcional)
        result_count: Número de resultados (opcional)
        error: Mensagem de erro (opcional)
    """
    details = {
        "database": database,
        "duration": duration,
        "result_count": result_count,
        "error": error
    }
    
    result = "success" if not error else "failed"
    audit_logger.log_action(f"database_{operation}", details, result=result)

# Decorator para log automático de funções
def log_function_call(action_name: Optional[str] = None):
    """
    Decorator para log automático de chamadas de função.
    
    Args:
        action_name: Nome personalizado da ação (opcional)
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            action = action_name or f"{func.__module__}.{func.__name__}"
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                log_user_action(action, {"duration": duration}, result="success")
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                log_user_action(action, {"duration": duration, "error": str(e)}, result="failed")
                raise
        
        return wrapper
    return decorator