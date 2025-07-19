"""
Módulo de banco de dados para conexão com SAP HANA.
"""
from hdbcli import dbapi
import pandas as pd
from app.config.constants import ID_RESUMO_DICT
from app.utils.logger import log_database_operation
from app.utils.performance import measure_performance

@measure_performance
@log_database_operation
def consultar_uc_hana(cod_uc, user="user", password="senha", address='cpspddhdb01', port='31015'):
    """
    Consulta informações de uma unidade consumidora no SAP HANA.
    
    Args:
        cod_uc (str): Código da unidade consumidora.
        user (str, optional): Usuário do SAP HANA.
        password (str, optional): Senha do SAP HANA.
        address (str, optional): Endereço do servidor SAP HANA.
        port (str, optional): Porta do servidor SAP HANA.
        
    Returns:
        dict: Dicionário com as informações da unidade consumidora.
    """
    # Remove zeros à esquerda do código da UC
    cod_uc_limpo = str(cod_uc).lstrip("0")

    try:
        # Estabelece conexão com o banco
        conn = dbapi.connect(address=address, port=port, user=user, password=password)
        cursor = conn.cursor()
        
        # Consulta SQL
        sql = """
        SELECT
            INSTATUS.ANLAGE COD_INSTALACAO,
            MAX(INSTATUS.ANLAGE_STATUS_TEXT) STATUS_INSTALACAO,
            MAX(EVBS.ZZCATAKIT) CATEGORIA_INST,
            MAX(EVER.VERTRAG) NUM_CONTRATO,
            MAX(EVER.ZNOME_RAZAO) NOME_RAZAO,
            MAX(EANL.ANLART) COD_TIPO_INSTALACAO,
            MAX(DOC.TAXTYPE) TIPO_DOCUMENTO,
            MAX(DOC.TAXNUM) NUMERO_DOC
        FROM "_SYS_BIC"."accs.views.analytics.dimensions/CA_DIM_INSTALLATION_STATUS" INSTATUS
        LEFT JOIN "SAP_CCS"."EANL" EANL ON INSTATUS.ANLAGE = EANL.ANLAGE
        LEFT JOIN "SAP_CCS"."EVBS" EVBS ON EANL.VSTELLE = EVBS.VSTELLE
        LEFT JOIN "SAP_CCS"."EVER" EVER ON INSTATUS.ANLAGE = EVER.ANLAGE
        LEFT JOIN "SAP_CCS"."DFKKBPTAXNUM" DOC ON EVER.ZPARTNER = DOC.PARTNER
        WHERE LTRIM(INSTATUS.ANLAGE, '0') = ?
          AND EVER.AUSZDAT = '99991231'
          AND DOC.TAXTYPE IN ('BR1','BR2')
        GROUP BY INSTATUS.ANLAGE
        """
        
        # Executa a consulta
        cursor.execute(sql, (cod_uc_limpo,))
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        conn.close()
    except Exception as e:
        print(f"Erro consultando HANA para UC {cod_uc}: {e}")
        return {'SAP_HANA_OK': False}

    # Processa os resultados
    if rows:
        df = pd.DataFrame(rows, columns=columns)
        # Substitui os valores BR1/BR2 por PF/PJ
        df['TIPO_DOCUMENTO'] = df['TIPO_DOCUMENTO'].replace({"BR2": "PF", "BR1": "PJ"})
        # Mapeia o COD_TIPO_INSTALACAO de acordo com o id_resumo_dict
        df['COD_TIPO_INSTALACAO'] = df['COD_TIPO_INSTALACAO'].map(ID_RESUMO_DICT)
        row_dict = df.to_dict(orient='records')[0]
        row_dict['SAP_HANA_OK'] = True
        return row_dict
    else:
        return {'SAP_HANA_OK': False}
