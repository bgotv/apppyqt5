# app/utils/logger.py
"""
Módulo para registro e visualização de métricas e logs.
"""
import os
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from app.config import settings
import getpass

# Configuração do logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(settings.LOGS_DIR, 'app.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('app')

class MetricsManager:
    """
    Gerencia métricas de desempenho e uso da aplicação.
    """
    def __init__(self):
        """Inicializa o gerenciador de métricas."""
        self.metrics_file = os.path.join(settings.PERFORMANCE_DIR, 'metrics.json')
        self.session_metrics = {
            'start_time': time.time(),
            'actions': [],
            'database_operations': [],
            'ui_actions': [],
            'analysis_time': {},
            'notes_analyzed': 0,
            'stage_durations': []
        }
        self._load_metrics()
        self.process_stages = {}  # note_id -> { etapa: {start,end,duration} }
        self.username = getpass.getuser()

    def _load_metrics(self):
        """Carrega métricas existentes do arquivo JSON."""
        if os.path.exists(self.metrics_file):
            try:
                with open(self.metrics_file, 'r', encoding='utf-8') as f:
                    self.all_metrics = json.load(f)
            except Exception as e:
                logger.error(f"Erro ao carregar métricas JSON: {e}")
                self.all_metrics = {'sessions': []}
        else:
            self.all_metrics = {'sessions': []}

    def _save_metrics(self):
        """
        Salva a sessão atual em um arquivo JSON mensal, acumulando registros.
        """
        try:
            # calcula duração da sessão
            self.session_metrics['duration'] = time.time() - self.session_metrics['start_time']

            # nome do arquivo por ano e mês
            now = datetime.now()
            ano_mes = f"{now.year}_{now.month:02d}"
            json_path = os.path.join(settings.PERFORMANCE_DIR, f"sessions_{ano_mes}.json")

            # carrega existentes
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
                if not isinstance(existing, list):
                    existing = []
            else:
                existing = []

            # adiciona nova sessão e salva
            existing.append(self.session_metrics)
            os.makedirs(os.path.dirname(json_path), exist_ok=True)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(existing, f, indent=2)

            logger.info(f"Métricas salvas em {json_path}")
        except Exception as e:
            logger.error(f"Erro ao salvar métricas JSON: {e}")

    def record_action(self, action_type, details=None):
        """Registra uma ação genérica."""
        action = {
            'type': action_type,
            'timestamp': time.time(),
            'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        if details:
            action['details'] = details
        self.session_metrics['actions'].append(action)

    def record_database_operation(self, operation_type, duration, details=None):
        """Registra uma operação de DB."""
        op = {
            'type': operation_type,
            'duration': duration,
            'timestamp': time.time(),
            'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        if details:
            op['details'] = details
        self.session_metrics['database_operations'].append(op)

    def record_ui_action(self, action_type, details=None):
        """Registra ação de UI."""
        ui = {
            'type': action_type,
            'timestamp': time.time(),
            'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        if details:
            ui['details'] = details
        self.session_metrics['ui_actions'].append(ui)

    def start_analysis_timer(self, note_id):
        """Inicia timer de análise de nota."""
        self.session_metrics['analysis_time'][note_id] = {'start': time.time(), 'steps': []}

    def record_analysis_step(self, note_id, step_name):
        """Registra passo na análise de nota."""
        if note_id in self.session_metrics['analysis_time']:
            self.session_metrics['analysis_time'][note_id]['steps'].append({
                'name': step_name, 'timestamp': time.time()
            })

    def end_analysis_timer(self, note_id, success=True):
        """Finaliza timer de análise de nota."""
        if note_id in self.session_metrics['analysis_time']:
            a = self.session_metrics['analysis_time'][note_id]
            a['end'] = time.time()
            a['duration'] = a['end'] - a['start']
            a['success'] = success
            if success:
                self.session_metrics['notes_analyzed'] += 1

    def get_session_metrics(self):
        return self.session_metrics.copy()

    def get_all_metrics(self):
        return self.all_metrics.copy()

    def get_average_analysis_time(self):
        times = [a['duration'] for a in self.session_metrics['analysis_time'].values() if a.get('success')]
        return sum(times)/len(times) if times else 0

    def start_stage(self, note_id, stage_name):
        """Inicia etapa temporizada."""
        self.process_stages.setdefault(note_id, {})[stage_name] = {'start': time.time(), 'end': None, 'duration': None}

    def end_stage(self, note_id, stage_name):
        """Finaliza etapa temporizada."""
        s = self.process_stages.get(note_id, {}).get(stage_name)
        if s and s['start']:
            s['end'] = time.time()
            s['duration'] = s['end'] - s['start']
             # ➊ Registra também no JSON de sessão
            self.session_metrics['stage_durations'].append({
               'note_id':      note_id,
               'stage':        stage_name,
               'start_time':   s['start'],
               'end_time':     s['end'],
               'duration_s':   s['duration'],
               'timestamp':    datetime.now().isoformat(),  # opcional
               'user':         self.username
           })

    def _export_stage_durations(self):
        """Exporta etapas para Parquet mensal acumulado."""
        import pandas as pd
        now = datetime.now()
        key = f"{now.year}_{now.month:02d}"
        path = os.path.join(settings.PERFORMANCE_DIR, f"stages_{key}.parquet")
        rows = []
        for nid, stages in self.process_stages.items():
            for st, d in stages.items():
                rows.append({
                    'note_id': nid,
                    'stage': st,
                    'start_time': datetime.fromtimestamp(d['start']).isoformat() if d['start'] else None,
                    'end_time': datetime.fromtimestamp(d['end']).isoformat() if d['end'] else None,
                    'duration_s': d['duration'],
                    'user': self.username
                })
        df_new = pd.DataFrame(rows)
        if os.path.exists(path):
            try:
                df_old = pd.read_parquet(path)
                df = pd.concat([df_old, df_new], ignore_index=True)
                # remove complete duplicates (same note_id, stage, start_time)
                df = df.drop_duplicates(subset=['note_id','stage','start_time'], keep='last')
            except:
                df = df_new
        else:
            df = df_new
        df.to_parquet(path, index=False)
        logger.info(f"Estágios exportados para {path}")

    def _export_analysis_steps(self):
        """Exporta passos de análise para Parquet mensal acumulado."""
        import pandas as pd
        from datetime import datetime as _dt
        rows = []
        for nid, a in self.session_metrics['analysis_time'].items():
            for idx, step in enumerate(a.get('steps', [])):
                rows.append({
                    'note_id': nid,
                    'step_name': step['name'],
                    'timestamp': _dt.fromtimestamp(step['timestamp']).isoformat(),
                    'step_index': idx+1,
                    'user': self.username
                })
        if not rows:
            return
        df = pd.DataFrame(rows)
        month_str = datetime.now().strftime('%Y%m')
        path = os.path.join(settings.PERFORMANCE_DIR, f"steps_{month_str}.parquet")
        os.makedirs(settings.PERFORMANCE_DIR, exist_ok=True)
        if os.path.exists(path):
            try:
                old = pd.read_parquet(path)
                df = pd.concat([old, df], ignore_index=True)
                df = df.drop_duplicates(subset=['note_id','step_name','timestamp'], keep='last')
            except:
                pass
        df.to_parquet(path, index=False)
        logger.info(f"Passos exportados para {path}")

    def export_now(self):
        self._export_stage_durations()
        self._export_analysis_steps()
        self._save_metrics()

    def close(self):
        self._export_stage_durations()
        self._save_metrics()

# Instância global
metrics_manager = MetricsManager()


def log_action(action_type, details=None):
    logger.info(f"Action: {action_type} - {details}")
    metrics_manager.record_action(action_type, details)


def log_database_operation(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            res = func(*args, **kwargs)
            dur = time.time() - start
            metrics_manager.record_database_operation(func.__name__, dur, {'success': True})
            return res
        except Exception as e:
            dur = time.time() - start
            metrics_manager.record_database_operation(func.__name__, dur, {'success': False, 'error': str(e)})
            raise
    return wrapper


def log_ui_action(action_type, details=None):
    logger.info(f"UI Action: {action_type} - {details}")
    metrics_manager.record_ui_action(action_type, details)


def close_metrics():
    metrics_manager.close()
