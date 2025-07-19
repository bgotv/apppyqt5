"""
Arquivo de inicialização para usar os conectores simulados.
Substitua o arquivo __init__.py original por este para usar as versões simuladas.
"""
from app.database.oracle_connector_mock import consulta_notas_oracle
from app.database.hana_connector_mock import consultar_uc_hana

__all__ = ['consulta_notas_oracle', 'consultar_uc_hana']
