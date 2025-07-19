"""
Módulo de banco de dados para simulação de conexão com SAP HANA.
Esta versão simulada não requer acesso real ao banco de dados.
"""
import pandas as pd
import random
from app.utils.logger import log_database_operation
from app.utils.performance import measure_performance

@measure_performance
@log_database_operation
def consultar_uc_hana(cod_uc, user="user", password="senha", address='cpspddhdb01', port='31015'):
    """
    Simula consulta de informações de uma unidade consumidora no SAP HANA.
    
    Args:
        cod_uc (str): Código da unidade consumidora.
        user (str, optional): Usuário do SAP HANA (não utilizado na simulação).
        password (str, optional): Senha do SAP HANA (não utilizado na simulação).
        address (str, optional): Endereço do servidor SAP HANA (não utilizado na simulação).
        port (str, optional): Porta do servidor SAP HANA (não utilizado na simulação).
        
    Returns:
        dict: Dicionário com as informações simuladas da unidade consumidora.
    """
    # Simula um pequeno atraso para parecer uma consulta real
    import time
    time.sleep(0.3)
    
    # Remove zeros à esquerda do código da UC
    cod_uc_limpo = str(cod_uc).lstrip("0")
    
    # Gera dados simulados com base no código da UC
    # Isso garante que a mesma UC sempre retorne os mesmos dados
    seed = sum(ord(c) for c in cod_uc_limpo)
    random.seed(seed)
    
    # Lista de possíveis status de instalação
    status_options = ['ATIVO', 'SUSPENSO', 'CORTADO', 'DESLIGADO A PEDIDO']
    status_weights = [0.8, 0.1, 0.05, 0.05]  # 80% de chance de estar ativo
    
    # Lista de possíveis categorias de instalação
    categoria_options = ['RESIDENCIAL', 'COMERCIAL', 'INDUSTRIAL', 'RURAL']
    
    # Lista de possíveis tipos de instalação
    tipo_options = ['Grupo B', 'Grupo A', 'B Optante', 'Cliente Livre']
    tipo_weights = [0.7, 0.2, 0.05, 0.05]  # 70% de chance de ser Grupo B
    
    # Gera dados aleatórios mas consistentes para a mesma UC
    uc_data = {
        'COD_INSTALACAO': cod_uc,
        'STATUS_INSTALACAO': random.choices(status_options, weights=status_weights)[0],
        'CATEGORIA_INST': random.choice(categoria_options),
        'NUM_CONTRATO': f'CONT{int(cod_uc_limpo) % 1000000:06d}',
        'NOME_RAZAO': f'Cliente Teste {cod_uc_limpo[-4:]}',
        'COD_TIPO_INSTALACAO': random.choices(tipo_options, weights=tipo_weights)[0],
        'TIPO_DOCUMENTO': random.choice(['PF', 'PJ']),
        'NUMERO_DOC': f'{"".join([str(random.randint(0, 9)) for _ in range(11)])}',
        'SAP_HANA_OK': True
    }
    
    return uc_data
