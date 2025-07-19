"""
Módulo para gerenciamento de bloqueio de notas.
"""
import os
import time
import getpass
import socket
from datetime import datetime
from app.utils.logger import log_action
from app.config import settings

class NotesLockManager:
    """
    Gerencia o bloqueio de notas para evitar análise simultânea por múltiplos usuários.
    """
    
    def __init__(self, lock_file_path=None):
        """
        Inicializa o gerenciador de bloqueio de notas.
        
        Args:
            lock_file_path (str, optional): Caminho para o arquivo de bloqueio.
        """
        self.lock_file_path = lock_file_path or settings.LOCK_FILE_PATH
        self.username = getpass.getuser()
        self.hostname = socket.gethostname()
        self.locked_notes = {}
        self._load_locks()
    
    def _load_locks(self):
        """Carrega os bloqueios do arquivo."""
        self.locked_notes = {}
        
        if not os.path.exists(self.lock_file_path):
            # Cria o arquivo se não existir
            try:
                with open(self.lock_file_path, 'w') as f:
                    f.write("# Arquivo de bloqueio de notas\n")
                    f.write("# Formato: nota_id|username|hostname|timestamp\n")
                log_action('lock_file_created', {'path': self.lock_file_path})
            except Exception as e:
                log_action('lock_file_creation_error', {'error': str(e)})
            return
        
        try:
            with open(self.lock_file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split('|')
                    if len(parts) >= 4:
                        note_id, user, host, timestamp_str = parts[:4]
                        try:
                            timestamp = float(timestamp_str)
                            self.locked_notes[note_id] = {
                                'user': user,
                                'host': host,
                                'timestamp': timestamp,
                                'datetime': datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                            }
                        except ValueError:
                            pass
            
            log_action('locks_loaded', {'count': len(self.locked_notes)})
        except Exception as e:
            log_action('load_locks_error', {'error': str(e)})
    
    def _save_locks(self):
        """Salva os bloqueios no arquivo."""
        try:
            with open(self.lock_file_path, 'w') as f:
                f.write("# Arquivo de bloqueio de notas\n")
                f.write("# Formato: nota_id|username|hostname|timestamp\n")
                
                for note_id, lock_info in self.locked_notes.items():
                    f.write(f"{note_id}|{lock_info['user']}|{lock_info['host']}|{lock_info['timestamp']}\n")
            
            log_action('locks_saved', {'count': len(self.locked_notes)})
            return True
        except Exception as e:
            log_action('save_locks_error', {'error': str(e)})
            return False
    
    def lock_note(self, note_id):
        """
        Bloqueia uma nota para análise.
        
        Args:
            note_id (str): Identificador da nota.
            
        Returns:
            bool: True se o bloqueio foi bem-sucedido, False caso contrário.
        """
        # Recarrega os bloqueios para garantir que estamos com a informação mais recente
        self._load_locks()
        
        # Verifica se a nota já está bloqueada
        if note_id in self.locked_notes:
            lock_info = self.locked_notes[note_id]
            
            # Se a nota estiver bloqueada pelo usuário atual, atualiza o timestamp
            if lock_info['user'] == self.username and lock_info['host'] == self.hostname:
                lock_info['timestamp'] = time.time()
                lock_info['datetime'] = datetime.fromtimestamp(lock_info['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                self._save_locks()
                log_action('note_lock_refreshed', {'note_id': note_id})
                return True
            
            # Verifica se o bloqueio expirou (mais de 4 horas)
            current_time = time.time()
            if current_time - lock_info['timestamp'] > 4 * 60 * 60:  # 4 horas em segundos
                # Remove o bloqueio expirado
                log_action('note_lock_expired', {
                    'note_id': note_id,
                    'previous_user': lock_info['user'],
                    'previous_host': lock_info['host'],
                    'lock_age_hours': (current_time - lock_info['timestamp']) / 3600
                })
            else:
                # Nota bloqueada por outro usuário
                log_action('note_lock_failed', {
                    'note_id': note_id,
                    'reason': 'locked_by_other_user',
                    'locked_by': f"{lock_info['user']}@{lock_info['host']}",
                    'locked_at': lock_info['datetime']
                })
                return False
        
        # Bloqueia a nota
        self.locked_notes[note_id] = {
            'user': self.username,
            'host': self.hostname,
            'timestamp': time.time(),
            'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Salva os bloqueios
        success = self._save_locks()
        
        if success:
            log_action('note_locked', {'note_id': note_id})
        
        return success
    
    def unlock_note(self, note_id):
        """
        Desbloqueia uma nota.
        
        Args:
            note_id (str): Identificador da nota.
            
        Returns:
            bool: True se o desbloqueio foi bem-sucedido, False caso contrário.
        """
        # Recarrega os bloqueios para garantir que estamos com a informação mais recente
        self._load_locks()
        
        # Verifica se a nota está bloqueada
        if note_id not in self.locked_notes:
            log_action('note_unlock_failed', {
                'note_id': note_id,
                'reason': 'not_locked'
            })
            return False
        
        # Verifica se a nota está bloqueada pelo usuário atual
        lock_info = self.locked_notes[note_id]
        if lock_info['user'] != self.username or lock_info['host'] != self.hostname:
            log_action('note_unlock_failed', {
                'note_id': note_id,
                'reason': 'locked_by_other_user',
                'locked_by': f"{lock_info['user']}@{lock_info['host']}",
                'locked_at': lock_info['datetime']
            })
            return False
        
        # Remove o bloqueio
        del self.locked_notes[note_id]
        
        # Salva os bloqueios
        success = self._save_locks()
        
        if success:
            log_action('note_unlocked', {'note_id': note_id})
        
        return success
    
    def is_note_locked(self, note_id):
        """
        Verifica se uma nota está bloqueada.
        
        Args:
            note_id (str): Identificador da nota.
            
        Returns:
            bool: True se a nota estiver bloqueada, False caso contrário.
        """
        # Recarrega os bloqueios para garantir que estamos com a informação mais recente
        self._load_locks()
        
        # Verifica se a nota está bloqueada
        if note_id not in self.locked_notes:
            return False
        
        # Verifica se o bloqueio expirou (mais de 4 horas)
        lock_info = self.locked_notes[note_id]
        current_time = time.time()
        if current_time - lock_info['timestamp'] > 4 * 60 * 60:  # 4 horas em segundos
            # Remove o bloqueio expirado
            del self.locked_notes[note_id]
            self._save_locks()
            log_action('note_lock_expired_check', {
                'note_id': note_id,
                'previous_user': lock_info['user'],
                'previous_host': lock_info['host'],
                'lock_age_hours': (current_time - lock_info['timestamp']) / 3600
            })
            return False
        
        return True
    
    def is_note_locked_by_me(self, note_id):
        """
        Verifica se uma nota está bloqueada pelo usuário atual.
        
        Args:
            note_id (str): Identificador da nota.
            
        Returns:
            bool: True se a nota estiver bloqueada pelo usuário atual, False caso contrário.
        """
        # Recarrega os bloqueios para garantir que estamos com a informação mais recente
        self._load_locks()
        
        # Verifica se a nota está bloqueada
        if note_id not in self.locked_notes:
            return False
        
        # Verifica se o bloqueio expirou (mais de 4 horas)
        lock_info = self.locked_notes[note_id]
        current_time = time.time()
        if current_time - lock_info['timestamp'] > 4 * 60 * 60:  # 4 horas em segundos
            # Remove o bloqueio expirado
            del self.locked_notes[note_id]
            self._save_locks()
            return False
        
        # Verifica se a nota está bloqueada pelo usuário atual
        return lock_info['user'] == self.username and lock_info['host'] == self.hostname
    
    def get_lock_info(self, note_id):
        """
        Obtém informações sobre o bloqueio de uma nota.
        
        Args:
            note_id (str): Identificador da nota.
            
        Returns:
            dict: Informações sobre o bloqueio, None se a nota não estiver bloqueada.
        """
        # Recarrega os bloqueios para garantir que estamos com a informação mais recente
        self._load_locks()
        
        # Verifica se a nota está bloqueada
        if note_id not in self.locked_notes:
            return None
        
        # Verifica se o bloqueio expirou (mais de 4 horas)
        lock_info = self.locked_notes[note_id]
        current_time = time.time()
        if current_time - lock_info['timestamp'] > 4 * 60 * 60:  # 4 horas em segundos
            # Remove o bloqueio expirado
            del self.locked_notes[note_id]
            self._save_locks()
            return None
        
        return lock_info.copy()
    
    def get_all_locks(self):
        """
        Obtém todos os bloqueios ativos.
        
        Returns:
            dict: Dicionário com todos os bloqueios ativos.
        """
        # Recarrega os bloqueios para garantir que estamos com a informação mais recente
        self._load_locks()
        
        # Remove bloqueios expirados
        current_time = time.time()
        expired_notes = []
        for note_id, lock_info in self.locked_notes.items():
            if current_time - lock_info['timestamp'] > 4 * 60 * 60:  # 4 horas em segundos
                expired_notes.append(note_id)
        
        for note_id in expired_notes:
            del self.locked_notes[note_id]
        
        if expired_notes:
            self._save_locks()
            log_action('expired_locks_removed', {'count': len(expired_notes)})
        
        return self.locked_notes.copy()
    
    def force_unlock_note(self, note_id, admin_password=None):
        """
        Força o desbloqueio de uma nota (apenas para administradores).
        
        Args:
            note_id (str): Identificador da nota.
            admin_password (str, optional): Senha de administrador.
            
        Returns:
            bool: True se o desbloqueio foi bem-sucedido, False caso contrário.
        """
        # Verifica a senha de administrador
        if admin_password != "admin123":  # Senha simples para exemplo
            log_action('force_unlock_failed', {
                'note_id': note_id,
                'reason': 'invalid_password'
            })
            return False
        
        # Recarrega os bloqueios para garantir que estamos com a informação mais recente
        self._load_locks()
        
        # Verifica se a nota está bloqueada
        if note_id not in self.locked_notes:
            log_action('force_unlock_failed', {
                'note_id': note_id,
                'reason': 'not_locked'
            })
            return False
        
        # Registra informações do bloqueio para log
        lock_info = self.locked_notes[note_id]
        
        # Remove o bloqueio
        del self.locked_notes[note_id]
        
        # Salva os bloqueios
        success = self._save_locks()
        
        if success:
            log_action('note_force_unlocked', {
                'note_id': note_id,
                'previous_user': lock_info['user'],
                'previous_host': lock_info['host'],
                'locked_at': lock_info['datetime']
            })
        
        return success
