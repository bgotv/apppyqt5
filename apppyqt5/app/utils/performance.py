"""
Módulo de utilidades para medição de desempenho.
"""
import os
import time
import datetime
import json
import csv
from functools import wraps
from app.config import settings

# Garante que o diretório de performance existe
os.makedirs(settings.PERFORMANCE_DIR, exist_ok=True)

# Arquivo CSV para armazenar métricas de desempenho
PERFORMANCE_CSV = os.path.join(settings.PERFORMANCE_DIR, f"performance_{datetime.datetime.now().strftime('%Y%m%d')}.csv")

# Inicializa o arquivo CSV se não existir
def initialize_performance_csv():
    """Inicializa o arquivo CSV de métricas de desempenho se não existir."""
    if not os.path.exists(PERFORMANCE_CSV):
        with open(PERFORMANCE_CSV, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['timestamp', 'operation', 'duration_ms', 'success', 'details'])

# Inicializa o arquivo CSV
initialize_performance_csv()

def measure_performance(func):
    """
    Decorator para medir o tempo de execução de uma função.
    
    Args:
        func: Função a ser decorada.
        
    Returns:
        wrapper: Função decorada com medição de desempenho.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Registra o tempo de início
        start_time = time.time()
        success = True
        error_msg = None
        
        try:
            # Executa a função
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            # Registra falha
            success = False
            error_msg = str(e)
            raise
        finally:
            # Calcula a duração
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            
            # Registra a métrica
            log_performance(
                operation=func.__name__,
                duration_ms=duration_ms,
                success=success,
                details={'error': error_msg} if error_msg else None
            )
    
    return wrapper

def log_performance(operation, duration_ms, success=True, details=None):
    """
    Registra uma métrica de desempenho no arquivo CSV.
    
    Args:
        operation (str): Nome da operação.
        duration_ms (float): Duração em milissegundos.
        success (bool): Indica se a operação foi bem-sucedida.
        details (dict, optional): Detalhes adicionais.
    """
    timestamp = datetime.datetime.now().isoformat()
    details_str = json.dumps(details) if details else ""
    
    # Registra no arquivo CSV
    with open(PERFORMANCE_CSV, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([timestamp, operation, f"{duration_ms:.2f}", str(success), details_str])
    
    return {
        'timestamp': timestamp,
        'operation': operation,
        'duration_ms': duration_ms,
        'success': success,
        'details': details
    }

class PerformanceTracker:
    """
    Classe para rastrear o desempenho de blocos de código.
    
    Exemplo de uso:
    ```
    with PerformanceTracker("carregar_notas") as tracker:
        # código a ser medido
        notas = carregar_notas_do_banco()
        tracker.add_detail("quantidade_notas", len(notas))
    ```
    """
    
    def __init__(self, operation_name):
        """
        Inicializa o rastreador de desempenho.
        
        Args:
            operation_name (str): Nome da operação a ser rastreada.
        """
        self.operation_name = operation_name
        self.start_time = None
        self.details = {}
    
    def __enter__(self):
        """Inicia a medição ao entrar no bloco with."""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Finaliza a medição ao sair do bloco with."""
        if self.start_time is not None:
            duration_ms = (time.time() - self.start_time) * 1000
            success = exc_type is None
            
            if exc_val:
                self.details['error'] = str(exc_val)
            
            log_performance(
                operation=self.operation_name,
                duration_ms=duration_ms,
                success=success,
                details=self.details
            )
    
    def add_detail(self, key, value):
        """
        Adiciona um detalhe à medição.
        
        Args:
            key (str): Chave do detalhe.
            value: Valor do detalhe.
        """
        self.details[key] = value

def get_performance_summary(operation=None, start_date=None, end_date=None):
    """
    Obtém um resumo das métricas de desempenho.
    
    Args:
        operation (str, optional): Filtrar por operação específica.
        start_date (str, optional): Data de início no formato ISO.
        end_date (str, optional): Data de fim no formato ISO.
        
    Returns:
        dict: Resumo das métricas de desempenho.
    """
    metrics = []
    
    try:
        with open(PERFORMANCE_CSV, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Converte tipos
                row['duration_ms'] = float(row['duration_ms'])
                row['success'] = row['success'].lower() == 'true'
                
                # Filtra por operação
                if operation and row['operation'] != operation:
                    continue
                
                # Filtra por data
                if start_date and row['timestamp'] < start_date:
                    continue
                if end_date and row['timestamp'] > end_date:
                    continue
                
                metrics.append(row)
    except FileNotFoundError:
        return {'error': 'Arquivo de métricas não encontrado'}
    
    # Calcula estatísticas
    if not metrics:
        return {'count': 0, 'message': 'Nenhuma métrica encontrada com os filtros especificados'}
    
    durations = [m['duration_ms'] for m in metrics]
    success_count = sum(1 for m in metrics if m['success'])
    
    return {
        'count': len(metrics),
        'success_rate': success_count / len(metrics) if metrics else 0,
        'avg_duration_ms': sum(durations) / len(durations) if durations else 0,
        'min_duration_ms': min(durations) if durations else 0,
        'max_duration_ms': max(durations) if durations else 0,
        'operations': list(set(m['operation'] for m in metrics))
    }
