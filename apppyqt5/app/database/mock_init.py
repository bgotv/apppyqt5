"""
Módulo de inicialização para conexões simuladas com bancos de dados.
Fornece funções para verificar disponibilidade de conexões reais e alternar para modo simulado.
"""
import os
import time
import random
from app.utils.logger import log_database_operation, log_action

# Variável global para controlar o modo de simulação
_SIMULATION_MODE = {
    'oracle': False,
    'hana': False,
    'forced': False  # Se True, força o uso de simulação mesmo se conexão real estiver disponível
}

def set_simulation_mode(oracle=None, hana=None, forced=None):
    """
    Define o modo de simulação para os bancos de dados.
    
    Args:
        oracle (bool, optional): Se True, força simulação para Oracle.
        hana (bool, optional): Se True, força simulação para HANA.
        forced (bool, optional): Se True, força o uso de simulação para ambos.
    """
    global _SIMULATION_MODE
    
    if oracle is not None:
        _SIMULATION_MODE['oracle'] = oracle
    
    if hana is not None:
        _SIMULATION_MODE['hana'] = hana
    
    if forced is not None:
        _SIMULATION_MODE['forced'] = forced
        if forced:
            _SIMULATION_MODE['oracle'] = True
            _SIMULATION_MODE['hana'] = True
    
    log_action('simulation_mode_changed', {
        'oracle': _SIMULATION_MODE['oracle'],
        'hana': _SIMULATION_MODE['hana'],
        'forced': _SIMULATION_MODE['forced']
    })

def get_simulation_status():
    """
    Retorna o status atual do modo de simulação.
    
    Returns:
        dict: Dicionário com o status de simulação para cada banco.
    """
    return {
        'oracle': _SIMULATION_MODE['oracle'],
        'hana': _SIMULATION_MODE['hana'],
        'forced': _SIMULATION_MODE['forced'],
        'any_simulated': _SIMULATION_MODE['oracle'] or _SIMULATION_MODE['hana']
    }

@log_database_operation
def check_oracle_connection(user, password, dsn):
    """
    Verifica se a conexão com o Oracle está disponível.
    
    Args:
        user (str): Usuário do Oracle.
        password (str): Senha do Oracle.
        dsn (str): DSN do Oracle.
        
    Returns:
        bool: True se a conexão estiver disponível, False caso contrário.
    """
    if _SIMULATION_MODE['forced']:
        return False
    
    try:
        import oracledb
        connection = oracledb.connect(user=user, password=password, dsn=dsn)
        connection.close()
        return True
    except Exception as e:
        log_action('oracle_connection_failed', {'error': str(e)})
        return False

@log_database_operation
def check_hana_connection(user, password, address, port):
    """
    Verifica se a conexão com o SAP HANA está disponível.
    
    Args:
        user (str): Usuário do SAP HANA.
        password (str): Senha do SAP HANA.
        address (str): Endereço do servidor SAP HANA.
        port (str): Porta do servidor SAP HANA.
        
    Returns:
        bool: True se a conexão estiver disponível, False caso contrário.
    """
    if _SIMULATION_MODE['forced']:
        return False
    
    try:
        from hdbcli import dbapi
        conn = dbapi.connect(address=address, port=port, user=user, password=password)
        conn.close()
        return True
    except Exception as e:
        log_action('hana_connection_failed', {'error': str(e)})
        return False

def initialize_database_connections(oracle_config, hana_config):
    """
    Inicializa as conexões com os bancos de dados, verificando disponibilidade
    e alternando para modo simulado quando necessário.
    
    Args:
        oracle_config (dict): Configurações de conexão com Oracle.
        hana_config (dict): Configurações de conexão com SAP HANA.
        
    Returns:
        dict: Status das conexões.
    """
    global _SIMULATION_MODE
    
    # Verifica conexão com Oracle
    oracle_ok = check_oracle_connection(
        oracle_config['user'],
        oracle_config['password'],
        oracle_config['dsn']
    )
    
    # Verifica conexão com HANA
    hana_ok = check_hana_connection(
        hana_config['user'],
        hana_config['password'],
        hana_config['address'],
        hana_config['port']
    )
    
    # Define modo de simulação com base na disponibilidade
    if not oracle_ok:
        _SIMULATION_MODE['oracle'] = True
    
    if not hana_ok:
        _SIMULATION_MODE['hana'] = True
    
    # Registra o status das conexões
    status = {
        'oracle_available': oracle_ok,
        'hana_available': hana_ok,
        'oracle_simulated': _SIMULATION_MODE['oracle'],
        'hana_simulated': _SIMULATION_MODE['hana']
    }
    
    log_action('database_connections_initialized', status)
    
    return status
