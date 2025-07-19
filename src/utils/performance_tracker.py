"""
Sistema avançado de medição e análise de performance.
Inclui medição de tempo detalhada, análise de gargalos e relatórios.
"""

import time
import threading
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from contextlib import contextmanager
import pandas as pd
from collections import defaultdict, deque
import psutil

from src.config.settings import AppSettings, PerformanceSettings
from src.utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class PerformanceMetric:
    """Métrica individual de performance."""
    name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    memory_start: Optional[float] = None
    memory_end: Optional[float] = None
    memory_delta: Optional[float] = None
    cpu_percent: Optional[float] = None
    details: Optional[Dict[str, Any]] = None
    thread_id: Optional[int] = None
    process_id: Optional[int] = None
    
    def __post_init__(self):
        """Inicializa valores calculados."""
        if self.end_time and self.start_time:
            self.duration = self.end_time - self.start_time
        
        if self.memory_start and self.memory_end:
            self.memory_delta = self.memory_end - self.memory_start
        
        self.thread_id = threading.get_ident()
        self.process_id = os.getpid()

class PerformanceTracker:
    """
    Rastreador de performance com medição detalhada de tempo,
    memória e CPU.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Implementa padrão Singleton thread-safe."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Inicializa o rastreador de performance."""
        if hasattr(self, '_initialized'):
            return
            
        self._initialized = True
        self.metrics: Dict[str, List[PerformanceMetric]] = defaultdict(list)
        self.active_trackers: Dict[str, PerformanceMetric] = {}
        self.session_start = time.time()
        self._lock = threading.Lock()
        
        # Configurações
        self.enabled = PerformanceSettings.ENABLE_PERFORMANCE_TRACKING
        self.max_records = PerformanceSettings.MAX_PERFORMANCE_RECORDS
        
        # Processo atual para monitoramento
        self.process = psutil.Process()
        
        logger.info("PerformanceTracker inicializado")
    
    @contextmanager
    def track(self, operation_name: str, details: Optional[Dict[str, Any]] = None):
        """
        Context manager para medição automática de performance.
        
        Args:
            operation_name: Nome da operação sendo medida
            details: Detalhes adicionais sobre a operação
            
        Yields:
            PerformanceMetric: Métrica sendo coletada
        """
        if not self.enabled:
            yield None
            return
        
        metric = self.start_tracking(operation_name, details)
        try:
            yield metric
        finally:
            self.end_tracking(operation_name)
    
    def start_tracking(self, operation_name: str, details: Optional[Dict[str, Any]] = None) -> PerformanceMetric:
        """
        Inicia o rastreamento de uma operação.
        
        Args:
            operation_name: Nome da operação
            details: Detalhes adicionais
            
        Returns:
            PerformanceMetric: Métrica iniciada
        """
        if not self.enabled:
            return None
        
        with self._lock:
            # Coleta informações iniciais
            current_time = time.time()
            memory_info = self.process.memory_info()
            cpu_percent = self.process.cpu_percent()
            
            metric = PerformanceMetric(
                name=operation_name,
                start_time=current_time,
                memory_start=memory_info.rss / 1024 / 1024,  # MB
                cpu_percent=cpu_percent,
                details=details or {}
            )
            
            self.active_trackers[operation_name] = metric
            
            logger.debug(f"Iniciou rastreamento: {operation_name}")
            return metric
    
    def end_tracking(self, operation_name: str) -> Optional[PerformanceMetric]:
        """
        Finaliza o rastreamento de uma operação.
        
        Args:
            operation_name: Nome da operação
            
        Returns:
            PerformanceMetric: Métrica finalizada
        """
        if not self.enabled or operation_name not in self.active_trackers:
            return None
        
        with self._lock:
            metric = self.active_trackers.pop(operation_name)
            
            # Coleta informações finais
            current_time = time.time()
            memory_info = self.process.memory_info()
            
            metric.end_time = current_time
            metric.memory_end = memory_info.rss / 1024 / 1024  # MB
            metric.duration = metric.end_time - metric.start_time
            metric.memory_delta = metric.memory_end - metric.memory_start
            
            # Armazena métrica
            self.metrics[operation_name].append(metric)
            
            # Limita número de registros
            if len(self.metrics[operation_name]) > self.max_records:
                self.metrics[operation_name] = self.metrics[operation_name][-self.max_records:]
            
            logger.debug(f"Finalizou rastreamento: {operation_name} ({metric.duration:.3f}s)")
            return metric
    
    def add_detail(self, operation_name: str, key: str, value: Any):
        """
        Adiciona detalhe a uma operação ativa.
        
        Args:
            operation_name: Nome da operação
            key: Chave do detalhe
            value: Valor do detalhe
        """
        if not self.enabled or operation_name not in self.active_trackers:
            return
        
        with self._lock:
            metric = self.active_trackers[operation_name]
            if metric.details is None:
                metric.details = {}
            metric.details[key] = value
    
    def get_metrics(self, operation_name: Optional[str] = None) -> Union[List[PerformanceMetric], Dict[str, List[PerformanceMetric]]]:
        """
        Obtém métricas coletadas.
        
        Args:
            operation_name: Nome específico da operação (opcional)
            
        Returns:
            Métricas coletadas
        """
        with self._lock:
            if operation_name:
                return self.metrics.get(operation_name, [])
            return dict(self.metrics)
    
    def get_statistics(self, operation_name: str) -> Dict[str, float]:
        """
        Calcula estatísticas para uma operação.
        
        Args:
            operation_name: Nome da operação
            
        Returns:
            Estatísticas calculadas
        """
        metrics = self.get_metrics(operation_name)
        if not metrics:
            return {}
        
        durations = [m.duration for m in metrics if m.duration is not None]
        memory_deltas = [m.memory_delta for m in metrics if m.memory_delta is not None]
        
        stats = {
            'count': len(metrics),
            'total_duration': sum(durations),
            'avg_duration': sum(durations) / len(durations) if durations else 0,
            'min_duration': min(durations) if durations else 0,
            'max_duration': max(durations) if durations else 0,
        }
        
        if memory_deltas:
            stats.update({
                'avg_memory_delta': sum(memory_deltas) / len(memory_deltas),
                'max_memory_delta': max(memory_deltas),
                'min_memory_delta': min(memory_deltas)
            })
        
        return stats
    
    def export_to_json(self, filepath: Optional[Path] = None) -> Path:
        """
        Exporta métricas para arquivo JSON.
        
        Args:
            filepath: Caminho do arquivo (opcional)
            
        Returns:
            Caminho do arquivo exportado
        """
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = AppSettings.PERFORMANCE_DIR / f"performance_metrics_{timestamp}.json"
        
        # Prepara dados para exportação
        export_data = {
            'session_info': {
                'start_time': self.session_start,
                'export_time': time.time(),
                'duration': time.time() - self.session_start,
                'process_id': os.getpid(),
                'thread_count': threading.active_count()
            },
            'metrics': {}
        }
        
        with self._lock:
            for operation_name, metrics_list in self.metrics.items():
                export_data['metrics'][operation_name] = [
                    asdict(metric) for metric in metrics_list
                ]
        
        # Salva arquivo
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        logger.info(f"Métricas exportadas para: {filepath}")
        return filepath
    
    def export_to_parquet(self, filepath: Optional[Path] = None) -> Path:
        """
        Exporta métricas para arquivo Parquet (mais eficiente).
        
        Args:
            filepath: Caminho do arquivo (opcional)
            
        Returns:
            Caminho do arquivo exportado
        """
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = AppSettings.PERFORMANCE_DIR / f"performance_metrics_{timestamp}.parquet"
        
        # Converte métricas para DataFrame
        all_metrics = []
        with self._lock:
            for operation_name, metrics_list in self.metrics.items():
                for metric in metrics_list:
                    metric_dict = asdict(metric)
                    metric_dict['operation'] = operation_name
                    all_metrics.append(metric_dict)
        
        if not all_metrics:
            logger.warning("Nenhuma métrica para exportar")
            return filepath
        
        df = pd.DataFrame(all_metrics)
        
        # Adiciona colunas calculadas
        df['start_datetime'] = pd.to_datetime(df['start_time'], unit='s')
        df['end_datetime'] = pd.to_datetime(df['end_time'], unit='s')
        
        # Salva arquivo
        df.to_parquet(filepath, index=False)
        
        logger.info(f"Métricas exportadas para Parquet: {filepath}")
        return filepath
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Gera relatório completo de performance.
        
        Returns:
            Relatório de performance
        """
        report = {
            'summary': {
                'session_duration': time.time() - self.session_start,
                'total_operations': sum(len(metrics) for metrics in self.metrics.values()),
                'unique_operations': len(self.metrics),
                'active_trackers': len(self.active_trackers)
            },
            'operations': {},
            'system_info': {
                'cpu_count': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total / 1024 / 1024 / 1024,  # GB
                'memory_available': psutil.virtual_memory().available / 1024 / 1024 / 1024,  # GB
                'process_memory': self.process.memory_info().rss / 1024 / 1024  # MB
            }
        }
        
        # Estatísticas por operação
        for operation_name in self.metrics:
            stats = self.get_statistics(operation_name)
            report['operations'][operation_name] = stats
        
        return report
    
    def clear_metrics(self, operation_name: Optional[str] = None):
        """
        Limpa métricas armazenadas.
        
        Args:
            operation_name: Nome específico da operação (opcional)
        """
        with self._lock:
            if operation_name:
                if operation_name in self.metrics:
                    del self.metrics[operation_name]
                    logger.info(f"Métricas limpas para: {operation_name}")
            else:
                self.metrics.clear()
                logger.info("Todas as métricas foram limpas")
    
    def get_top_slowest(self, limit: int = 10) -> List[tuple]:
        """
        Retorna as operações mais lentas.
        
        Args:
            limit: Número máximo de resultados
            
        Returns:
            Lista de tuplas (operação, duração_máxima)
        """
        slowest = []
        
        with self._lock:
            for operation_name, metrics_list in self.metrics.items():
                durations = [m.duration for m in metrics_list if m.duration is not None]
                if durations:
                    max_duration = max(durations)
                    slowest.append((operation_name, max_duration))
        
        return sorted(slowest, key=lambda x: x[1], reverse=True)[:limit]

# Instância global do rastreador
performance_tracker = PerformanceTracker()

# Context manager para facilitar uso
@contextmanager
def track_performance(operation_name: str, details: Optional[Dict[str, Any]] = None):
    """
    Context manager global para rastreamento de performance.
    
    Args:
        operation_name: Nome da operação
        details: Detalhes adicionais
    """
    with performance_tracker.track(operation_name, details) as metric:
        yield metric

# Decorator para medição automática de funções
def measure_performance(func_or_name=None):
    """
    Decorator para medição automática de performance de funções.
    
    Args:
        func_or_name: Função ou nome personalizado da operação
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            operation_name = func_or_name if isinstance(func_or_name, str) else f"{func.__module__}.{func.__name__}"
            
            with track_performance(operation_name):
                return func(*args, **kwargs)
        
        return wrapper
    
    # Se chamado com argumentos
    if callable(func_or_name):
        return decorator(func_or_name)
    else:
        return decorator

# Classe auxiliar para medição de etapas
class StageTracker:
    """Rastreador especializado para etapas de análise."""
    
    def __init__(self, note_id: str, user_id: str):
        """
        Inicializa rastreador de etapas.
        
        Args:
            note_id: ID da nota sendo analisada
            user_id: ID do usuário
        """
        self.note_id = note_id
        self.user_id = user_id
        self.stages = {}
        self.current_stage = None
    
    def start_stage(self, stage_name: str):
        """Inicia uma nova etapa."""
        if self.current_stage:
            self.end_stage(self.current_stage)
        
        self.current_stage = stage_name
        operation_name = f"stage_{stage_name}_{self.note_id}"
        
        performance_tracker.start_tracking(operation_name, {
            'note_id': self.note_id,
            'user_id': self.user_id,
            'stage': stage_name
        })
    
    def end_stage(self, stage_name: str):
        """Finaliza uma etapa."""
        operation_name = f"stage_{stage_name}_{self.note_id}"
        metric = performance_tracker.end_tracking(operation_name)
        
        if metric:
            self.stages[stage_name] = {
                'duration': metric.duration,
                'memory_delta': metric.memory_delta,
                'timestamp': metric.start_time
            }
        
        if self.current_stage == stage_name:
            self.current_stage = None
    
    def get_total_time(self) -> float:
        """Retorna tempo total de todas as etapas."""
        return sum(stage['duration'] for stage in self.stages.values())
    
    def export_stages(self) -> Dict[str, Any]:
        """Exporta dados das etapas."""
        return {
            'note_id': self.note_id,
            'user_id': self.user_id,
            'stages': self.stages,
            'total_time': self.get_total_time(),
            'stage_count': len(self.stages)
        }