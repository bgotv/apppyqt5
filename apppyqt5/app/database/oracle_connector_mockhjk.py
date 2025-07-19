"""
Módulo de banco de dados para simulação de conexão com Oracle.
Esta versão simulada não requer acesso real ao banco de dados.
"""
import pandas as pd
import datetime
import random
from app.utils.logger import log_database_operation
from app.utils.performance import measure_performance

@measure_performance
@log_database_operation
def consulta_notas_oracle(oracle_user=None, oracle_password=None, oracle_dsn=None):
    """
    Simula consulta de notas técnicas no banco Oracle.
    
    Args:
        oracle_user (str, optional): Usuário do Oracle (não utilizado na simulação).
        oracle_password (str, optional): Senha do Oracle (não utilizado na simulação).
        oracle_dsn (str, optional): DSN do Oracle (não utilizado na simulação).
        
    Returns:
        list: Lista de dicionários com as notas técnicas simuladas.
    """
    # Simula um pequeno atraso para parecer uma consulta real
    import time
    time.sleep(0.5)
    
    # Gera dados simulados
    notas = []
    
    # Cria 10 notas simuladas
    for i in range(1, 11):
        # Data de cadastro aleatória nos últimos 30 dias
        data_cadastro = datetime.datetime.now() - datetime.timedelta(days=random.randint(1, 30))
        
        # Cria uma nota simulada
        nota = {
            'CD_PROJETO': f'PROJ{100000+i}',
            'CD_UC': f'{1000000+i*10}',
            'NR_ATIVIDADE': f'AT{200000+i}',
            'DT_CADASTRO': data_cadastro.strftime("%d-%m-%y"),
            'mod_pp': random.choice(['Autoconsumo Local', 'Autoconsumo Remoto']),
            'ccsp_fonteger': random.choice(['Energia Solar', 'Energia Eólica', 'Energia Hidráulica']),
            'vl_potencia_gerador': random.uniform(3.0, 15.0),
            'Aguarda_Analise_Tecnica': 'Sim',
            'Aguarda_Analise_Comercial': random.choice(['Sim', 'Não']),
            'BOX_PROJETO': f'BOX{i}',
            'ds_subgrupo': f'Subgrupo {i} - BOX{i}',
            'RUA_CCS': f'Rua Exemplo {i}',
            'NUM_RUA_CCS': f'{i*100}',
            'tipo': 'GD'
        }
        
        notas.append(nota)
    
    return notas
