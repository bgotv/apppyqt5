"""
Módulo para gerenciamento de bloqueio de notas.
"""
import os
import json
import datetime
import getpass
from app.config import settings
from app.utils.logger import log_action

class NoteLockManager:
    """
    Gerenciador de bloqueio de notas para evitar edição simultânea.
    """
    
    def __init__(self, lock_file_path=None):
        """
        Inicializa o gerenciador de bloqueio de notas.
        
        Args:
            lock_file_path (str, optional): Caminho para o arquivo de bloqueio.
                Se None, usa o valor de settings.LOCK_FILE_PATH.
        """
        self.lock_file_path = lock_file_path or settings.LOCK_FILE_PATH
        self.current_user = getpass.getuser()
        self._ensure_lock_file_exists()
    
    def _ensure_lock_file_exists(self):
        """Garante que o arquivo de bloqueio existe."""
        if not os.path.exists(self.lock_file_path):
            # Cria o diretório se não existir
            os.makedirs(os.path.dirname(self.lock_file_path), exist_ok=True)
            
            # Cria o arquivo com um dicionário vazio
            with open(self.lock_file_path, 'w') as f:
                json.dump({}, f)
    
    def get_locked_notes(self):
        """
        Obtém a lista de notas bloqueadas.
        
        Returns:
            dict: Dicionário com as notas bloqueadas no formato {nota_id: {user, timestamp}}.
        """
        try:
            with open(self.lock_file_path, 'r') as f:
                locks = json.load(f)
            
            # Filtra locks expirados (mais de 4 horas)
            current_time = datetime.datetime.now()
            valid_locks = {}
            
            for note_id, lock_info in locks.items():
                lock_time = datetime.datetime.fromisoformat(lock_info['timestamp'])
                time_diff = (current_time - lock_time).total_seconds() / 3600  # em horas
                
                if time_diff < 4:  # Lock válido por 4 horas
                    valid_locks[note_id] = lock_info
            
            # Atualiza o arquivo se algum lock foi removido
            if len(valid_locks) != len(locks):
                with open(self.lock_file_path, 'w') as f:
                    json.dump(valid_locks, f)
            
            return valid_locks
        except Exception as e:
            log_action('lock_error', {'error': str(e), 'operation': 'get_locked_notes'})
            return {}
    
    def is_note_locked(self, note_id):
        """
        Verifica se uma nota está bloqueada.
        
        Args:
            note_id (str): Identificador da nota.
            
        Returns:
            dict: Informações do bloqueio se a nota estiver bloqueada, None caso contrário.
        """
        locks = self.get_locked_notes()
        return locks.get(str(note_id))
    
    def is_note_locked_by_me(self, note_id):
        """
        Verifica se uma nota está bloqueada pelo usuário atual.
        
        Args:
            note_id (str): Identificador da nota.
            
        Returns:
            bool: True se a nota estiver bloqueada pelo usuário atual, False caso contrário.
        """
        lock_info = self.is_note_locked(note_id)
        if lock_info:
            return lock_info['user'] == self.current_user
        return False
    
    def lock_note(self, note_id):
        """
        Bloqueia uma nota para edição.
        
        Args:
            note_id (str): Identificador da nota.
            
        Returns:
            bool: True se o bloqueio foi bem-sucedido, False caso contrário.
        """
        try:
            # Verifica se a nota já está bloqueada
            lock_info = self.is_note_locked(note_id)
            if lock_info and lock_info['user'] != self.current_user:
                log_action('lock_failed', {
                    'note_id': note_id,
                    'reason': 'already_locked',
                    'locked_by': lock_info['user']
                })
                return False
            
            # Obtém os bloqueios atuais
            locks = self.get_locked_notes()
            
            # Adiciona ou atualiza o bloqueio
            locks[str(note_id)] = {
                'user': self.current_user,
                'timestamp': datetime.datetime.now().isoformat()
            }
            
            # Salva os bloqueios
            with open(self.lock_file_path, 'w') as f:
                json.dump(locks, f)
            
            log_action('note_locked', {'note_id': note_id, 'user': self.current_user})
            return True
        except Exception as e:
            log_action('lock_error', {'error': str(e), 'operation': 'lock_note', 'note_id': note_id})
            return False
    
    def unlock_note(self, note_id):
        """
        Desbloqueia uma nota.
        
        Args:
            note_id (str): Identificador da nota.
            
        Returns:
            bool: True se o desbloqueio foi bem-sucedido, False caso contrário.
        """
        try:
            # Verifica se a nota está bloqueada pelo usuário atual
            if not self.is_note_locked_by_me(note_id):
                log_action('unlock_failed', {
                    'note_id': note_id,
                    'reason': 'not_locked_by_me'
                })
                return False
            
            # Obtém os bloqueios atuais
            locks = self.get_locked_notes()
            
            # Remove o bloqueio
            if str(note_id) in locks:
                del locks[str(note_id)]
            
            # Salva os bloqueios
            with open(self.lock_file_path, 'w') as f:
                json.dump(locks, f)
            
            log_action('note_unlocked', {'note_id': note_id, 'user': self.current_user})
            return True
        except Exception as e:
            log_action('lock_error', {'error': str(e), 'operation': 'unlock_note', 'note_id': note_id})
            return False
    
    def unlock_all_my_notes(self):
        """
        Desbloqueia todas as notas bloqueadas pelo usuário atual.
        
        Returns:
            int: Número de notas desbloqueadas.
        """
        try:
            # Obtém os bloqueios atuais
            locks = self.get_locked_notes()
            
            # Identifica as notas bloqueadas pelo usuário atual
            my_locks = [note_id for note_id, lock_info in locks.items() 
                       if lock_info['user'] == self.current_user]
            
            # Remove os bloqueios
            for note_id in my_locks:
                del locks[note_id]
            
            # Salva os bloqueios
            with open(self.lock_file_path, 'w') as f:
                json.dump(locks, f)
            
            log_action('notes_unlocked_all', {
                'count': len(my_locks),
                'user': self.current_user
            })
            
            return len(my_locks)
        except Exception as e:
            log_action('lock_error', {'error': str(e), 'operation': 'unlock_all_my_notes'})
            return 0
