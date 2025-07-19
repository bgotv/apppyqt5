"""
Módulo de inicialização para o pacote de banco de dados.
Configura as conexões e inicializa o modo de simulação quando necessário.
"""
from app.config import settings
from app.utils.logger import log_action
from app.database.mock_init import initialize_database_connections, get_simulation_status

# Importa os conectores
from app.database.oracle_connector import consulta_notas_oracle
from app.database.hana_connector import consultar_uc_hana

def init_database():
    """
    Inicializa as conexões com os bancos de dados.
    Verifica a disponibilidade e configura o modo de simulação quando necessário.
    
    Returns:
        dict: Status das conexões.
    """
    # Configurações de conexão
    oracle_config = {
        'user': settings.ORACLE_USER,
        'password': settings.ORACLE_PASSWORD,
        'dsn': settings.ORACLE_DSN
    }
    
    hana_config = {
        'user': settings.HANA_USER,
        'password': settings.HANA_PASSWORD,
        'address': settings.HANA_ADDRESS,
        'port': settings.HANA_PORT
    }
    
    # Inicializa as conexões
    status = initialize_database_connections(oracle_config, hana_config)
    
    # Registra o status
    log_action('database_initialized', {
        'oracle_simulated': status['oracle_simulated'],
        'hana_simulated': status['hana_simulated']
    })
    
    return status

def get_connection_status():
    """
    Retorna o status atual das conexões com os bancos de dados.
    
    Returns:
        dict: Status das conexões.
    """
    sim_status = get_simulation_status()
    
    return {
        'oracle_simulated': sim_status['oracle'],
        'hana_simulated': sim_status['hana'],
        'any_simulated': sim_status['any_simulated'],
        'forced_simulation': sim_status['forced']
    }
