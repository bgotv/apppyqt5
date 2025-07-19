"""
Módulo para gerenciamento de flags de pendências.
"""
from app.utils.logger import log_action
from app.config import constants

class FlagsManager:
    """
    Gerencia as flags de pendências durante a análise técnica.
    """
    
    def __init__(self):
        """Inicializa o gerenciador de flags."""
        self.flags = {}
        self.active_flags = {}
        self._init_flags()
    
    def _init_flags(self):
        """Inicializa o dicionário de flags com as definições do sistema."""
        self.flags = constants.FLAG_INFO.copy()
        self.clear_all_flags()

    def get_active_flags_for_report(self):
        """
        Retorna as flags ativas que devem ser consideradas para o relatório de indeferimento.
        Exclui flags que não devem causar indeferimento.
        
        Returns:
            list: Lista de dicionários com informações das flags ativas para indeferimento.
        """
        result = []
        
        for flag_id, value in self.active_flags.items():
            if value and flag_id in self.flags:
                flag_info = self.flags[flag_id]
                
                # Verifica se a flag deve ser considerada para indeferimento
                # Por padrão, todas as flags causam indeferimento, exceto as que têm
                # a propriedade 'indeferimento' definida como False
                if flag_info.get('indeferimento', True):
                    result.append(flag_info)
        
        return result
    
    def clear_all_flags(self):
        """Limpa todas as flags ativas."""
        self.active_flags = {}
        log_action('flags_cleared')
    
    def set_flag(self, flag_id, value=1):
        """
        Define o valor de uma flag.
        
        Args:
            flag_id: Identificador da flag.
            value (int, optional): Valor da flag. Defaults to 1.
            
        Returns:
            bool: True se a flag foi definida com sucesso, False caso contrário.
        """
        if flag_id in self.flags or isinstance(flag_id, (int, str)):
            self.active_flags[flag_id] = value
            log_action('flag_set', {'flag_id': flag_id, 'value': value})
            return True
        return False
    
    def add_flag(self, cabecalho, texto):
        """
        Adiciona uma nova flag personalizada.
        
        Args:
            cabecalho (str): Cabeçalho da flag.
            texto (str): Texto da flag.
            
        Returns:
            str: Identificador da nova flag.
        """
        # Gera um ID único para a flag
        flag_id = f"custom_{len(self.flags) + 1}"
        
        # Adiciona a flag ao dicionário
        self.flags[flag_id] = {
            "cabecalho": cabecalho,
            "texto": texto
        }
        
        # Ativa a flag
        self.active_flags[flag_id] = 1
        
        log_action('flag_added', {
            'flag_id': flag_id,
            'cabecalho': cabecalho,
            'texto': texto
        })
        
        return flag_id
    
    def get_flag(self, flag_id):
        """
        Obtém o valor de uma flag.
        
        Args:
            flag_id: Identificador da flag.
            
        Returns:
            int: Valor da flag, 0 se não estiver ativa.
        """
        return self.active_flags.get(flag_id, 0)
    
    def get_active_flags(self):
        """
        Retorna todas as flags ativas.
        
        Returns:
            dict: Dicionário com as flags ativas.
        """
        return self.active_flags.copy()
    
    def get_flag_info(self, flag_id):
        """
        Obtém as informações de uma flag.
        
        Args:
            flag_id: Identificador da flag.
            
        Returns:
            dict: Informações da flag, None se não existir.
        """
        return self.flags.get(flag_id)
    
    def get_active_flags_by_cabecalho(self):
        """
        Agrupa as flags ativas por cabeçalho.
        
        Returns:
            dict: Dicionário com flags agrupadas por cabeçalho.
        """
        result = {}
        
        for flag_id, value in self.active_flags.items():
            if value and flag_id in self.flags:
                flag_info = self.flags[flag_id]
                cabecalho = flag_info.get("cabecalho", "outros")
                
                if cabecalho not in result:
                    result[cabecalho] = []
                
                result[cabecalho].append({
                    "id": flag_id,
                    "texto": flag_info.get("texto", "")
                })
        
        log_action('flags_grouped', {'count': sum(len(flags) for flags in result.values())})
        
        return result
